from __future__ import annotations

from typing import List


CLARIFICATION_PROMPT = (
    "You are SystemDesign-GPT, an AI system design interviewer assistant. "
    "The candidate already posed the design question below. "
    "Ask exactly three clarifying questions that will help you scope a production-ready system design. "
    "Return only a JSON object with a single key `questions` mapping to a list of three concise, high-value clarifying questions. "
    "Do not add any explanations, extra text, or trailing commas."
    "\n\nDesign question: {question}"
)


DESIGN_PROMPT = (
    "You are SystemDesign-GPT. The interview question is '{question}'. "
    "You already collected answers to clarifying questions. Use that context to craft a complete system design. "
    "Structure your response strictly as valid JSON matching this schema:\n"
    "{{\n"
    "  \"assumptions\": [string],\n"
    "  \"functional_requirements\": [string],\n"
    "  \"non_functional_requirements\": [string],\n"
    "  \"high_level_architecture\": string,\n"
    "  \"components\": [\n"
    "    {{\n"
    "      \"name\": string,\n"
    "      \"type\": string,\n"
    "      \"description\": string,\n"
    "      \"connections\": [string]\n"
    "    }}\n"
    "  ],\n"
    "  \"database_design\": string,\n"
    "  \"scaling_strategy\": string,\n"
    "  \"caching_strategy\": string,\n"
    "  \"capacity_estimation\": string,\n"
    "  \"bottlenecks\": [string],\n"
    "  \"tradeoffs\": [string],\n"
    "  \"mermaid_diagram\": string\n"
    "}}"
    "\n\nClarifying questions and answers:\n"
    "{clarifications}\n\n"
    "Output the JSON without markdown, explanations, or comments. Use concise bullet-like sentences for list entries. Ensure the Mermaid diagram in `mermaid_diagram` is valid flowchart syntax describing the component interplay."
)


def build_clarification_prompt(question: str) -> str:
    return CLARIFICATION_PROMPT.format(question=question)


def build_design_prompt(question: str, clarifications: List[str]) -> str:
    answers = "\n\n".join(clarification for clarification in clarifications)
    return DESIGN_PROMPT.format(question=question, clarifications=answers)
