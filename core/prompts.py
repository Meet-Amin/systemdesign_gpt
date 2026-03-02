from __future__ import annotations

from textwrap import dedent
from typing import Sequence

CLARIFICATION_PROMPT = dedent(
    """
    You are SystemDesign-GPT, an AI architecture assistant.
    The user already posed a real project implementation task below.
    Ask exactly three clarifying questions that will help you scope a
    production-ready system design.
    Return only a JSON object with a single key `questions` mapping to a list
    of three concise, high-value clarifying questions.
    Return strict RFC8259 JSON: use double quotes only and no trailing commas.
    Do not add explanations, markdown, or extra text.

    Design problem: {question}
    """
).strip()

DESIGN_SCHEMA = dedent(
    """
    {
      "assumptions": [string],
      "functional_requirements": [string],
      "non_functional_requirements": [string],
      "api_contracts": [string],
      "data_model_entities": [string],
      "sequence_of_operations": [string],
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
      "consistency_and_transactions": string,
      "scaling_strategy": string,
      "caching_strategy": string,
      "capacity_estimation": string,
      "reliability_and_resilience": string,
      "security_and_compliance": string,
      "observability_and_slos": string,
      "deployment_and_release_strategy": string,
      "disaster_recovery": string,
      "cost_estimation": string,
      "testing_strategy": string,
      "operational_runbook": [string],
      "bottlenecks": [string],
      "tradeoffs": [string],
      "mermaid_diagram": string
    }
    """
).strip()


DESIGN_PROMPT = dedent(
    """
    You are SystemDesign-GPT. The design problem is '{question}'.
    The problem is a real project implementation task.
    You already collected answers to clarifying questions. Use that context to
    craft a complete system design.
    Structure your response strictly as valid JSON matching this schema:
    {schema}

    Clarifying questions and answers:
    {clarifications}

    Return strict RFC8259 JSON only: use double quotes, no trailing commas, and
    escape newlines inside strings.
    Do not include markdown, explanations, or comments.
    Use concrete, implementation-ready detail that engineering teams can
    execute.
    Include realistic protocols, storage/indexing choices, failure handling,
    and operational concerns.
    Use concise bullet-like sentences for list entries, but provide enough
    depth for real production usage.
    If required information is missing, state it explicitly under `assumptions`
    instead of inventing facts.
    Do not introduce technologies that are not justified by the requirements or
    clarifications.
    Provide concrete SLO targets and alerting examples in
    `observability_and_slos`.
    Include rollout/rollback strategy and migration considerations in
    `deployment_and_release_strategy`.
    Ensure the Mermaid diagram in `mermaid_diagram` is valid flowchart syntax
    describing component interplay.
    """
).strip()

IMPLEMENTATION_PROMPT_SCHEMA = dedent(
    """
    {
      "generated_for_task": string,
      "recommended_tools_overview": [string],
      "prompts": [
        {
          "title": string,
          "objective": string,
          "recommended_tools": [string],
          "prompt": string
        }
      ]
    }
    """
).strip()

IMPLEMENTATION_PROMPTS_PROMPT = dedent(
    """
    You are SystemDesign-GPT. Convert the architecture context below into
    high-quality implementation prompts for AI coding tools.
    These prompts will be copy-pasted into vibe-coding assistants to implement
    this feature in a real project.

    Task:
    {task}

    Architecture summary (JSON):
    {design_json}

    Return strict RFC8259 JSON matching this schema:
    {schema}

    Requirements:
    - Return 8 to 12 prompts.
    - Fill `recommended_tools_overview` with 4-6 best AI coding tools for
      these prompts (e.g., Cursor, Windsurf, GitHub Copilot Chat, ChatGPT,
      Claude).
    - Make prompts execution-oriented and repository-aware (ask assistant to
      inspect current codebase before changes).
    - Cover full lifecycle: planning, backend/API, database migration,
      frontend integration (if applicable), auth/security, testing,
      observability, deployment/rollback.
    - For each prompt, include `recommended_tools` with 1-3 tools from the
      overview that best fit that prompt.
    - Each `prompt` should include:
      1) expected files to inspect or create,
      2) implementation steps,
      3) validation commands/tests,
      4) done criteria.
    - Keep each prompt concise but actionable.
    - Do not include markdown fences.
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


def build_implementation_prompts_prompt(task: str, design_json: str) -> str:
    normalized_task = _normalize_question(task)
    normalized_design = design_json.strip()
    if not normalized_design:
        raise ValueError("design_json must be a non-empty string")
    return IMPLEMENTATION_PROMPTS_PROMPT.format(
        task=normalized_task,
        design_json=normalized_design,
        schema=IMPLEMENTATION_PROMPT_SCHEMA,
    )
