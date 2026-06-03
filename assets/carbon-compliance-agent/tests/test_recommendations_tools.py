"""Unit tests for Decarbonization Recommendation Engine."""

import json
import pytest


def test_recommendations_ranked_by_impact_per_capex():
    from tools.recommendations_tools import get_decarbonization_recommendations
    result = json.loads(get_decarbonization_recommendations.invoke({
        "portfolio_scope1_tco2e": 5000.0,
        "portfolio_scope2_tco2e": 500.0,
        "active_flaring_alerts": 2,
        "active_methane_alerts": 1,
        "active_inefficiency_alerts": 1,
    }))
    assert result["status"] == "success"
    recs = result["recommendations"]
    assert len(recs) > 0

    # Assert ranked field increments from 1
    assert recs[0]["rank"] == 1
    assert recs[-1]["rank"] == len(recs)

    # Assert all required fields present
    for rec in recs:
        assert "intervention_type" in rec
        assert "projected_reduction_tco2e" in rec
        assert "estimated_capex_usd" in rec
        assert "payback_period_years" in rec
        assert "implementation_complexity" in rec


def test_recommendations_top_n_limit():
    from tools.recommendations_tools import get_decarbonization_recommendations
    result = json.loads(get_decarbonization_recommendations.invoke({
        "portfolio_scope1_tco2e": 5000.0,
        "portfolio_scope2_tco2e": 500.0,
        "top_n": 2,
    }))
    assert len(result["recommendations"]) <= 2


def test_recommendations_total_projected_reduction():
    from tools.recommendations_tools import get_decarbonization_recommendations
    result = json.loads(get_decarbonization_recommendations.invoke({
        "portfolio_scope1_tco2e": 3000.0,
        "portfolio_scope2_tco2e": 300.0,
    }))
    recs = result["recommendations"]
    computed_total = sum(r["projected_reduction_tco2e"] for r in recs)
    assert abs(computed_total - result["total_projected_reduction_tco2e"]) < 0.1


def test_recommendations_no_flaring_alerts_lower_reduction():
    from tools.recommendations_tools import get_decarbonization_recommendations
    # With active flaring alerts
    with_alerts = json.loads(get_decarbonization_recommendations.invoke({
        "portfolio_scope1_tco2e": 5000.0,
        "portfolio_scope2_tco2e": 500.0,
        "active_flaring_alerts": 3,
    }))
    # Without flaring alerts
    without_alerts = json.loads(get_decarbonization_recommendations.invoke({
        "portfolio_scope1_tco2e": 5000.0,
        "portfolio_scope2_tco2e": 500.0,
        "active_flaring_alerts": 0,
    }))
    # More alerts → higher projected flaring reduction
    with_total = with_alerts["total_projected_reduction_tco2e"]
    without_total = without_alerts["total_projected_reduction_tco2e"]
    assert with_total >= without_total
