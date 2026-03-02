from __future__ import annotations

import base64
import html
from typing import Iterable, List

import streamlit as st
import streamlit.components.v1 as components

from core.diagram import build_diagram
from core.exporters import to_confluence_wiki, to_github_pr_comment, to_pdf_bytes
from core.features import diff_design_packages, estimate_cost
from core.generator import DesignGenerator
from core.history import (
    add_reviewer_comment,
    create_history_entry,
    list_history_entries,
    set_review_status,
)
from core.schemas import (
    CostModelInput,
    DesignPackage,
    DesignResponse,
    ImplementationPromptPack,
)

PAGE_TITLE = "SystemDesign-GPT"
DEFAULT_QUESTION = (
    "Implement real-time notifications for a project management SaaS app."
)


st.set_page_config(page_title=PAGE_TITLE, layout="wide")


def init_state() -> None:
    defaults = {
        "question": DEFAULT_QUESTION,
        "diff_question": "",
        "design_response": None,
        "implementation_prompt_pack": None,
        "followup_response": None,
        "threat_model": None,
        "test_plan": None,
        "cost_estimate": None,
        "design_diff": None,
        "history_entries": [],
        "open_prompt_pack_in_new_tab": False,
        "error_message": "",
        "need_design": False,
        "need_prompt_pack": False,
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


def _build_export_markdown(
    question: str,
    package: DesignPackage,
    diagram: str,
    prompt_pack: ImplementationPromptPack | None = None,
) -> str:
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
        sections.extend(f"- {item}" for item in package.quality_report.recommendations)
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
                f"- **{row.option}** | Latency {row.latency_score}/5 | "
                f"Cost {row.cost_score}/5 | "
                f"Complexity {row.complexity_score}/5 | "
                f"Reliability {row.reliability_score}/5 | "
                f"Delivery {row.delivery_speed_score}/5"
            )
            sections.append(f"  - Notes: {row.notes}")
        if package.recommended_option:
            sections.append(f"- Recommended Option: **{package.recommended_option}**")
    sections.append("## Run Metrics")
    sections.append(
        f"- Tokens: {package.usage_metrics.total_tokens} (prompt "
        f"{package.usage_metrics.prompt_tokens}, completion "
        f"{package.usage_metrics.completion_tokens})"
    )
    sections.append(f"- Latency: {package.usage_metrics.latency_ms} ms")
    sections.append(
        f"- Estimated Cost (USD): {package.usage_metrics.estimated_cost_usd}"
    )
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
        sections.append(
            f"- **{component.name}** ({component.type}): {component.description}"
        )
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
    if prompt_pack and prompt_pack.prompts:
        sections.append("## Best AI Tools For These Prompts")
        sections.extend(f"- {tool}" for tool in prompt_pack.recommended_tools_overview)
        sections.append("## Vibe Coding Prompts")
        for idx, prompt in enumerate(prompt_pack.prompts, start=1):
            sections.append(f"### Prompt {idx}: {prompt.title}")
            sections.append(f"- Objective: {prompt.objective}")
            if prompt.recommended_tools:
                sections.append(
                    f"- Best used in: {', '.join(prompt.recommended_tools)}"
                )
            sections.append(prompt.prompt)
        sections.append("## Prompt Pack Metrics")
        sections.append(
            f"- Tokens: {prompt_pack.usage_metrics.total_tokens} (prompt "
            f"{prompt_pack.usage_metrics.prompt_tokens}, completion "
            f"{prompt_pack.usage_metrics.completion_tokens})"
        )
        sections.append(f"- Latency: {prompt_pack.usage_metrics.latency_ms} ms")
        sections.append(
            f"- Estimated Cost (USD): {prompt_pack.usage_metrics.estimated_cost_usd}"
        )

    return "\n".join(sections)


def _build_prompt_pack_html(prompt_pack: ImplementationPromptPack) -> str:
    body: List[str] = []
    body.append("<h1>Vibe Coding Prompts</h1>")
    if prompt_pack.recommended_tools_overview:
        body.append("<h2>Best AI Tools</h2><ul>")
        for tool in prompt_pack.recommended_tools_overview:
            body.append(f"<li>{html.escape(tool)}</li>")
        body.append("</ul>")
    for idx, prompt in enumerate(prompt_pack.prompts, start=1):
        body.append(f"<h2>{idx}. {html.escape(prompt.title)}</h2>")
        body.append(
            f"<p><strong>Objective:</strong> {html.escape(prompt.objective)}</p>"
        )
        if prompt.recommended_tools:
            tools = ", ".join(html.escape(tool) for tool in prompt.recommended_tools)
            body.append(f"<p><strong>Best used in:</strong> {tools}</p>")
        body.append(f"<pre>{html.escape(prompt.prompt)}</pre>")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Vibe Coding Prompts</title>"
        "<style>"
        "body { font-family: Arial, sans-serif; max-width: 980px; margin: 24px auto; "
        "padding: 0 16px; line-height: 1.5 }"
        "pre { white-space: pre-wrap; background: #f6f8fa; "
        "border: 1px solid #d0d7de; padding: 12px; border-radius: 8px }"
        "</style>"
        "</head><body>" + "".join(body) + "</body></html>"
    )


def _open_html_in_new_tab(html_payload: str) -> None:
    encoded = base64.b64encode(html_payload.encode("utf-8")).decode("utf-8")
    components.html(
        (f"<script>window.open('data:text/html;base64,{encoded}', '_blank');</script>"),
        height=0,
    )


def main() -> None:
    init_state()

    st.title(PAGE_TITLE)
    st.write(
        "AI-native assistant that turns real project implementation tasks into "
        "production-ready system architecture."
    )

    with st.form("question_form"):
        question_input = st.text_area(
            "Project implementation task",
            value=st.session_state["question"],
            height=150,
        )
        submit_generate = st.form_submit_button("Generate architecture")

    if submit_generate:
        cleaned = question_input.strip()
        if not cleaned:
            st.error("Please describe a project implementation task before continuing.")
        else:
            st.session_state["question"] = cleaned
            st.session_state["design_response"] = None
            st.session_state["implementation_prompt_pack"] = None
            st.session_state["need_design"] = True
            st.session_state["need_prompt_pack"] = False
            st.session_state["error_message"] = ""

    if st.session_state["need_design"]:
        try:
            generator = DesignGenerator()
            with st.spinner("Generating system design..."):
                package = generator.generate_design_package_from_task(
                    st.session_state["question"]
                )
            st.session_state["design_response"] = package
            create_history_entry(st.session_state["question"], package, tags=[])
            st.session_state["history_entries"] = list_history_entries()
            st.session_state["need_design"] = False
            st.session_state["error_message"] = ""
        except Exception as exc:
            st.session_state["error_message"] = str(exc)
            st.session_state["need_design"] = False

    if (
        st.session_state["need_prompt_pack"]
        and st.session_state.get("design_response") is not None
    ):
        try:
            generator = DesignGenerator()
            with st.spinner("Generating vibe coding prompts..."):
                pack = generator.generate_implementation_prompt_pack(
                    st.session_state["question"],
                    st.session_state["design_response"],
                )
            st.session_state["implementation_prompt_pack"] = pack
            st.session_state["need_prompt_pack"] = False
            st.session_state["open_prompt_pack_in_new_tab"] = True
        except Exception as exc:
            st.session_state["error_message"] = str(exc)
            st.session_state["need_prompt_pack"] = False

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
                    f"- **{row.option}** | Latency {row.latency_score}/5 | "
                    f"Cost {row.cost_score}/5 | "
                    f"Complexity {row.complexity_score}/5 | "
                    f"Reliability {row.reliability_score}/5 | "
                    f"Delivery {row.delivery_speed_score}/5"
                )
                container.markdown(f"  - {row.notes}")
            if package.recommended_option:
                container.success(f"Recommended Option: {package.recommended_option}")

        container.subheader("Run Metrics")
        container.markdown(
            f"- Tokens: {package.usage_metrics.total_tokens} (prompt "
            f"{package.usage_metrics.prompt_tokens}, completion "
            f"{package.usage_metrics.completion_tokens})"
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
                container.markdown(
                    f"  - Connections: {', '.join(component.connections)}"
                )
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

        if container.button(
            "Generate Vibe Coding Prompts",
            key="generate_vibe_prompts",
        ):
            st.session_state["need_prompt_pack"] = True
            st.session_state["error_message"] = ""
            st.rerun()

        prompt_pack = st.session_state.get("implementation_prompt_pack")
        if st.session_state.get("open_prompt_pack_in_new_tab") and prompt_pack:
            _open_html_in_new_tab(_build_prompt_pack_html(prompt_pack))
            st.session_state["open_prompt_pack_in_new_tab"] = False
        if prompt_pack and prompt_pack.prompts:
            container.subheader("Best AI Tools For Prompt Execution")
            container.markdown(
                "- " + "\n- ".join(prompt_pack.recommended_tools_overview)
            )
            container.subheader("Vibe Coding Prompts")
            for idx, prompt in enumerate(prompt_pack.prompts, start=1):
                container.markdown(f"**{idx}. {prompt.title}**")
                container.markdown(f"- Objective: {prompt.objective}")
                if prompt.recommended_tools:
                    container.markdown(
                        f"- Best used in: {', '.join(prompt.recommended_tools)}"
                    )
                container.text_area(
                    f"Prompt {idx}",
                    value=prompt.prompt,
                    height=220,
                    key=f"vibe_prompt_{idx}",
                )
            container.subheader("Prompt Pack Metrics")
            container.markdown(
                f"- Tokens: {prompt_pack.usage_metrics.total_tokens} (prompt "
                f"{prompt_pack.usage_metrics.prompt_tokens}, completion "
                f"{prompt_pack.usage_metrics.completion_tokens})"
            )
            container.markdown(f"- Latency: {prompt_pack.usage_metrics.latency_ms} ms")
            container.markdown(
                "- Estimated Cost (USD): "
                f"{prompt_pack.usage_metrics.estimated_cost_usd}"
            )

        container.subheader("Follow-up Q&A")
        followup_input = container.text_input(
            "Ask follow-up question",
            key="followup_input",
            placeholder="Example: How do we optimize this architecture for lower cost?",
        )
        if container.button("Run Follow-up Analysis", key="followup_btn"):
            if followup_input.strip():
                try:
                    generator = DesignGenerator()
                    followup_response = generator.generate_follow_up_response(
                        st.session_state["question"], package, followup_input.strip()
                    )
                    st.session_state["followup_response"] = followup_response
                except Exception as exc:
                    st.session_state["error_message"] = str(exc)
            else:
                st.session_state["error_message"] = "Follow-up question cannot be empty."
        if st.session_state.get("followup_response"):
            followup_response = st.session_state["followup_response"]
            container.markdown(f"**Answer:** {followup_response.answer}")
            if followup_response.impacted_sections:
                container.markdown(
                    "- Impacted sections: "
                    + ", ".join(followup_response.impacted_sections)
                )
            if followup_response.revised_plan:
                container.markdown("**Revised plan**")
                for step in followup_response.revised_plan:
                    container.markdown(f"- {step}")

        container.subheader("Architecture Diff")
        diff_task = container.text_area(
            "Second task for comparison",
            value=st.session_state.get("diff_question", ""),
            height=100,
        )
        if container.button("Compare Tasks", key="diff_btn"):
            clean_diff_task = diff_task.strip()
            if clean_diff_task:
                try:
                    generator = DesignGenerator()
                    with st.spinner("Generating comparison design..."):
                        other_package = generator.generate_design_package_from_task(
                            clean_diff_task
                        )
                    st.session_state["diff_question"] = clean_diff_task
                    st.session_state["design_diff"] = diff_design_packages(
                        st.session_state["question"], package, clean_diff_task, other_package
                    )
                except Exception as exc:
                    st.session_state["error_message"] = str(exc)
        if st.session_state.get("design_diff"):
            design_diff = st.session_state["design_diff"]
            container.markdown(f"**Diff summary:** {design_diff.summary}")
            _render_list("Added Components", design_diff.added_components)
            _render_list("Removed Components", design_diff.removed_components)
            _render_list("Added Requirements", design_diff.added_requirements)
            _render_list("Removed Requirements", design_diff.removed_requirements)
            _render_list("Risk Changes", design_diff.risk_changes)

        container.subheader("Team Review Workflow")
        history_entries = list_history_entries()
        st.session_state["history_entries"] = history_entries
        if history_entries:
            selected = container.selectbox(
                "Pick version to review",
                options=[entry.version_id for entry in history_entries],
                key="history_select",
            )
            status_col, comment_col = container.columns(2)
            status = status_col.selectbox(
                "Set status",
                options=["draft", "approved", "needs_changes"],
                key="status_select",
            )
            if status_col.button("Update Status", key="status_update"):
                set_review_status(selected, status)
                st.session_state["history_entries"] = list_history_entries()
            comment = comment_col.text_input("Add review comment", key="review_comment")
            if comment_col.button("Add Comment", key="comment_add"):
                add_reviewer_comment(selected, comment)
                st.session_state["history_entries"] = list_history_entries()
            chosen = next((e for e in st.session_state["history_entries"] if e.version_id == selected), None)
            if chosen:
                container.markdown(f"**Current status:** {chosen.status}")
                _render_list("Reviewer Comments", chosen.reviewer_comments)

        container.subheader("Cost Model Calculator")
        c1, c2, c3, c4 = container.columns(4)
        model_input = CostModelInput(
            monthly_active_users=c1.number_input("MAU", min_value=1, value=10000),
            peak_qps=c2.number_input("Peak QPS", min_value=1, value=100),
            storage_gb=c3.number_input("Storage GB", min_value=1, value=200),
            retention_days=c4.number_input("Retention days", min_value=1, value=30),
        )
        if container.button("Estimate Cost", key="cost_btn"):
            st.session_state["cost_estimate"] = estimate_cost(package, model_input)
        if st.session_state.get("cost_estimate"):
            estimate = st.session_state["cost_estimate"]
            container.metric("Estimated Monthly Cost", f"${estimate.total_monthly_cost_usd}")
            for item in estimate.items:
                container.markdown(
                    f"- **{item.category}**: ${item.monthly_cost_usd} ({item.rationale})"
                )

        container.subheader("Threat Model")
        if container.button("Generate Threat Model", key="threat_btn"):
            try:
                generator = DesignGenerator()
                st.session_state["threat_model"] = generator.generate_threat_model(
                    st.session_state["question"], package
                )
            except Exception as exc:
                st.session_state["error_message"] = str(exc)
        if st.session_state.get("threat_model"):
            threat_model = st.session_state["threat_model"]
            container.markdown(f"**Methodology:** {threat_model.methodology}")
            for item in threat_model.threats:
                container.markdown(
                    f"- **{item.category}** | Threat: {item.threat} | "
                    f"Impact: {item.impact} | Mitigation: {item.mitigation}"
                )
            _render_list("Residual Risks", threat_model.residual_risks)

        container.subheader("Test Plan")
        if container.button("Generate Test Plan", key="test_plan_btn"):
            try:
                generator = DesignGenerator()
                st.session_state["test_plan"] = generator.generate_test_plan(
                    st.session_state["question"], package
                )
            except Exception as exc:
                st.session_state["error_message"] = str(exc)
        if st.session_state.get("test_plan"):
            test_plan = st.session_state["test_plan"]
            for case in test_plan.cases:
                container.markdown(f"**{case.name}** ({case.level})")
                container.markdown(f"- Objective: {case.objective}")
                for step in case.steps:
                    container.markdown(f"- Step: {step}")
                container.markdown(f"- Success criteria: {case.success_criteria}")
            _render_list("CI Gates", test_plan.ci_gates)

        container.subheader("Export Pack")
        confluence_payload = to_confluence_wiki(
            st.session_state["question"], package, prompt_pack
        )
        github_comment_payload = to_github_pr_comment(st.session_state["question"], package)
        container.download_button(
            label="Export Confluence (wiki markup)",
            data=confluence_payload,
            file_name="systemdesign-gpt-confluence.txt",
            mime="text/plain",
        )
        container.download_button(
            label="Export GitHub PR Comment",
            data=github_comment_payload,
            file_name="systemdesign-gpt-pr-comment.md",
            mime="text/markdown",
        )
        pdf_payload = to_pdf_bytes(st.session_state["question"], package)
        if pdf_payload:
            container.download_button(
                label="Export PDF",
                data=pdf_payload,
                file_name="systemdesign-gpt-output.pdf",
                mime="application/pdf",
            )
        else:
            container.caption("PDF export needs `reportlab` installed.")

        markdown_payload = _build_export_markdown(
            st.session_state["question"],
            package,
            diagram,
            prompt_pack,
        )
        container.download_button(
            label="Export to Markdown",
            data=markdown_payload,
            file_name="systemdesign-gpt-output.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
