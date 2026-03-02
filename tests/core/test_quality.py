from __future__ import annotations

import pytest

from core.quality import evaluate_design_quality
from core.schemas import DesignResponse


@pytest.fixture
def minimal_design() -> DesignResponse:
    """Return a minimal DesignResponse for testing."""
    return DesignResponse(
        assumptions=[],
        functional_requirements=[],
        non_functional_requirements=[],
        api_contracts=[],
        data_model_entities=[],
        sequence_of_operations=[],
        high_level_architecture="",
        components=[],
        database_design="",
        consistency_and_transactions="",
        scaling_strategy="",
        caching_strategy="",
        capacity_estimation="",
        reliability_and_resilience="",
        security_and_compliance="",
        observability_and_slos="",
        deployment_and_release_strategy="",
        disaster_recovery="",
        cost_estimation="",
        testing_strategy="",
        operational_runbook=[],
        bottlenecks=[],
        tradeoffs=[],
        mermaid_diagram="",
    )


def test_evaluate_design_quality_minimal(minimal_design: DesignResponse):
    """Test quality evaluation with a minimal design."""
    report = evaluate_design_quality(minimal_design)
    assert report.total_score >= 0
    assert len(report.dimensions) == 5
    assert "API contracts" in report.missing_areas
    assert "Data model entities" in report.missing_areas


def test_evaluate_design_quality_with_keywords(minimal_design: DesignResponse):
    """Test that keywords in the design increase the score."""
    minimal_design.reliability_and_resilience = "retry circuit breaker"
    minimal_design.security_and_compliance = "oauth jwt"
    minimal_design.observability_and_slos = "alert slo"
    minimal_design.deployment_and_release_strategy = "canary rollback"

    report = evaluate_design_quality(minimal_design)

    assert report.dimensions[0].score > 3
    assert report.dimensions[1].score > 3
    assert report.dimensions[2].score > 3
    assert report.dimensions[3].score > 3
