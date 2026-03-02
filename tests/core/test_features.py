from __future__ import annotations

from core.features import diff_design_packages, estimate_cost
from core.schemas import Component, CostModelInput, DesignPackage, DesignResponse, QualityReport


def _make_package(task_suffix: str) -> DesignPackage:
    design = DesignResponse(
        assumptions=[],
        functional_requirements=[f"req-{task_suffix}"],
        non_functional_requirements=[],
        api_contracts=[],
        data_model_entities=["User", "Event"],
        sequence_of_operations=[],
        high_level_architecture="",
        components=[
            Component(
                name=f"api-{task_suffix}",
                type="service",
                description="desc",
                connections=[],
            )
        ],
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
        bottlenecks=["single region"],
        tradeoffs=["higher cost"],
        mermaid_diagram="",
    )
    quality = QualityReport(total_score=50, dimensions=[], missing_areas=[], recommendations=[])
    return DesignPackage(
        design=design,
        mermaid_diagram="",
        quality_report=quality,
    )


def test_diff_design_packages():
    source = _make_package("a")
    target = _make_package("b")
    diff = diff_design_packages("task-a", source, "task-b", target)
    assert diff.from_task == "task-a"
    assert diff.to_task == "task-b"
    assert "api-b" in diff.added_components
    assert "api-a" in diff.removed_components


def test_estimate_cost():
    package = _make_package("a")
    estimate = estimate_cost(
        package,
        CostModelInput(
            monthly_active_users=10000,
            peak_qps=120,
            storage_gb=300,
            retention_days=30,
        ),
    )
    assert estimate.total_monthly_cost_usd > 0
    assert len(estimate.items) >= 3
