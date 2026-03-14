from __future__ import annotations

from pathlib import Path

import pytest

from core import history
from core.schemas import Component, DesignPackage, DesignResponse, QualityReport


def _package() -> DesignPackage:
    design = DesignResponse(
        assumptions=[],
        functional_requirements=[],
        non_functional_requirements=[],
        api_contracts=[],
        data_model_entities=[],
        sequence_of_operations=[],
        high_level_architecture="",
        components=[Component(name="api", type="service", description="", connections=[])],
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
    return DesignPackage(
        design=design,
        mermaid_diagram="",
        quality_report=QualityReport(total_score=10, dimensions=[]),
    )


def test_history_create_and_update(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / ".history.json")
    entry = history.create_history_entry("task", _package(), tags=["tag-a"])
    assert entry.task == "task"
    assert entry.tags == ["tag-a"]

    all_entries = history.list_history_entries()
    assert len(all_entries) == 1

    updated = history.set_review_status(entry.version_id, "approved")
    assert updated is not None
    assert updated.status == "approved"

    commented = history.add_reviewer_comment(entry.version_id, "looks good")
    assert commented is not None
    assert commented.reviewer_comments == ["looks good"]


def test_history_rejects_invalid_review_status(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / ".history.json")
    entry = history.create_history_entry("task", _package(), tags=[])

    with pytest.raises(ValueError):
        history.set_review_status(entry.version_id, "bogus")

    reloaded = history.list_history_entries()
    assert len(reloaded) == 1
    assert reloaded[0].version_id == entry.version_id
    assert reloaded[0].status == "draft"
