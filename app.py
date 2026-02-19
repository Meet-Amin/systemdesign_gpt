from __future__ import annotations

from typing import Iterable, List

import streamlit as st

from core.diagram import build_diagram
from core.generator import DesignGenerator
from core.schemas import DesignResponse


PAGE_TITLE = "SystemDesign-GPT"
DEFAULT_QUESTION = "Design YouTube"


st.set_page_config(page_title=PAGE_TITLE, layout="wide")


def init_state() -> None:
    defaults = {
        "question": DEFAULT_QUESTION,
        "clarification_questions": [],
        "clarification_answers": [],
        "design_response": None,
        "error_message": "",
        "need_clarifications": False,
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


def _build_clarification_context(questions: List[str], answers: List[str]) -> List[str]:
    context: List[str] = []
    for idx, (question, answer) in enumerate(zip(questions, answers), start=1):
        context.append(f"Q{idx}: {question}\nA{idx}: {answer}")
    return context


def _build_export_markdown(question: str, clarifications: List[str], answers: List[str], design: DesignResponse, diagram: str) -> str:
    sections: List[str] = []
    sections.append("# SystemDesign-GPT Output")
    sections.append("## Interview Question")
    sections.append(question)
    sections.append("## Clarifications")
    for q, answer in zip(clarifications, answers):
        sections.append(f"- **Q:** {q}")
        sections.append(f"  - **A:** {answer}")
    sections.append("## Assumptions")
    sections.extend(f"- {item}" for item in design.assumptions)
    sections.append("## Functional Requirements")
    sections.extend(f"- {item}" for item in design.functional_requirements)
    sections.append("## Non-Functional Requirements")
    sections.extend(f"- {item}" for item in design.non_functional_requirements)
    sections.append("## High-Level Architecture")
    sections.append(design.high_level_architecture)
    sections.append("## Components")
    for component in design.components:
        sections.append(f"- **{component.name}** ({component.type}): {component.description}")
        if component.connections:
            sections.append(f"  - Connections: {', '.join(component.connections)}")
    sections.append("## Database Design")
    sections.append(design.database_design)
    sections.append("## Scaling Strategy")
    sections.append(design.scaling_strategy)
    sections.append("## Caching Strategy")
    sections.append(design.caching_strategy)
    sections.append("## Capacity Estimation")
    sections.append(design.capacity_estimation)
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
    st.write("AI-native assistant that guides the system design interview workflow from clarifications through production-ready architecture.")

    with st.form("question_form"):
        question_input = st.text_area("System design question", value=st.session_state["question"], height=150)
        submit_question = st.form_submit_button("Ask clarifying questions")

    if submit_question:
        cleaned = question_input.strip()
        if not cleaned:
            st.error("Please describe a system design problem before continuing.")
        else:
            st.session_state["question"] = cleaned
            st.session_state["clarification_questions"] = []
            st.session_state["clarification_answers"] = []
            st.session_state["design_response"] = None
            st.session_state["need_clarifications"] = True
            st.session_state["need_design"] = False
            st.session_state["error_message"] = ""

    if st.session_state["need_clarifications"]:
        try:
            generator = DesignGenerator()
            with st.spinner("Generating clarifying questions..."):
                clarification = generator.generate_clarifying_questions(st.session_state["question"])
            st.session_state["clarification_questions"] = clarification.questions
            st.session_state["clarification_answers"] = ["" for _ in clarification.questions]
            st.session_state["need_clarifications"] = False
        except Exception as exc:
            st.session_state["error_message"] = str(exc)
            st.session_state["need_clarifications"] = False

    question_section = st.expander("Clarifying questions", expanded=True)
    with question_section:
        if st.session_state["clarification_questions"]:
            clar_form = st.form("clarification_answers_form")
            with clar_form:
                answers: List[str] = []
                for idx, question in enumerate(st.session_state["clarification_questions"]):
                    key = f"clar_answer_{idx}"
                    default_value = st.session_state["clarification_answers"][idx]
                    answer = st.text_area(f"Q{idx + 1}: {question}", value=default_value, key=key, height=75)
                    answers.append(answer.strip())
                submit_answers = st.form_submit_button("Submit answers and generate design")
            if submit_answers:
                st.session_state["clarification_answers"] = answers
                try:
                    generator = DesignGenerator()
                    clarification_context = _build_clarification_context(
                        st.session_state["clarification_questions"],
                        st.session_state["clarification_answers"],
                    )
                    with st.spinner("Generating system design..."):
                        design = generator.generate_design(
                            st.session_state["question"],
                            clarification_context,
                        )
                    st.session_state["design_response"] = design
                    st.session_state["need_design"] = False
                    st.session_state["error_message"] = ""
                except Exception as exc:
                    st.session_state["error_message"] = str(exc)
        else:
            st.write("Clarifying questions will appear here once the system processes your prompt.")

    if st.session_state["error_message"]:
        st.error(st.session_state["error_message"])

    if design := st.session_state.get("design_response"):
        container = st.container()
        container.header("System design output")
        _render_list("Assumptions", design.assumptions)
        _render_list("Functional Requirements", design.functional_requirements)
        _render_list("Non-Functional Requirements", design.non_functional_requirements)
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
        container.subheader("Scaling Strategy")
        container.write(design.scaling_strategy)
        container.subheader("Caching Strategy")
        container.write(design.caching_strategy)
        container.subheader("Capacity Estimation")
        container.write(design.capacity_estimation)
        _render_list("Bottlenecks", design.bottlenecks)
        _render_list("Tradeoffs", design.tradeoffs)

        diagram = build_diagram(design)
        container.subheader("Mermaid Architecture Diagram")
        container.markdown(f"```mermaid\n{diagram}\n```")

        markdown_payload = _build_export_markdown(
            st.session_state["question"],
            st.session_state["clarification_questions"],
            st.session_state["clarification_answers"],
            design,
            diagram,
        )
        container.download_button(
            label="Export to Markdown",
            data=markdown_payload,
            file_name="systemdesign-gpt-output.md",
            mime="text/markdown",
        )

        if st.session_state["clarification_questions"]:
            container.caption("Use the export to share or archive the final design with your candidates or team.")


if __name__ == "__main__":
    main()
