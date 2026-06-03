"""Carbon Hotspot Detection Tools.

Real-time anomaly detection for flaring events, methane leaks,
and inefficient wells with severity scoring and corrective action recommendations.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Thresholds — configurable; these are illustrative industry benchmarks
_FLARE_BASELINE_MCF_PER_DAY = 150.0       # Rolling 30-day average baseline per well
_FLARE_REGULATORY_LIMIT_MCF_PER_DAY = 500.0
_METHANE_RATE_THRESHOLD_MCFD = 50.0        # mcf/day above which leak is flagged
_WELL_INTENSITY_VARIANCE_THRESHOLD = 0.25  # 25% above field average → flag


def _compute_severity(excess_pct: float) -> str:
    """Map excess percentage above threshold to severity level."""
    if excess_pct >= 1.0:        # ≥ 100% above threshold
        return "CRITICAL"
    elif excess_pct >= 0.5:      # ≥ 50% above threshold
        return "HIGH"
    elif excess_pct >= 0.2:      # ≥ 20% above threshold
        return "MEDIUM"
    else:
        return "LOW"


@tool
def detect_flaring_anomalies(
    well_id: str,
    period: str,
    flare_volume_mcf: float,
    baseline_mcf: float = _FLARE_BASELINE_MCF_PER_DAY,
    regulatory_limit_mcf: float = _FLARE_REGULATORY_LIMIT_MCF_PER_DAY,
) -> str:
    """Detect flaring anomalies by comparing reported flare volumes against baseline and regulatory limits.

    Args:
        well_id: PRA well identifier
        period: Date in YYYY-MM-DD format
        flare_volume_mcf: Actual flare volume in mcf for the period
        baseline_mcf: Rolling 30-day average flare baseline in mcf (default 150)
        regulatory_limit_mcf: Applicable regulatory flaring limit in mcf (default 500)
    """
    logger.info(
        "detect_flaring_anomalies: well=%s, flare=%.2f mcf, baseline=%.2f mcf",
        well_id, flare_volume_mcf, baseline_mcf,
    )

    anomaly = flare_volume_mcf > baseline_mcf
    regulatory_breach = flare_volume_mcf > regulatory_limit_mcf
    excess_vs_baseline = max(0.0, flare_volume_mcf - baseline_mcf)
    excess_pct = (excess_vs_baseline / baseline_mcf) if baseline_mcf > 0 else 0.0
    severity = _compute_severity(excess_pct) if anomaly else "NONE"

    # Estimated annual CO2e impact (52.2 kg CO2e/mcf × excess × 365 days / 1000)
    annual_impact_tco2e = (excess_vs_baseline * 52.2 * 365.0) / 1000.0

    recommended_action = None
    if regulatory_breach:
        recommended_action = "IMMEDIATE: Flaring exceeds regulatory limit. Initiate emergency gas capture or shut-in procedure. Notify regulatory authority."
    elif severity in ("HIGH", "CRITICAL"):
        recommended_action = "Install or activate gas capture/compression system. Investigate root cause (compressor failure, gas lift issue). Report within 24h."
    elif anomaly:
        recommended_action = "Review well production parameters. Check for compressor performance issues. Schedule inspection within 72h."

    return json.dumps({
        "status": "success",
        "well_id": well_id,
        "period": period,
        "anomaly_detected": anomaly,
        "regulatory_breach": regulatory_breach,
        "flare_volume_mcf": flare_volume_mcf,
        "baseline_mcf": baseline_mcf,
        "regulatory_limit_mcf": regulatory_limit_mcf,
        "excess_volume_mcf": round(excess_vs_baseline, 2),
        "excess_percentage": round(excess_pct * 100, 1),
        "severity": severity,
        "estimated_annual_impact_tco2e": round(annual_impact_tco2e, 2),
        "recommended_action": recommended_action,
    })


@tool
def detect_methane_leaks(
    well_completion_id: str,
    period: str,
    methane_rate_mcfd: float,
    equipment_type: str = "WELLHEAD",
) -> str:
    """Evaluate methane venting and fugitive emission rates for leak detection.

    Compares methane rate against threshold limits and assigns severity and repair priority.

    Args:
        well_completion_id: PRA well completion identifier
        period: Date in YYYY-MM-DD format
        methane_rate_mcfd: Methane emission/vent rate in mcf per day
        equipment_type: Equipment type (WELLHEAD, SEPARATOR, COMPRESSOR, PIPELINE, STORAGE)
    """
    logger.info(
        "detect_methane_leaks: completion=%s, methane_rate=%.2f mcfd, equip=%s",
        well_completion_id, methane_rate_mcfd, equipment_type,
    )

    # Equipment-specific thresholds
    thresholds = {
        "WELLHEAD": 50.0,
        "SEPARATOR": 30.0,
        "COMPRESSOR": 80.0,
        "PIPELINE": 20.0,
        "STORAGE": 25.0,
    }
    threshold = thresholds.get(equipment_type, _METHANE_RATE_THRESHOLD_MCFD)
    leak_detected = methane_rate_mcfd > threshold
    excess = max(0.0, methane_rate_mcfd - threshold)
    excess_pct = (excess / threshold) if threshold > 0 else 0.0
    severity = _compute_severity(excess_pct) if leak_detected else "NONE"

    # Convert mcfd to tCH4/day: 1 mcf CH4 ≈ 19.2 kg; GWP100 = 28 → tCO2e/day
    leak_rate_tch4_per_day = (methane_rate_mcfd * 19.2) / 1000.0
    annual_impact_tco2e = leak_rate_tch4_per_day * 28.0 * 365.0

    repair_priority = {
        "CRITICAL": "IMMEDIATE — shut-in or emergency repair within 24 hours",
        "HIGH": "URGENT — schedule repair within 72 hours",
        "MEDIUM": "PLANNED — schedule repair within 2 weeks",
        "LOW": "ROUTINE — include in next scheduled maintenance",
        "NONE": "No action required",
    }

    return json.dumps({
        "status": "success",
        "well_completion_id": well_completion_id,
        "period": period,
        "equipment_type": equipment_type,
        "leak_detected": leak_detected,
        "methane_rate_mcfd": methane_rate_mcfd,
        "threshold_mcfd": threshold,
        "excess_mcfd": round(excess, 2),
        "severity": severity,
        "leak_rate_tch4_per_day": round(leak_rate_tch4_per_day, 4),
        "estimated_annual_impact_tco2e": round(annual_impact_tco2e, 2),
        "repair_priority": repair_priority.get(severity, "No action required"),
    })


@tool
def detect_inefficient_wells(
    well_id: str,
    field_avg_intensity_tco2e_per_boe: float,
    well_intensity_tco2e_per_boe: float,
) -> str:
    """Identify wells with carbon intensity significantly above field average.

    Args:
        well_id: PRA well identifier
        field_avg_intensity_tco2e_per_boe: Field-average carbon intensity in tCO2e per BOE
        well_intensity_tco2e_per_boe: This well's carbon intensity in tCO2e per BOE
    """
    logger.info(
        "detect_inefficient_wells: well=%s, field_avg=%.4f, well=%.4f tCO2e/BOE",
        well_id, field_avg_intensity_tco2e_per_boe, well_intensity_tco2e_per_boe,
    )

    variance_pct = (
        (well_intensity_tco2e_per_boe - field_avg_intensity_tco2e_per_boe)
        / field_avg_intensity_tco2e_per_boe
        if field_avg_intensity_tco2e_per_boe > 0
        else 0.0
    )

    inefficiency_flag = variance_pct > _WELL_INTENSITY_VARIANCE_THRESHOLD
    severity = _compute_severity(variance_pct) if inefficiency_flag else "NONE"

    # Root cause hypothesis based on variance magnitude
    if variance_pct > 1.0:
        root_cause = "Severely elevated flaring or venting — likely equipment failure or process upset"
    elif variance_pct > 0.5:
        root_cause = "Significant flaring or methane venting above field norm — investigate gas handling"
    elif variance_pct > 0.25:
        root_cause = "Moderately elevated intensity — possible excessive water cut or declining GOR"
    else:
        root_cause = "Within acceptable variance range"

    annual_improvement_potential_tco2e = (
        (well_intensity_tco2e_per_boe - field_avg_intensity_tco2e_per_boe)
        * 365.0  # approximate daily BOE × days
    )

    return json.dumps({
        "status": "success",
        "well_id": well_id,
        "inefficiency_flag": inefficiency_flag,
        "field_avg_intensity_tco2e_per_boe": round(field_avg_intensity_tco2e_per_boe, 6),
        "well_intensity_tco2e_per_boe": round(well_intensity_tco2e_per_boe, 6),
        "variance_from_field_avg_pct": round(variance_pct * 100, 1),
        "severity": severity,
        "root_cause_hypothesis": root_cause,
        "annual_improvement_potential_tco2e": round(abs(annual_improvement_potential_tco2e), 2),
    })


@tool
def generate_hotspot_alert(
    asset_id: str,
    asset_type: str,
    alert_type: str,
    severity: str,
    metric_name: str,
    current_value: float,
    threshold_value: float,
    recommended_action: str,
    estimated_annual_impact_tco2e: float = 0.0,
) -> str:
    """Create a structured hotspot alert object from anomaly detection results.

    Args:
        asset_id: PRA asset identifier (well ID, field ID, or plant ID)
        asset_type: Asset type — WELL, FIELD, PLANT, RESERVOIR
        alert_type: Type of alert — FLARING, METHANE_LEAK, INEFFICIENT_WELL
        severity: Alert severity — LOW, MEDIUM, HIGH, CRITICAL
        metric_name: Name of the metric that triggered the alert
        current_value: Current observed value of the metric
        threshold_value: Threshold value that was exceeded
        recommended_action: Specific recommended corrective action
        estimated_annual_impact_tco2e: Estimated annualized emissions impact in tCO2e
    """
    alert_id = str(uuid.uuid4())[:8].upper()
    excess_amount = max(0.0, current_value - threshold_value)

    alert = {
        "alert_id": f"CCIE-{alert_type[:3]}-{alert_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_type": asset_type,
        "asset_id": asset_id,
        "alert_type": alert_type,
        "severity": severity,
        "metric_name": metric_name,
        "current_value": round(current_value, 4),
        "threshold_value": round(threshold_value, 4),
        "excess_amount": round(excess_amount, 4),
        "recommended_action": recommended_action,
        "estimated_annual_impact_tco2e": round(estimated_annual_impact_tco2e, 2),
        "status": "OPEN",
        "requires_human_approval_to_close": severity in ("HIGH", "CRITICAL"),
    }

    logger.warning(
        "HOTSPOT ALERT [%s] %s — %s on %s %s: %.2f (threshold: %.2f)",
        alert["alert_id"], severity, alert_type, asset_type, asset_id,
        current_value, threshold_value,
    )

    return json.dumps({"status": "success", "alert": alert})
