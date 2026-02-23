from __future__ import annotations

from textwrap import dedent
from typing import Sequence


CLARIFICATION_PROMPT = dedent(
    """
    You are SystemDesign-GPT, an AI system design interviewer assistant.
    The candidate already posed the design question below.
    Ask exactly three clarifying questions that will help you scope a production-ready system design.
    Return only a JSON object with a single key `questions` mapping to a list of three concise, high-value clarifying questions.
    Return strict RFC8259 JSON: use double quotes only and no trailing commas.
    Do not add explanations, markdown, or extra text.

    Design question: {question}
    """
).strip()

DESIGN_SCHEMA = dedent(
    """
    {
      "assumptions": [string],
      "functional_requirements": [string],
      "non_functional_requirements": [string],
      "high_level_architecture": string,
      "components": [
        {
          "name": string,
          "type": string,
          "description": string,
          "connections": [string]
        }
      ],
      "database_design": string,
      "scaling_strategy": string,
      "caching_strategy": string,
      "capacity_estimation": string,
      "bottlenecks": [string],
      "tradeoffs": [string],
      "mermaid_diagram": string
    }
    """
).strip()


DESIGN_PROMPT = dedent(
    """
    You are SystemDesign-GPT. The interview question is '{question}'.
    You already collected answers to clarifying questions. Use that context to craft a complete system design.
    Structure your response strictly as valid JSON matching this schema:
    {schema}

    Clarifying questions and answers:
    {clarifications}

    Return strict RFC8259 JSON only: use double quotes, no trailing commas, and escape newlines inside strings.
    Do not include markdown, explanations, or comments.
    Use concise bullet-like sentences for list entries.
    If required information is missing, state it explicitly under `assumptions` instead of inventing facts.
    Do not introduce technologies that are not justified by the requirements or clarifications.
    Ensure the Mermaid diagram in `mermaid_diagram` is valid flowchart syntax describing component interplay.
    """
).strip()


def _normalize_question(question: str) -> str:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must be a non-empty string")
    return normalized_question


def _normalize_clarifications(clarifications: Sequence[str]) -> list[str]:
    normalized = [item.strip() for item in clarifications if item.strip()]
    if not normalized:
        raise ValueError("clarifications must contain at least one non-empty entry")
    return normalized


def build_clarification_prompt(question: str) -> str:
    """Build the prompt used to request three clarifying questions."""
    return CLARIFICATION_PROMPT.format(question=_normalize_question(question))


def build_design_prompt(question: str, clarifications: Sequence[str]) -> str:
    """Build the prompt used to generate the final system design JSON."""
    normalized_question = _normalize_question(question)
    normalized_clarifications = _normalize_clarifications(clarifications)
    answers = "\n\n".join(normalized_clarifications)
    return DESIGN_PROMPT.format(
        question=normalized_question,
        schema=DESIGN_SCHEMA,
        clarifications=answers,
    )
