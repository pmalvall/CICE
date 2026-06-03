"""Unit tests for SAP PRA Data Ingestion Tools."""

import json
import pytest


def test_get_pra_field_data_all():
    from tools.pra_tools import get_pra_field_data
    result = json.loads(get_pra_field_data.invoke({"top": 100}))
    assert result["status"] == "success"
    assert result["record_count"] > 0
    assert "fields" in result
    assert all("FieldId" in f for f in result["fields"])


def test_get_pra_field_data_specific_field():
    from tools.pra_tools import get_pra_field_data
    result = json.loads(get_pra_field_data.invoke({"field_id": "FIELD-001"}))
    assert result["status"] == "success"
    assert result["record_count"] == 1
    assert result["fields"][0]["FieldId"] == "FIELD-001"


def test_get_pra_field_data_missing_field():
    from tools.pra_tools import get_pra_field_data
    result = json.loads(get_pra_field_data.invoke({"field_id": "NONEXISTENT"}))
    assert result["status"] == "success"
    assert result["record_count"] == 0


def test_get_pra_plant_volumes_normalization():
    from tools.pra_tools import get_pra_plant_volumes
    result = json.loads(get_pra_plant_volumes.invoke({
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
    }))
    assert result["status"] == "success"
    assert result["record_count"] > 0
    vol = result["volumes"][0]
    assert "OilVolume_bbl" in vol
    assert "GasVolume_mcf" in vol
    assert "FlareVolume_mcf" in vol


def test_get_pra_plant_volumes_field_filter():
    from tools.pra_tools import get_pra_plant_volumes
    result = json.loads(get_pra_plant_volumes.invoke({"field_id": "FIELD-001"}))
    assert result["status"] == "success"
    assert all(v["FieldId"] == "FIELD-001" for v in result["volumes"])


def test_get_pra_revenue_document_fields():
    from tools.pra_tools import get_pra_revenue_document
    result = json.loads(get_pra_revenue_document.invoke({}))
    assert result["status"] == "success"
    doc = result["documents"][0]
    assert "DocumentId" in doc
    assert "GrossRevenue_USD" in doc
    assert "NetRevenue_USD" in doc


def test_get_pra_well_data_by_field():
    from tools.pra_tools import get_pra_well_data
    result = json.loads(get_pra_well_data.invoke({"field_id": "FIELD-001"}))
    assert result["status"] == "success"
    assert all(w["FieldId"] == "FIELD-001" for w in result["wells"])


def test_get_pra_well_completion_variable_data():
    from tools.pra_tools import get_pra_well_completion_variable_data
    result = json.loads(get_pra_well_completion_variable_data.invoke({"well_id": "WELL-001"}))
    assert result["status"] == "success"
    assert result["record_count"] > 0
    record = result["variable_data"][0]
    assert "FlarVolume_mcf_per_day" in record
    assert "VentVolume_mcf_per_day" in record


def test_get_pra_reservoir_data():
    from tools.pra_tools import get_pra_reservoir_data
    result = json.loads(get_pra_reservoir_data.invoke({"field_id": "FIELD-001"}))
    assert result["status"] == "success"
    assert all(r["FieldId"] == "FIELD-001" for r in result["reservoirs"])
