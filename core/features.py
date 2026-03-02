from __future__ import annotations

from typing import Iterable

from .schemas import CostBreakdownItem, CostEstimate, CostModelInput, DesignDiff, DesignPackage


def _norm_set(values: Iterable[str]) -> set[str]:
    return {value.strip() for value in values if value and value.strip()}


def diff_design_packages(
    from_task: str, from_package: DesignPackage, to_task: str, to_package: DesignPackage
) -> DesignDiff:
    from_design = from_package.design
    to_design = to_package.design

    from_components = _norm_set(component.name for component in from_design.components)
    to_components = _norm_set(component.name for component in to_design.components)

    from_reqs = _norm_set(from_design.functional_requirements)
    to_reqs = _norm_set(to_design.functional_requirements)

    from_risks = _norm_set(from_design.bottlenecks + from_design.tradeoffs)
    to_risks = _norm_set(to_design.bottlenecks + to_design.tradeoffs)

    added_components = sorted(to_components - from_components)
    removed_components = sorted(from_components - to_components)
    added_requirements = sorted(to_reqs - from_reqs)
    removed_requirements = sorted(from_reqs - to_reqs)
    added_risks = sorted(to_risks - from_risks)
    removed_risks = sorted(from_risks - to_risks)

    risk_changes = [f"Added risk: {risk}" for risk in added_risks] + [
        f"Removed risk: {risk}" for risk in removed_risks
    ]
    summary = (
        f"{len(added_components)} component(s) added, "
        f"{len(removed_components)} removed, "
        f"{len(added_requirements)} requirement(s) added, "
        f"{len(removed_requirements)} removed."
    )
    return DesignDiff(
        from_task=from_task,
        to_task=to_task,
        added_components=added_components,
        removed_components=removed_components,
        added_requirements=added_requirements,
        removed_requirements=removed_requirements,
        risk_changes=risk_changes,
        summary=summary,
    )


def estimate_cost(package: DesignPackage, model_input: CostModelInput) -> CostEstimate:
    component_count = max(1, len(package.design.components))
    db_complexity = max(1, len(package.design.data_model_entities))

    compute_cost = round((model_input.peak_qps * 0.35) + (component_count * 12), 2)
    storage_cost = round((model_input.storage_gb * 0.08), 2)
    network_cost = round((model_input.monthly_active_users / 10_000) * 18, 2)
    observability_cost = round((component_count * 6) + (model_input.peak_qps * 0.05), 2)
    resilience_cost = round((db_complexity * 9), 2)

    items = [
        CostBreakdownItem(
            category="Compute",
            monthly_cost_usd=compute_cost,
            rationale="Application services, autoscaling workers, and orchestration.",
        ),
        CostBreakdownItem(
            category="Storage",
            monthly_cost_usd=storage_cost,
            rationale="Primary database and object storage footprint.",
        ),
        CostBreakdownItem(
            category="Network",
            monthly_cost_usd=network_cost,
            rationale="Egress, API gateway, and load-balancer traffic.",
        ),
        CostBreakdownItem(
            category="Observability",
            monthly_cost_usd=observability_cost,
            rationale="Logs, metrics, traces, and dashboards.",
        ),
        CostBreakdownItem(
            category="Resilience",
            monthly_cost_usd=resilience_cost,
            rationale="Backups, replication, and disaster recovery overhead.",
        ),
    ]
    total = round(sum(item.monthly_cost_usd for item in items), 2)
    assumptions = [
        f"Peak load assumed at {model_input.peak_qps} QPS.",
        f"Data retention assumed at {model_input.retention_days} days.",
        "Pricing model is heuristic and should be replaced with cloud provider calculators.",
    ]
    return CostEstimate(
        assumptions=assumptions,
        items=items,
        total_monthly_cost_usd=total,
    )
