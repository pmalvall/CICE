"""Unit tests for Regulatory Disclosure Generation Tools."""

import json
import pytest


COMMON_PARAMS = {
    "company_id": "TEST-CO",
    "reporting_period_start": "2024-01-01",
    "reporting_period_end": "2024-12-31",
    "scope1_tco2e": 1500.0,
    "scope2_tco2e": 120.0,
    "scope3_tco2e": 8500.0,
    "carbon_intensity_tco2e_per_boe": 0.042,
    "total_production_boe": 38000.0,
}


def test_prepare_csrd_disclosure_esrs_e1_data_points():
    from tools.disclosure_tools import prepare_csrd_disclosure
    result = json.loads(prepare_csrd_disclosure.invoke(COMMON_PARAMS))
    assert result["status"] == "success"
    disc = result["disclosure"]
    assert disc["framework"] == "CSRD"
    assert disc["standard"] == "ESRS E1 — Climate Change"

    # Required ESRS E1 data points
    assert "ESRS_E1_6_GHG_Emissions" in disc
    assert "ESRS_E1_4_Carbon_Intensity" in disc
    ghg = disc["ESRS_E1_6_GHG_Emissions"]
    assert ghg["scope1_tco2e"] == 1500.0
    assert ghg["scope2_location_based_tco2e"] == 120.0
    assert ghg["scope3_tco2e"] == 8500.0
    assert ghg["total_ghg_tco2e"] == 10120.0

    assert disc["disclosure_status"].startswith("DRAFT")
    assert disc["auditable"] is True


def test_prepare_ifrs_s2_disclosure_required_fields():
    from tools.disclosure_tools import prepare_ifrs_s2_disclosure
    result = json.loads(prepare_ifrs_s2_disclosure.invoke({
        "company_id": "TEST-CO",
        "reporting_period_start": "2024-01-01",
        "reporting_period_end": "2024-12-31",
        "scope1_tco2e": 1500.0,
        "scope2_tco2e": 120.0,
        "scope3_tco2e": 8500.0,
        "carbon_intensity_tco2e_per_boe": 0.042,
    }))
    assert result["status"] == "success"
    disc = result["disclosure"]
    assert disc["framework"] == "IFRS S2"
    assert "IFRS_S2_29_Metrics" in disc
    assert "IFRS_S2_9_21_Risks_Opportunities" in disc
    metrics = disc["IFRS_S2_29_Metrics"]
    assert metrics["total_ghg_tco2e"] == 10120.0
    assert disc["disclosure_status"].startswith("DRAFT")


def test_prepare_sb253_disclosure_revenue_threshold():
    from tools.disclosure_tools import prepare_sb253_disclosure
    result = json.loads(prepare_sb253_disclosure.invoke({
        "company_id": "TEST-CO",
        "reporting_period_start": "2024-01-01",
        "reporting_period_end": "2024-12-31",
        "scope1_tco2e": 1500.0,
        "scope2_tco2e": 120.0,
        "scope3_tco2e": 8500.0,
        "annual_revenue_usd": 2_000_000_000.0,  # $2B
    }))
    assert result["status"] == "success"
    disc = result["disclosure"]
    assert disc["sb253_reporting_required"] is True
    assert disc["SB253_Scope1_Scope2"]["scope1_tco2e"] == 1500.0
    assert disc["attestation"]["penalty_exposure_usd_per_year"] == 500_000


def test_render_regulatory_report_json_format():
    from tools.disclosure_tools import render_regulatory_report, prepare_csrd_disclosure
    # Prepare disclosure data first
    csrd_result = prepare_csrd_disclosure.invoke(COMMON_PARAMS)
    disc_data = json.loads(csrd_result)["disclosure"]

    result = json.loads(render_regulatory_report.invoke({
        "disclosure_data": json.dumps({"disclosure": disc_data}),
        "format": "JSON",
        "jurisdiction": "CSRD",
        "reporting_period": "2024",
    }))
    assert result["status"] == "success"
    assert result["report_status"] == "DRAFT"
    assert result["human_approval_required"] is True
    assert result["file_name"].endswith(".json")
    assert result["jurisdiction"] == "CSRD"
    assert result["lineage_record_count"] > 0
    assert "warning" in result and len(result["warning"]) > 0


def test_render_regulatory_report_invalid_format():
    from tools.disclosure_tools import render_regulatory_report
    result = json.loads(render_regulatory_report.invoke({
        "disclosure_data": "{}",
        "format": "EXCEL",
        "jurisdiction": "CSRD",
        "reporting_period": "2024",
    }))
    assert result["status"] == "error"
    assert "EXCEL" in result["message"]


def test_render_regulatory_report_xbrl_format():
    from tools.disclosure_tools import render_regulatory_report
    result = json.loads(render_regulatory_report.invoke({
        "disclosure_data": json.dumps({"disclosure": {"ESRS_E1_6": {}}}),
        "format": "XBRL",
        "jurisdiction": "CSRD",
        "reporting_period": "2024",
    }))
    assert result["status"] == "success"
    assert result["file_name"].endswith(".xbrl")
