from __future__ import annotations

from typing import List

from .schemas import DesignResponse, QualityDimension, QualityReport


def _score_by_presence(text: str, keywords: List[str]) -> int:
    haystack = text.lower()
    hits = sum(1 for word in keywords if word in haystack)
    if hits >= max(1, len(keywords) // 2):
        return 9
    if hits >= 2:
        return 7
    if hits >= 1:
        return 5
    return 3


def _missing_sections(design: DesignResponse) -> List[str]:
    missing: List[str] = []
    if not design.api_contracts:
        missing.append("API contracts")
    if not design.data_model_entities:
        missing.append("Data model entities")
    if not design.operational_runbook:
        missing.append("Operational runbook")
    if not design.components:
        missing.append("Component breakdown")
    if not design.observability_and_slos.strip():
        missing.append("Observability and SLO definitions")
    return missing


def evaluate_design_quality(design: DesignResponse) -> QualityReport:
    reliability_keywords = [
        "retry",
        "circuit breaker",
        "idempot",
        "backoff",
        "dead letter",
        "failover",
    ]
    security_keywords = [
        "oauth",
        "jwt",
        "encryption",
        "kms",
        "rbac",
        "audit",
    ]
    operations_keywords = [
        "alert",
        "slo",
        "dashboard",
        "runbook",
        "on-call",
        "incident",
    ]
    delivery_keywords = [
        "canary",
        "blue/green",
        "rollback",
        "feature flag",
        "migration",
    ]

    reliability_score = _score_by_presence(
        design.reliability_and_resilience, reliability_keywords
    )
    security_score = _score_by_presence(
        design.security_and_compliance, security_keywords
    )
    observability_score = _score_by_presence(
        design.observability_and_slos, operations_keywords
    )
    delivery_score = _score_by_presence(
        design.deployment_and_release_strategy, delivery_keywords
    )
    architecture_completeness = min(
        10,
        max(
            3,
            (
                int(bool(design.components))
                + int(bool(design.api_contracts))
                + int(bool(design.data_model_entities))
                + int(bool(design.sequence_of_operations))
                + int(bool(design.database_design.strip()))
                + int(bool(design.capacity_estimation.strip()))
            )
            + 3,
        ),
    )

    dimensions: List[QualityDimension] = [
        QualityDimension(
            name="Reliability",
            score=reliability_score,
            rationale="Assessed from resilience mechanisms in reliability strategy.",
        ),
        QualityDimension(
            name="Security",
            score=security_score,
            rationale="Assessed from auth, encryption, and access-control depth.",
        ),
        QualityDimension(
            name="Observability",
            score=observability_score,
            rationale="Assessed from SLO, metrics, alerting, and incident readiness.",
        ),
        QualityDimension(
            name="Delivery",
            score=delivery_score,
            rationale="Assessed from rollout, rollback, and migration safety details.",
        ),
        QualityDimension(
            name="Architecture Completeness",
            score=architecture_completeness,
            rationale="Assessed from required implementation sections coverage.",
        ),
    ]
    total_score = sum(d.score for d in dimensions) * 2

    missing = _missing_sections(design)
    recommendations: List[str] = []
    if reliability_score < 7:
        recommendations.append(
            "Add idempotency, DLQ policy, retries with backoff, and failover strategy."
        )
    if security_score < 7:
        recommendations.append(
            "Add threat model, key rotation, RBAC model, and audit/event "
            "retention policy."
        )
    if observability_score < 7:
        recommendations.append(
            "Define golden signals, SLO targets, and pager-backed alert thresholds."
        )
    if delivery_score < 7:
        recommendations.append(
            "Add canary rollout with automated rollback and schema migration "
            "guardrails."
        )
    if not recommendations:
        recommendations.append(
            "Quality is strong; next step is benchmark-based load and chaos validation."
        )

    return QualityReport(
        total_score=total_score,
        dimensions=dimensions,
        missing_areas=missing,
        recommendations=recommendations,
    )
