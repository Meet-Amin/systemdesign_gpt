from __future__ import annotations

from typing import Iterable, List

import streamlit as st

from core.diagram import build_diagram
from core.generator import DesignGenerator
from core.schemas import DesignPackage, DesignResponse


PAGE_TITLE = "SystemDesign-GPT"
DEFAULT_QUESTION = "Implement real-time notifications for a project management SaaS app."


st.set_page_config(page_title=PAGE_TITLE, layout="wide")


def init_state() -> None:
    defaults = {
        "question": DEFAULT_QUESTION,
        "design_response": None,
        "error_message": "",
        "need_design": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_list(title: str, items: Iterable[str]) -> None:
    st.subheader(title)
    if not items:
        st.write("(none provided)")
        return
    for element in items:
        st.markdown(f"- {element}")


def _build_export_markdown(question: str, package: DesignPackage, diagram: str) -> str:
    design = package.design
    sections: List[str] = []
    sections.append("# SystemDesign-GPT Output")
    sections.append("## Design Problem")
    sections.append(question)
    sections.append("## Quality Score")
    sections.append(f"- Total Score: {package.quality_report.total_score}/100")
    for dimension in package.quality_report.dimensions:
        sections.append(
            f"- {dimension.name}: {dimension.score}/10 ({dimension.rationale})"
        )
    if package.quality_report.missing_areas:
        sections.append("## Missing Areas")
        sections.extend(f"- {item}" for item in package.quality_report.missing_areas)
    if package.quality_report.recommendations:
        sections.append("## Improvement Recommendations")
        sections.extend(
            f"- {item}" for item in package.quality_report.recommendations
        )
    if package.alternatives:
        sections.append("## Architecture Alternatives")
        for alt in package.alternatives:
            sections.append(f"- **{alt.name}**: {alt.focus}")
            sections.append(f"  - Summary: {alt.summary}")
            if alt.strengths:
                sections.append(f"  - Strengths: {', '.join(alt.strengths)}")
            if alt.risks:
                sections.append(f"  - Risks: {', '.join(alt.risks)}")
    if package.decision_matrix:
        sections.append("## Decision Matrix")
        for row in package.decision_matrix:
            sections.append(
                f"- **{row.option}** | Latency {row.latency_score}/5 | Cost {row.cost_score}/5 | "
                f"Complexity {row.complexity_score}/5 | Reliability {row.reliability_score}/5 | "
                f"Delivery {row.delivery_speed_score}/5"
            )
            sections.append(f"  - Notes: {row.notes}")
        if package.recommended_option:
            sections.append(f"- Recommended Option: **{package.recommended_option}**")
    sections.append("## Run Metrics")
    sections.append(
        f"- Tokens: {package.usage_metrics.total_tokens} "
        f"(prompt {package.usage_metrics.prompt_tokens}, completion {package.usage_metrics.completion_tokens})"
    )
    sections.append(f"- Latency: {package.usage_metrics.latency_ms} ms")
    sections.append(f"- Estimated Cost (USD): {package.usage_metrics.estimated_cost_usd}")
    sections.append("## Assumptions")
    sections.extend(f"- {item}" for item in design.assumptions)
    sections.append("## Functional Requirements")
    sections.extend(f"- {item}" for item in design.functional_requirements)
    sections.append("## Non-Functional Requirements")
    sections.extend(f"- {item}" for item in design.non_functional_requirements)
    sections.append("## API Contracts")
    sections.extend(f"- {item}" for item in design.api_contracts)
    sections.append("## Data Model Entities")
    sections.extend(f"- {item}" for item in design.data_model_entities)
    sections.append("## Sequence of Operations")
    sections.extend(f"- {item}" for item in design.sequence_of_operations)
    sections.append("## High-Level Architecture")
    sections.append(design.high_level_architecture)
    sections.append("## Components")
    for component in design.components:
        sections.append(f"- **{component.name}** ({component.type}): {component.description}")
        if component.connections:
            sections.append(f"  - Connections: {', '.join(component.connections)}")
    sections.append("## Database Design")
    sections.append(design.database_design)
    sections.append("## Consistency and Transactions")
    sections.append(design.consistency_and_transactions)
    sections.append("## Scaling Strategy")
    sections.append(design.scaling_strategy)
    sections.append("## Caching Strategy")
    sections.append(design.caching_strategy)
    sections.append("## Capacity Estimation")
    sections.append(design.capacity_estimation)
    sections.append("## Reliability and Resilience")
    sections.append(design.reliability_and_resilience)
    sections.append("## Security and Compliance")
    sections.append(design.security_and_compliance)
    sections.append("## Observability and SLOs")
    sections.append(design.observability_and_slos)
    sections.append("## Deployment and Release Strategy")
    sections.append(design.deployment_and_release_strategy)
    sections.append("## Disaster Recovery")
    sections.append(design.disaster_recovery)
    sections.append("## Cost Estimation")
    sections.append(design.cost_estimation)
    sections.append("## Testing Strategy")
    sections.append(design.testing_strategy)
    sections.append("## Operational Runbook")
    sections.extend(f"- {item}" for item in design.operational_runbook)
    sections.append("## Bottlenecks")
    sections.extend(f"- {item}" for item in design.bottlenecks)
    sections.append("## Tradeoffs")
    sections.extend(f"- {item}" for item in design.tradeoffs)
    sections.append("## Mermaid Diagram")
    sections.append("```mermaid")
    sections.append(diagram)
    sections.append("```")

    return "\n".join(sections)


def main() -> None:
    init_state()

    st.title(PAGE_TITLE)
    st.write("AI-native assistant that turns real project implementation tasks into production-ready system architecture.")

    with st.form("question_form"):
        question_input = st.text_area("Project implementation task", value=st.session_state["question"], height=150)
        submit_generate = st.form_submit_button("Generate architecture")

    if submit_generate:
        cleaned = question_input.strip()
        if not cleaned:
            st.error("Please describe a project implementation task before continuing.")
        else:
            st.session_state["question"] = cleaned
            st.session_state["design_response"] = None
            st.session_state["need_design"] = True
            st.session_state["error_message"] = ""

    if st.session_state["need_design"]:
        try:
            generator = DesignGenerator()
            with st.spinner("Generating system design..."):
                package = generator.generate_design_package_from_task(
                    st.session_state["question"]
                )
            st.session_state["design_response"] = package
            st.session_state["need_design"] = False
            st.session_state["error_message"] = ""
        except Exception as exc:
            st.session_state["error_message"] = str(exc)
            st.session_state["need_design"] = False

    if st.session_state["error_message"]:
        st.error(st.session_state["error_message"])

    if package := st.session_state.get("design_response"):
        design: DesignResponse = package.design
        container = st.container()
        container.header("Production-grade system design output")
        container.subheader("Design Quality Score")
        container.metric("Total Score", f"{package.quality_report.total_score}/100")
        for dimension in package.quality_report.dimensions:
            container.markdown(
                f"- **{dimension.name}**: {dimension.score}/10 - {dimension.rationale}"
            )
        if package.quality_report.missing_areas:
            _render_list("Missing Areas", package.quality_report.missing_areas)
        if package.quality_report.recommendations:
            _render_list(
                "Improvement Recommendations", package.quality_report.recommendations
            )

        if package.alternatives:
            container.subheader("Architecture Alternatives")
            for alt in package.alternatives:
                container.markdown(f"**{alt.name}** ({alt.focus})")
                container.write(alt.summary)
                if alt.strengths:
                    container.markdown(f"- Strengths: {', '.join(alt.strengths)}")
                if alt.risks:
                    container.markdown(f"- Risks: {', '.join(alt.risks)}")

        if package.decision_matrix:
            container.subheader("Decision Matrix")
            for row in package.decision_matrix:
                container.markdown(
                    f"- **{row.option}** | Latency {row.latency_score}/5 | Cost {row.cost_score}/5 | "
                    f"Complexity {row.complexity_score}/5 | Reliability {row.reliability_score}/5 | "
                    f"Delivery {row.delivery_speed_score}/5"
                )
                container.markdown(f"  - {row.notes}")
            if package.recommended_option:
                container.success(
                    f"Recommended Option: {package.recommended_option}"
                )

        container.subheader("Run Metrics")
        container.markdown(
            f"- Tokens: {package.usage_metrics.total_tokens} "
            f"(prompt {package.usage_metrics.prompt_tokens}, completion {package.usage_metrics.completion_tokens})"
        )
        container.markdown(f"- Latency: {package.usage_metrics.latency_ms} ms")
        container.markdown(
            f"- Estimated Cost (USD): {package.usage_metrics.estimated_cost_usd}"
        )
        _render_list("Assumptions", design.assumptions)
        _render_list("Functional Requirements", design.functional_requirements)
        _render_list("Non-Functional Requirements", design.non_functional_requirements)
        _render_list("API Contracts", design.api_contracts)
        _render_list("Data Model Entities", design.data_model_entities)
        _render_list("Sequence of Operations", design.sequence_of_operations)
        container.subheader("High-Level Architecture")
        container.write(design.high_level_architecture)
        container.subheader("Components")
        for component in design.components:
            container.markdown(
                f"- **{component.name} ({component.type})**: {component.description}"
            )
            if component.connections:
                container.markdown(f"  - Connections: {', '.join(component.connections)}")
        container.subheader("Database Design")
        container.write(design.database_design)
        container.subheader("Consistency and Transactions")
        container.write(design.consistency_and_transactions)
        container.subheader("Scaling Strategy")
        container.write(design.scaling_strategy)
        container.subheader("Caching Strategy")
        container.write(design.caching_strategy)
        container.subheader("Capacity Estimation")
        container.write(design.capacity_estimation)
        container.subheader("Reliability and Resilience")
        container.write(design.reliability_and_resilience)
        container.subheader("Security and Compliance")
        container.write(design.security_and_compliance)
        container.subheader("Observability and SLOs")
        container.write(design.observability_and_slos)
        container.subheader("Deployment and Release Strategy")
        container.write(design.deployment_and_release_strategy)
        container.subheader("Disaster Recovery")
        container.write(design.disaster_recovery)
        container.subheader("Cost Estimation")
        container.write(design.cost_estimation)
        container.subheader("Testing Strategy")
        container.write(design.testing_strategy)
        _render_list("Operational Runbook", design.operational_runbook)
        _render_list("Bottlenecks", design.bottlenecks)
        _render_list("Tradeoffs", design.tradeoffs)

        diagram = package.mermaid_diagram or build_diagram(design)
        container.subheader("Mermaid Architecture Diagram")
        container.markdown(f"```mermaid\n{diagram}\n```")

        markdown_payload = _build_export_markdown(
            st.session_state["question"],
            package,
            diagram,
        )
        container.download_button(
            label="Export to Markdown",
            data=markdown_payload,
            file_name="systemdesign-gpt-output.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
