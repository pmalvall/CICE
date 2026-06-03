"""SAP PRA Data Ingestion Tools.

These tools consume SAP Production and Revenue Accounting (PRA) OData APIs
via MCP server tools. In production, the actual OData calls are routed through
the MCP server layer (mcp_tools.py). These are standalone tool implementations
that can be called directly by the agent or wrapped as MCP-backed tools.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_pra_field_data(field_id: Optional[str] = None, top: int = 100) -> str:
    """Fetch field-level metadata from SAP PRA.

    Returns field ID, name, region, operator, and active status.
    Use field_id to retrieve a specific field, or omit to retrieve all fields (up to top limit).

    Args:
        field_id: Optional PRA field identifier to retrieve a specific field
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info("get_pra_field_data called: field_id=%s, top=%d", field_id, top)

    # In production, this routes through the MCP server for OP_PRAFIELD_0001
    # Mock response structure matching PRA Field OData schema
    mock_fields = [
        {
            "FieldId": "FIELD-001",
            "FieldName": "North Sea Alpha",
            "Region": "EU-NORTH",
            "Operator": "SAP_PRA_DEMO",
            "IsActive": True,
            "ProductionStartDate": "2010-01-01",
            "Latitude": 58.5,
            "Longitude": 2.3,
        },
        {
            "FieldId": "FIELD-002",
            "FieldName": "Gulf Coast Beta",
            "Region": "US-GULF",
            "Operator": "SAP_PRA_DEMO",
            "IsActive": True,
            "ProductionStartDate": "2015-06-01",
            "Latitude": 28.9,
            "Longitude": -90.1,
        },
    ]

    if field_id:
        result = [f for f in mock_fields if f["FieldId"] == field_id]
    else:
        result = mock_fields[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_PRAFIELD_0001",
        "record_count": len(result),
        "fields": result,
    })


@tool
def get_pra_plant_volumes(
    field_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    top: int = 100,
) -> str:
    """Fetch plant-level production volumes from SAP PRA per measurement period.

    Returns volumes by hydrocarbon type (oil, gas, condensate, water) per plant and period.

    Args:
        field_id: Optional field identifier to filter volumes by field
        period_start: Start date in YYYY-MM-DD format (e.g. 2024-01-01)
        period_end: End date in YYYY-MM-DD format (e.g. 2024-03-31)
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info(
        "get_pra_plant_volumes called: field_id=%s, period=%s to %s, top=%d",
        field_id, period_start, period_end, top,
    )

    # Mock response matching PRA Simple Plant Volume OData schema (OP_SIMPLEPLANTVOLUME_0001)
    mock_volumes = [
        {
            "PlantId": "PLANT-001",
            "FieldId": "FIELD-001",
            "MeasurementPeriod": period_start or "2024-01-01",
            "OilVolume_bbl": 125000.0,
            "GasVolume_mcf": 890000.0,
            "CondensateVolume_bbl": 8500.0,
            "WaterVolume_bbl": 45000.0,
            "FlareVolume_mcf": 4200.0,
            "VentVolume_mcf": 850.0,
            "Unit": "BOE",
        },
        {
            "PlantId": "PLANT-002",
            "FieldId": "FIELD-002",
            "MeasurementPeriod": period_start or "2024-01-01",
            "OilVolume_bbl": 98000.0,
            "GasVolume_mcf": 620000.0,
            "CondensateVolume_bbl": 5200.0,
            "WaterVolume_bbl": 38000.0,
            "FlareVolume_mcf": 8900.0,
            "VentVolume_mcf": 1200.0,
            "Unit": "BOE",
        },
    ]

    if field_id:
        result = [v for v in mock_volumes if v["FieldId"] == field_id]
    else:
        result = mock_volumes[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_SIMPLEPLANTVOLUME_0001",
        "record_count": len(result),
        "period_start": period_start,
        "period_end": period_end,
        "volumes": result,
    })


@tool
def get_pra_revenue_document(
    document_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    top: int = 100,
) -> str:
    """Read PRA Revenue Accounting Documents for financial reconciliation.

    Returns document header, transaction amounts, and volume references.

    Args:
        document_id: Optional specific revenue accounting document ID
        period_start: Start date in YYYY-MM-DD format
        period_end: End date in YYYY-MM-DD format
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info(
        "get_pra_revenue_document called: doc_id=%s, period=%s to %s",
        document_id, period_start, period_end,
    )

    # Mock response matching OP_PRAREVENUEACCTDOCUMENT_0001 schema
    mock_docs = [
        {
            "DocumentId": "REV-2024-001",
            "PlantId": "PLANT-001",
            "PostingDate": period_start or "2024-01-31",
            "DocumentType": "OIL_REVENUE",
            "GrossRevenue_USD": 9875000.0,
            "NetRevenue_USD": 9125000.0,
            "VolumeReference_bbl": 125000.0,
            "PricePerUnit_USD": 79.0,
            "Currency": "USD",
        },
        {
            "DocumentId": "REV-2024-002",
            "PlantId": "PLANT-002",
            "PostingDate": period_start or "2024-01-31",
            "DocumentType": "GAS_REVENUE",
            "GrossRevenue_USD": 2480000.0,
            "NetRevenue_USD": 2356000.0,
            "VolumeReference_mcf": 620000.0,
            "PricePerUnit_USD": 4.0,
            "Currency": "USD",
        },
    ]

    if document_id:
        result = [d for d in mock_docs if d["DocumentId"] == document_id]
    else:
        result = mock_docs[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_PRAREVENUEACCTDOCUMENT_0001",
        "record_count": len(result),
        "documents": result,
    })


@tool
def get_pra_well_data(
    well_id: Optional[str] = None,
    field_id: Optional[str] = None,
    top: int = 100,
) -> str:
    """Fetch well and well-completion master data from SAP PRA.

    Returns well ID, name, completion type, production status, field assignment, and coordinates.

    Args:
        well_id: Optional specific well identifier
        field_id: Optional field identifier to filter wells by field
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info("get_pra_well_data called: well_id=%s, field_id=%s, top=%d", well_id, field_id, top)

    mock_wells = [
        {
            "WellId": "WELL-001",
            "WellName": "Alpha-1",
            "FieldId": "FIELD-001",
            "CompletionType": "VERTICAL",
            "ProductionStatus": "ACTIVE",
            "Latitude": 58.51,
            "Longitude": 2.31,
            "SpudDate": "2011-03-15",
            "FirstProductionDate": "2011-09-01",
        },
        {
            "WellId": "WELL-002",
            "WellName": "Alpha-2",
            "FieldId": "FIELD-001",
            "CompletionType": "HORIZONTAL",
            "ProductionStatus": "ACTIVE",
            "Latitude": 58.52,
            "Longitude": 2.32,
            "SpudDate": "2013-07-20",
            "FirstProductionDate": "2014-02-01",
        },
        {
            "WellId": "WELL-003",
            "WellName": "Beta-1",
            "FieldId": "FIELD-002",
            "CompletionType": "HORIZONTAL",
            "ProductionStatus": "ACTIVE",
            "Latitude": 28.91,
            "Longitude": -90.11,
            "SpudDate": "2016-01-10",
            "FirstProductionDate": "2016-06-15",
        },
    ]

    if well_id:
        result = [w for w in mock_wells if w["WellId"] == well_id]
    elif field_id:
        result = [w for w in mock_wells if w["FieldId"] == field_id]
    else:
        result = mock_wells[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_PRAWELL_0001",
        "record_count": len(result),
        "wells": result,
    })


@tool
def get_pra_well_completion_variable_data(
    well_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    top: int = 100,
) -> str:
    """Fetch time-series well completion variable data from SAP PRA.

    Returns operational parameters such as flow rates, pressures, GOR, and flare volumes per well completion per day.

    Args:
        well_id: Optional specific well identifier to filter data
        period_start: Start date in YYYY-MM-DD format
        period_end: End date in YYYY-MM-DD format
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info(
        "get_pra_well_completion_variable_data called: well_id=%s, period=%s to %s",
        well_id, period_start, period_end,
    )

    mock_variable_data = [
        {
            "WellId": "WELL-001",
            "Date": period_start or "2024-01-15",
            "OilFlowRate_bbl_per_day": 4200.0,
            "GasFlowRate_mcf_per_day": 29500.0,
            "WaterFlowRate_bbl_per_day": 1500.0,
            "FlarVolume_mcf_per_day": 145.0,
            "VentVolume_mcf_per_day": 28.0,
            "TubingPressure_psi": 1850.0,
            "GOR_scf_per_bbl": 7024.0,
        },
        {
            "WellId": "WELL-002",
            "Date": period_start or "2024-01-15",
            "OilFlowRate_bbl_per_day": 3800.0,
            "GasFlowRate_mcf_per_day": 25000.0,
            "WaterFlowRate_bbl_per_day": 1200.0,
            "FlarVolume_mcf_per_day": 320.0,  # elevated — anomaly
            "VentVolume_mcf_per_day": 85.0,   # elevated — methane concern
            "TubingPressure_psi": 1650.0,
            "GOR_scf_per_bbl": 6579.0,
        },
        {
            "WellId": "WELL-003",
            "Date": period_start or "2024-01-15",
            "OilFlowRate_bbl_per_day": 2900.0,
            "GasFlowRate_mcf_per_day": 18000.0,
            "WaterFlowRate_bbl_per_day": 2800.0,
            "FlarVolume_mcf_per_day": 210.0,
            "VentVolume_mcf_per_day": 42.0,
            "TubingPressure_psi": 2100.0,
            "GOR_scf_per_bbl": 6207.0,
        },
    ]

    if well_id:
        result = [d for d in mock_variable_data if d["WellId"] == well_id]
    else:
        result = mock_variable_data[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_PRAWELLCOMPLETIONDATED_0001",
        "record_count": len(result),
        "period_start": period_start,
        "period_end": period_end,
        "variable_data": result,
    })


@tool
def get_pra_reservoir_data(
    reservoir_id: Optional[str] = None,
    field_id: Optional[str] = None,
    top: int = 100,
) -> str:
    """Fetch reservoir master data from SAP PRA.

    Returns reservoir ID, name, type, depth, and field association.

    Args:
        reservoir_id: Optional specific reservoir identifier
        field_id: Optional field identifier to filter reservoirs by field
        top: Maximum number of records to return (default 100, max 100)
    """
    top = min(top, 100)
    logger.info("get_pra_reservoir_data called: reservoir_id=%s, field_id=%s", reservoir_id, field_id)

    mock_reservoirs = [
        {
            "ReservoirId": "RES-001",
            "ReservoirName": "Alpha Sandstone A",
            "FieldId": "FIELD-001",
            "ReservoirType": "SANDSTONE",
            "DepthTVD_ft": 8500.0,
            "PorePressure_psi": 4250.0,
            "InitialOilInPlace_MMBO": 285.0,
            "RecoveryFactor": 0.42,
        },
        {
            "ReservoirId": "RES-002",
            "ReservoirName": "Beta Carbonate B",
            "FieldId": "FIELD-002",
            "ReservoirType": "CARBONATE",
            "DepthTVD_ft": 11200.0,
            "PorePressure_psi": 5600.0,
            "InitialOilInPlace_MMBO": 195.0,
            "RecoveryFactor": 0.38,
        },
    ]

    if reservoir_id:
        result = [r for r in mock_reservoirs if r["ReservoirId"] == reservoir_id]
    elif field_id:
        result = [r for r in mock_reservoirs if r["FieldId"] == field_id]
    else:
        result = mock_reservoirs[:top]

    return json.dumps({
        "status": "success",
        "api": "OP_PRARESERVOIR_0001",
        "record_count": len(result),
        "reservoirs": result,
    })
