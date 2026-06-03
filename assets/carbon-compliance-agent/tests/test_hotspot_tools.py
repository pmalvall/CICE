"""Unit tests for Carbon Hotspot Detection Tools."""

import json
import pytest


def test_detect_flaring_anomaly_when_exceeds_baseline():
    from tools.hotspot_tools import detect_flaring_anomalies
    result = json.loads(detect_flaring_anomalies.invoke({
        "well_id": "WELL-001",
        "period": "2024-01-15",
        "flare_volume_mcf": 320.0,  # > baseline of 150
        "baseline_mcf": 150.0,
    }))
    assert result["status"] == "success"
    assert result["anomaly_detected"] is True
    assert result["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert result["excess_volume_mcf"] > 0


def test_detect_flaring_no_anomaly_within_baseline():
    from tools.hotspot_tools import detect_flaring_anomalies
    result = json.loads(detect_flaring_anomalies.invoke({
        "well_id": "WELL-002",
        "period": "2024-01-15",
        "flare_volume_mcf": 100.0,  # < baseline of 150
        "baseline_mcf": 150.0,
    }))
    assert result["anomaly_detected"] is False
    assert result["severity"] == "NONE"


def test_detect_flaring_regulatory_breach():
    from tools.hotspot_tools import detect_flaring_anomalies
    result = json.loads(detect_flaring_anomalies.invoke({
        "well_id": "WELL-003",
        "period": "2024-01-15",
        "flare_volume_mcf": 600.0,  # > regulatory limit of 500
        "baseline_mcf": 150.0,
        "regulatory_limit_mcf": 500.0,
    }))
    assert result["regulatory_breach"] is True
    assert result["severity"] == "CRITICAL"
    assert "IMMEDIATE" in result["recommended_action"]


def test_detect_methane_leak_above_threshold():
    from tools.hotspot_tools import detect_methane_leaks
    result = json.loads(detect_methane_leaks.invoke({
        "well_completion_id": "WC-001",
        "period": "2024-01-15",
        "methane_rate_mcfd": 120.0,  # > WELLHEAD threshold of 50
        "equipment_type": "WELLHEAD",
    }))
    assert result["leak_detected"] is True
    assert result["severity"] in ("MEDIUM", "HIGH", "CRITICAL")
    assert result["estimated_annual_impact_tco2e"] > 0


def test_detect_methane_leak_below_threshold():
    from tools.hotspot_tools import detect_methane_leaks
    result = json.loads(detect_methane_leaks.invoke({
        "well_completion_id": "WC-002",
        "period": "2024-01-15",
        "methane_rate_mcfd": 20.0,  # < WELLHEAD threshold of 50
        "equipment_type": "WELLHEAD",
    }))
    assert result["leak_detected"] is False
    assert result["severity"] == "NONE"


def test_detect_methane_severity_levels():
    from tools.hotspot_tools import detect_methane_leaks
    # HIGH severity: > 50% above threshold
    result = json.loads(detect_methane_leaks.invoke({
        "well_completion_id": "WC-003",
        "period": "2024-01-15",
        "methane_rate_mcfd": 80.0,  # 60% above threshold of 50
    }))
    assert result["severity"] == "HIGH"


def test_detect_inefficient_wells_above_threshold():
    from tools.hotspot_tools import detect_inefficient_wells
    result = json.loads(detect_inefficient_wells.invoke({
        "well_id": "WELL-HIGH",
        "field_avg_intensity_tco2e_per_boe": 0.04,
        "well_intensity_tco2e_per_boe": 0.065,  # 62.5% above avg → clearly HIGH
    }))
    assert result["inefficiency_flag"] is True
    assert result["variance_from_field_avg_pct"] > 50.0
    assert result["severity"] == "HIGH"


def test_detect_inefficient_wells_within_threshold():
    from tools.hotspot_tools import detect_inefficient_wells
    result = json.loads(detect_inefficient_wells.invoke({
        "well_id": "WELL-OK",
        "field_avg_intensity_tco2e_per_boe": 0.04,
        "well_intensity_tco2e_per_boe": 0.042,  # 5% above avg — within 25% threshold
    }))
    assert result["inefficiency_flag"] is False
    assert result["severity"] == "NONE"


def test_generate_hotspot_alert_structure():
    from tools.hotspot_tools import generate_hotspot_alert
    result = json.loads(generate_hotspot_alert.invoke({
        "asset_id": "WELL-001",
        "asset_type": "WELL",
        "alert_type": "FLARING",
        "severity": "HIGH",
        "metric_name": "flare_volume_mcf",
        "current_value": 320.0,
        "threshold_value": 150.0,
        "recommended_action": "Install gas capture system",
        "estimated_annual_impact_tco2e": 89.5,
    }))
    assert result["status"] == "success"
    alert = result["alert"]
    assert alert["alert_type"] == "FLARING"
    assert alert["severity"] == "HIGH"
    assert alert["status"] == "OPEN"
    assert alert["requires_human_approval_to_close"] is True
    assert alert["excess_amount"] == pytest.approx(170.0, abs=0.1)
    assert alert["alert_id"].startswith("CCIE-FLA-")
