"""Decarbonization Recommendation Engine.

Generates prioritized intervention recommendations ranked by
cost-vs-emissions impact (tCO2e reduction per USD capex invested).
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_decarbonization_recommendations(
    portfolio_scope1_tco2e: float,
    portfolio_scope2_tco2e: float,
    active_flaring_alerts: int = 0,
    active_methane_alerts: int = 0,
    active_inefficiency_alerts: int = 0,
    top_n: int = 10,
) -> str:
    """Analyze the emissions profile and generate ranked decarbonization interventions.

    Interventions are ranked by emissions reduction potential per USD capital expenditure
    (highest tCO2e/USD = highest priority).

    Args:
        portfolio_scope1_tco2e: Total portfolio Scope 1 emissions in tCO2e
        portfolio_scope2_tco2e: Total portfolio Scope 2 emissions in tCO2e
        active_flaring_alerts: Number of open HIGH/CRITICAL flaring alerts
        active_methane_alerts: Number of open HIGH/CRITICAL methane leak alerts
        active_inefficiency_alerts: Number of open HIGH/CRITICAL well inefficiency alerts
        top_n: Maximum number of recommendations to return (default 10, max 10)
    """
    top_n = min(top_n, 10)
    total_scope1_scope2 = portfolio_scope1_tco2e + portfolio_scope2_tco2e

    logger.info(
        "get_decarbonization_recommendations: scope1=%.2f, scope2=%.2f tCO2e, "
        "flaring_alerts=%d, methane_alerts=%d, inefficiency_alerts=%d",
        portfolio_scope1_tco2e, portfolio_scope2_tco2e,
        active_flaring_alerts, active_methane_alerts, active_inefficiency_alerts,
    )

    # Base recommendation catalogue — tailored by active alert profile
    all_recommendations = []

    # Recommendation 1: Flare gas capture (highest impact if flaring alerts present)
    flare_reduction_pct = 0.35 if active_flaring_alerts > 0 else 0.10
    flare_capex = 2_500_000
    flare_reduction_tco2e = portfolio_scope1_tco2e * flare_reduction_pct
    all_recommendations.append({
        "intervention_type": "Flare Gas Capture & Recovery System",
        "target_asset": "All assets with active flaring alerts" if active_flaring_alerts > 0 else "Portfolio-wide",
        "description": "Install/upgrade flare gas capture compressors to redirect flared gas to sales or fuel gas system. Eliminates direct combustion and CO2e emissions.",
        "projected_reduction_tco2e": round(flare_reduction_tco2e, 2),
        "estimated_capex_usd": flare_capex,
        "payback_period_years": round(flare_capex / (flare_reduction_tco2e * 50.0), 1),  # $50/tCO2e carbon price proxy
        "cost_saving_usd_per_year": round(flare_reduction_tco2e * 25.0, 0),  # Gas value recovered
        "implementation_complexity": "MEDIUM",
        "regulatory_compliance_impact": "Directly reduces CSRD ESRS E1-6 Scope 1 and addresses regulatory flaring limits",
        "priority_score": flare_reduction_tco2e / flare_capex,
    })

    # Recommendation 2: Methane leak detection and repair (LDAR)
    methane_reduction_pct = 0.25 if active_methane_alerts > 0 else 0.08
    methane_capex = 800_000
    methane_reduction_tco2e = portfolio_scope1_tco2e * methane_reduction_pct
    all_recommendations.append({
        "intervention_type": "Methane Leak Detection and Repair (LDAR) Program",
        "target_asset": "All assets with active methane leak alerts" if active_methane_alerts > 0 else "Portfolio-wide",
        "description": "Implement optical gas imaging (OGI) cameras and continuous monitoring sensors. Conduct quarterly LDAR surveys. Repair identified leaks within 30 days.",
        "projected_reduction_tco2e": round(methane_reduction_tco2e, 2),
        "estimated_capex_usd": methane_capex,
        "payback_period_years": round(methane_capex / (methane_reduction_tco2e * 50.0), 1),
        "cost_saving_usd_per_year": round(methane_reduction_tco2e * 35.0, 0),  # Methane has higher value
        "implementation_complexity": "LOW",
        "regulatory_compliance_impact": "Reduces Scope 1 fugitive emissions; supports IRA methane fee compliance (US assets)",
        "priority_score": methane_reduction_tco2e / methane_capex,
    })

    # Recommendation 3: Renewable electricity procurement (Scope 2 reduction)
    re_reduction_pct = 0.80
    re_capex = 500_000
    re_reduction_tco2e = portfolio_scope2_tco2e * re_reduction_pct
    all_recommendations.append({
        "intervention_type": "Renewable Energy Certificates (RECs) / PPA Procurement",
        "target_asset": "All assets with grid electricity consumption",
        "description": "Procure renewable energy certificates or enter power purchase agreements for offshore/onshore operations. Transitions Scope 2 to market-based zero-carbon electricity.",
        "projected_reduction_tco2e": round(re_reduction_tco2e, 2),
        "estimated_capex_usd": re_capex,
        "payback_period_years": round(re_capex / max(re_reduction_tco2e * 50.0, 1), 1),
        "cost_saving_usd_per_year": 0.0,  # RECs are a cost; no direct saving
        "implementation_complexity": "LOW",
        "regulatory_compliance_impact": "Eliminates Scope 2 (market-based) for CSRD and IFRS S2 reporting",
        "priority_score": re_reduction_tco2e / re_capex,
    })

    # Recommendation 4: Electric compression (replacing gas-driven compressors)
    elec_comp_capex = 5_000_000
    elec_comp_reduction_tco2e = portfolio_scope1_tco2e * 0.12
    all_recommendations.append({
        "intervention_type": "Electrification of Gas-Driven Compression",
        "target_asset": "Compressor stations at PLANT-001 and PLANT-002",
        "description": "Replace reciprocating gas-driven compressors with electric motor-driven equivalents. Eliminates direct combustion emissions from compression and reduces methane slip.",
        "projected_reduction_tco2e": round(elec_comp_reduction_tco2e, 2),
        "estimated_capex_usd": elec_comp_capex,
        "payback_period_years": round(elec_comp_capex / (elec_comp_reduction_tco2e * 50.0), 1),
        "cost_saving_usd_per_year": round(elec_comp_reduction_tco2e * 15.0, 0),  # Fuel gas savings
        "implementation_complexity": "HIGH",
        "regulatory_compliance_impact": "Significant Scope 1 combustion reduction; improves CSRD carbon intensity metric",
        "priority_score": elec_comp_reduction_tco2e / elec_comp_capex,
    })

    # Recommendation 5: Well optimization for inefficient wells
    if active_inefficiency_alerts > 0:
        well_opt_capex = 1_200_000
        well_opt_reduction_tco2e = portfolio_scope1_tco2e * 0.08
        all_recommendations.append({
            "intervention_type": "Well Performance Optimization (ESP/Gas Lift Redesign)",
            "target_asset": f"{active_inefficiency_alerts} well(s) flagged as high-carbon-intensity outliers",
            "description": "Redesign artificial lift (ESP/gas lift) parameters to optimize production rate relative to gas consumption. Install downhole sensors for real-time optimization. Reduces per-BOE carbon intensity.",
            "projected_reduction_tco2e": round(well_opt_reduction_tco2e, 2),
            "estimated_capex_usd": well_opt_capex,
            "payback_period_years": round(well_opt_capex / (well_opt_reduction_tco2e * 50.0), 1),
            "cost_saving_usd_per_year": round(well_opt_reduction_tco2e * 20.0, 0),
            "implementation_complexity": "MEDIUM",
            "regulatory_compliance_impact": "Improves carbon intensity per BOE metric for CSRD ESRS E1-4",
            "priority_score": well_opt_reduction_tco2e / well_opt_capex,
        })

    # Sort by priority score (tCO2e reduction / capex) descending
    all_recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

    # Add rank and clean up priority_score from output
    ranked = []
    for i, rec in enumerate(all_recommendations[:top_n], start=1):
        rec_out = {k: v for k, v in rec.items() if k != "priority_score"}
        rec_out["rank"] = i
        ranked.append(rec_out)

    total_projected_reduction = sum(r["projected_reduction_tco2e"] for r in ranked)
    total_capex = sum(r["estimated_capex_usd"] for r in ranked)

    logger.info(
        "Decarbonization recommendations generated: count=%d, total_projected_reduction=%.2f tCO2e, total_capex=$%.0f",
        len(ranked), total_projected_reduction, total_capex,
    )

    return json.dumps({
        "status": "success",
        "recommendation_count": len(ranked),
        "total_projected_reduction_tco2e": round(total_projected_reduction, 2),
        "total_estimated_capex_usd": total_capex,
        "portfolio_reduction_pct": round(total_projected_reduction / max(total_scope1_scope2, 1) * 100, 1),
        "recommendations": ranked,
    })
