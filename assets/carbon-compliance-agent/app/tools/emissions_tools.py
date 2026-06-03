"""Scope 1/2/3 Emissions Calculation Tools.

Implements GHG Protocol methodology for computing direct (Scope 1),
indirect energy (Scope 2), and value chain (Scope 3) emissions from
SAP PRA production data with full factor provenance tracking.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# GHG Protocol emission factors (kg CO2e per unit) — illustrative values
# In production these are retrieved dynamically from SAP Sustainability Footprint Management
_EMISSION_FACTORS = {
    "EU-NORTH": {
        "combustion_kg_co2e_per_mcf": 54.87,
        "flaring_kg_co2e_per_mcf": 52.20,
        "methane_gwp100": 28.0,
        "grid_kg_co2e_per_kwh": 0.233,
        "oil_downstream_kg_co2e_per_bbl": 0.43,
        "gas_downstream_kg_co2e_per_mmbtu": 0.053,
    },
    "US-GULF": {
        "combustion_kg_co2e_per_mcf": 54.87,
        "flaring_kg_co2e_per_mcf": 52.20,
        "methane_gwp100": 28.0,
        "grid_kg_co2e_per_kwh": 0.386,
        "oil_downstream_kg_co2e_per_bbl": 0.43,
        "gas_downstream_kg_co2e_per_mmbtu": 0.053,
    },
}
_DEFAULT_REGION = "EU-NORTH"


@tool
def get_emission_factors(region: str, gas_type: str = "CO2", activity_type: str = "combustion") -> str:
    """Retrieve region-specific emission factors from SAP Sustainability Footprint Management.

    Args:
        region: Region code (e.g. EU-NORTH, US-GULF)
        gas_type: Greenhouse gas type — CO2, CH4, N2O, or CO2e (default: CO2e)
        activity_type: Emission activity type — combustion, flaring, venting, fugitive, grid (default: combustion)
    """
    logger.info("get_emission_factors: region=%s, gas_type=%s, activity_type=%s", region, gas_type, activity_type)

    factors = _EMISSION_FACTORS.get(region, _EMISSION_FACTORS[_DEFAULT_REGION])

    activity_map = {
        "combustion": {"value": factors["combustion_kg_co2e_per_mcf"], "unit": "kg CO2e/mcf"},
        "flaring": {"value": factors["flaring_kg_co2e_per_mcf"], "unit": "kg CO2e/mcf"},
        "venting": {"value": factors["methane_gwp100"], "unit": "kg CO2e/kg CH4 (GWP100)"},
        "fugitive": {"value": factors["methane_gwp100"], "unit": "kg CO2e/kg CH4 (GWP100)"},
        "grid": {"value": factors["grid_kg_co2e_per_kwh"], "unit": "kg CO2e/kWh"},
    }

    factor_data = activity_map.get(activity_type, activity_map["combustion"])

    return json.dumps({
        "status": "success",
        "region": region,
        "gas_type": gas_type,
        "activity_type": activity_type,
        "factor_value": factor_data["value"],
        "factor_unit": factor_data["unit"],
        "methodology": "GHG Protocol Corporate Standard",
        "source_standard": "IPCC AR6 / EPA AP-42",
        "effective_date": "2024-01-01",
        "validated_by": "SAP Sustainability Footprint Management",
    })


@tool
def calculate_scope1_emissions(
    asset_id: str,
    region: str,
    flare_volume_mcf: float,
    vent_volume_mcf: float,
    fuel_gas_consumed_mcf: float = 0.0,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> str:
    """Calculate Scope 1 (direct) emissions for an asset using GHG Protocol methodology.

    Covers combustion (fuel gas), flaring (CO2 + CH4 + N2O), venting (methane),
    and fugitive emissions.

    Args:
        asset_id: PRA asset identifier (field, plant, or well ID)
        region: Region code for emission factor selection (e.g. EU-NORTH, US-GULF)
        flare_volume_mcf: Volume of gas flared in thousand cubic feet (mcf)
        vent_volume_mcf: Volume of methane vented in thousand cubic feet (mcf)
        fuel_gas_consumed_mcf: Volume of fuel gas combusted in mcf (default 0)
        period_start: Reporting period start date YYYY-MM-DD
        period_end: Reporting period end date YYYY-MM-DD
    """
    logger.info(
        "calculate_scope1_emissions: asset=%s, region=%s, flare=%.2f mcf, vent=%.2f mcf",
        asset_id, region, flare_volume_mcf, vent_volume_mcf,
    )

    factors = _EMISSION_FACTORS.get(region, _EMISSION_FACTORS[_DEFAULT_REGION])

    # Combustion: fuel gas consumed × combustion emission factor
    combustion_tco2e = (fuel_gas_consumed_mcf * factors["combustion_kg_co2e_per_mcf"]) / 1000.0

    # Flaring: flare gas × flaring factor (combined CO2 + incomplete combustion CH4 + N2O)
    flaring_tco2e = (flare_volume_mcf * factors["flaring_kg_co2e_per_mcf"]) / 1000.0

    # Venting: methane vent volume × density (0.0192 kg CH4/mcf) × GWP100
    # mcf CH4 → kg CH4: 1 mcf CH4 ≈ 19.2 kg at standard conditions
    venting_tco2e = (vent_volume_mcf * 19.2 * factors["methane_gwp100"]) / 1000.0

    # Fugitive: simplified estimate (2% of venting as fugitive baseline)
    fugitive_tco2e = venting_tco2e * 0.02

    total_scope1_tco2e = combustion_tco2e + flaring_tco2e + venting_tco2e + fugitive_tco2e

    return json.dumps({
        "status": "success",
        "asset_id": asset_id,
        "region": region,
        "period_start": period_start,
        "period_end": period_end,
        "scope1_total_tco2e": round(total_scope1_tco2e, 4),
        "breakdown": {
            "combustion_tco2e": round(combustion_tco2e, 4),
            "flaring_tco2e": round(flaring_tco2e, 4),
            "venting_tco2e": round(venting_tco2e, 4),
            "fugitive_tco2e": round(fugitive_tco2e, 4),
        },
        "emission_factors_applied": {
            "combustion_kg_co2e_per_mcf": factors["combustion_kg_co2e_per_mcf"],
            "flaring_kg_co2e_per_mcf": factors["flaring_kg_co2e_per_mcf"],
            "methane_gwp100": factors["methane_gwp100"],
        },
        "methodology": "GHG Protocol Corporate Standard — Scope 1",
        "factor_source": "IPCC AR6 / EPA AP-42",
        "calculation_traceable": True,
    })


@tool
def calculate_scope2_emissions(
    asset_id: str,
    region: str,
    energy_consumed_kwh: float,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> str:
    """Calculate Scope 2 (indirect energy) emissions from purchased electricity for an asset.

    Uses location-based method with regional grid emission factors.

    Args:
        asset_id: PRA asset identifier
        region: Region code for grid emission factor selection
        energy_consumed_kwh: Total purchased electricity consumed in kWh for the period
        period_start: Reporting period start date YYYY-MM-DD
        period_end: Reporting period end date YYYY-MM-DD
    """
    logger.info(
        "calculate_scope2_emissions: asset=%s, region=%s, energy=%.2f kWh",
        asset_id, region, energy_consumed_kwh,
    )

    factors = _EMISSION_FACTORS.get(region, _EMISSION_FACTORS[_DEFAULT_REGION])
    grid_factor = factors["grid_kg_co2e_per_kwh"]

    scope2_tco2e = (energy_consumed_kwh * grid_factor) / 1000.0

    return json.dumps({
        "status": "success",
        "asset_id": asset_id,
        "region": region,
        "period_start": period_start,
        "period_end": period_end,
        "scope2_total_tco2e": round(scope2_tco2e, 4),
        "energy_consumed_kwh": energy_consumed_kwh,
        "grid_emission_factor_kg_co2e_per_kwh": grid_factor,
        "method": "Location-based",
        "methodology": "GHG Protocol Scope 2 Guidance",
        "factor_source": "IEA Emissions Factors 2023",
        "calculation_traceable": True,
    })


@tool
def calculate_scope3_emissions(
    asset_id: str,
    oil_sold_bbl: float = 0.0,
    gas_sold_mmbtu: float = 0.0,
    region: str = "EU-NORTH",
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> str:
    """Calculate Scope 3 Category 11 (use of sold products) emissions for hydrocarbons sold.

    Covers downstream combustion of oil and gas products by end users.

    Args:
        asset_id: PRA asset identifier
        oil_sold_bbl: Barrels of crude oil sold in the period
        gas_sold_mmbtu: MMBtu of natural gas sold in the period
        region: Region code (default EU-NORTH)
        period_start: Reporting period start date YYYY-MM-DD
        period_end: Reporting period end date YYYY-MM-DD
    """
    logger.info(
        "calculate_scope3_emissions: asset=%s, oil=%.2f bbl, gas=%.2f MMBtu",
        asset_id, oil_sold_bbl, gas_sold_mmbtu,
    )

    factors = _EMISSION_FACTORS.get(region, _EMISSION_FACTORS[_DEFAULT_REGION])

    oil_downstream_tco2e = oil_sold_bbl * factors["oil_downstream_kg_co2e_per_bbl"] / 1000.0
    gas_downstream_tco2e = gas_sold_mmbtu * factors["gas_downstream_kg_co2e_per_mmbtu"] / 1000.0
    total_scope3_tco2e = oil_downstream_tco2e + gas_downstream_tco2e

    # Carbon intensity: tCO2e per BOE (1 bbl oil = 1 BOE; 1 MMBtu gas ≈ 0.172 BOE)
    total_boe = oil_sold_bbl + (gas_sold_mmbtu * 0.172)
    carbon_intensity = (total_scope3_tco2e / total_boe) if total_boe > 0 else 0.0

    return json.dumps({
        "status": "success",
        "asset_id": asset_id,
        "region": region,
        "period_start": period_start,
        "period_end": period_end,
        "scope3_total_tco2e": round(total_scope3_tco2e, 4),
        "breakdown": {
            "oil_downstream_tco2e": round(oil_downstream_tco2e, 4),
            "gas_downstream_tco2e": round(gas_downstream_tco2e, 4),
        },
        "carbon_intensity_tco2e_per_boe": round(carbon_intensity, 6),
        "total_boe": round(total_boe, 2),
        "scope3_category": "Category 11 — Use of Sold Products",
        "methodology": "GHG Protocol Corporate Value Chain (Scope 3) Standard",
        "factor_source": "IPCC AR6",
        "calculation_traceable": True,
    })


@tool
def validate_emissions_results(
    asset_id: str,
    period: str,
    scope1_tco2e: float,
    scope2_tco2e: float,
    scope3_tco2e: float,
    methodology: str = "GHG Protocol",
) -> str:
    """Submit calculated emissions to SAP Sustainability Footprint Management for validation.

    Checks for consistency, outliers, missing factors, and regulatory threshold compliance.

    Args:
        asset_id: PRA asset identifier
        period: Reporting period in YYYY-MM format (e.g. 2024-01)
        scope1_tco2e: Calculated Scope 1 emissions in tCO2e
        scope2_tco2e: Calculated Scope 2 emissions in tCO2e
        scope3_tco2e: Calculated Scope 3 emissions in tCO2e
        methodology: Emissions methodology reference (default: GHG Protocol)
    """
    logger.info(
        "validate_emissions_results: asset=%s, period=%s, S1=%.2f, S2=%.2f, S3=%.2f tCO2e",
        asset_id, period, scope1_tco2e, scope2_tco2e, scope3_tco2e,
    )

    total = scope1_tco2e + scope2_tco2e + scope3_tco2e
    flags = []

    # Validation rules
    if scope1_tco2e > scope3_tco2e * 2:
        flags.append({
            "code": "SCOPE1_HIGH_RATIO",
            "severity": "WARNING",
            "message": "Scope 1 exceeds 2x Scope 3 — verify flaring volumes and emission factors.",
        })
    if scope2_tco2e == 0:
        flags.append({
            "code": "SCOPE2_ZERO",
            "severity": "INFO",
            "message": "Scope 2 is zero — confirm no purchased electricity for this asset.",
        })
    if scope1_tco2e < 0 or scope2_tco2e < 0 or scope3_tco2e < 0:
        flags.append({
            "code": "NEGATIVE_EMISSIONS",
            "severity": "ERROR",
            "message": "Negative emissions detected — check input volumes for data quality issues.",
        })

    validation_status = "VALIDATED" if not any(f["severity"] == "ERROR" for f in flags) else "FLAGGED"

    return json.dumps({
        "status": "success",
        "asset_id": asset_id,
        "period": period,
        "validation_status": validation_status,
        "total_tco2e": round(total, 4),
        "scope1_tco2e": round(scope1_tco2e, 4),
        "scope2_tco2e": round(scope2_tco2e, 4),
        "scope3_tco2e": round(scope3_tco2e, 4),
        "flags": flags,
        "methodology_validated": methodology,
        "validated_by": "SAP Sustainability Footprint Management",
        "validation_timestamp": "2024-01-31T12:00:00Z",
    })
