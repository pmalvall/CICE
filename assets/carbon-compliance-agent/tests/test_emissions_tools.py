"""Unit tests for Scope 1/2/3 Emissions Calculation Tools."""

import json
import pytest


def test_get_emission_factors_combustion():
    from tools.emissions_tools import get_emission_factors
    result = json.loads(get_emission_factors.invoke({
        "region": "EU-NORTH",
        "gas_type": "CO2",
        "activity_type": "combustion",
    }))
    assert result["status"] == "success"
    assert result["factor_value"] > 0
    assert "GHG Protocol" in result["methodology"]
    assert result["region"] == "EU-NORTH"


def test_get_emission_factors_unknown_region_defaults():
    from tools.emissions_tools import get_emission_factors
    result = json.loads(get_emission_factors.invoke({
        "region": "UNKNOWN-REGION",
        "activity_type": "flaring",
    }))
    # Should fall back to default region rather than failing
    assert result["status"] == "success"
    assert result["factor_value"] > 0


def test_calculate_scope1_combustion_flaring_venting():
    from tools.emissions_tools import calculate_scope1_emissions
    result = json.loads(calculate_scope1_emissions.invoke({
        "asset_id": "PLANT-001",
        "region": "EU-NORTH",
        "flare_volume_mcf": 4200.0,
        "vent_volume_mcf": 850.0,
        "fuel_gas_consumed_mcf": 500.0,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
    }))
    assert result["status"] == "success"
    assert result["scope1_total_tco2e"] > 0

    # Verify breakdown sums match total
    bd = result["breakdown"]
    total = sum(bd[k] for k in ["combustion_tco2e", "flaring_tco2e", "venting_tco2e", "fugitive_tco2e"])
    assert abs(total - result["scope1_total_tco2e"]) < 0.01  # floating point tolerance

    assert result["calculation_traceable"] is True


def test_calculate_scope1_zero_flare():
    from tools.emissions_tools import calculate_scope1_emissions
    result = json.loads(calculate_scope1_emissions.invoke({
        "asset_id": "PLANT-ZERO",
        "region": "US-GULF",
        "flare_volume_mcf": 0.0,
        "vent_volume_mcf": 0.0,
    }))
    assert result["status"] == "success"
    assert result["scope1_total_tco2e"] == 0.0


def test_calculate_scope2_grid_factor_multiplication():
    from tools.emissions_tools import calculate_scope2_emissions
    result = json.loads(calculate_scope2_emissions.invoke({
        "asset_id": "PLANT-001",
        "region": "EU-NORTH",
        "energy_consumed_kwh": 1_000_000.0,
    }))
    assert result["status"] == "success"
    # EU-NORTH grid factor = 0.233 kg CO2e/kWh → 1M kWh = 233 tCO2e
    assert abs(result["scope2_total_tco2e"] - 233.0) < 1.0
    assert result["method"] == "Location-based"


def test_calculate_scope3_oil_and_gas():
    from tools.emissions_tools import calculate_scope3_emissions
    result = json.loads(calculate_scope3_emissions.invoke({
        "asset_id": "FIELD-001",
        "oil_sold_bbl": 100_000.0,
        "gas_sold_mmbtu": 500_000.0,
    }))
    assert result["status"] == "success"
    assert result["scope3_total_tco2e"] > 0
    assert result["scope3_category"] == "Category 11 — Use of Sold Products"
    assert result["carbon_intensity_tco2e_per_boe"] > 0


def test_validate_emissions_validated_status():
    from tools.emissions_tools import validate_emissions_results
    result = json.loads(validate_emissions_results.invoke({
        "asset_id": "FIELD-001",
        "period": "2024-01",
        "scope1_tco2e": 500.0,
        "scope2_tco2e": 50.0,
        "scope3_tco2e": 1200.0,
    }))
    assert result["status"] == "success"
    assert result["validation_status"] == "VALIDATED"
    assert result["total_tco2e"] == 1750.0


def test_validate_emissions_negative_flagged():
    from tools.emissions_tools import validate_emissions_results
    result = json.loads(validate_emissions_results.invoke({
        "asset_id": "FIELD-ERR",
        "period": "2024-01",
        "scope1_tco2e": -100.0,
        "scope2_tco2e": 50.0,
        "scope3_tco2e": 200.0,
    }))
    assert result["validation_status"] == "FLAGGED"
    assert any(f["severity"] == "ERROR" for f in result["flags"])
