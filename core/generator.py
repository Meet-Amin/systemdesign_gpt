from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any, List

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from .diagram import build_diagram
from .prompts import (
    build_clarification_prompt,
    build_design_prompt,
    build_follow_up_prompt,
    build_implementation_prompts_prompt,
    build_test_plan_prompt,
    build_threat_model_prompt,
)
from .quality import evaluate_design_quality
from .schemas import (
    ArchitectureAlternative,
    ClarificationResponse,
    DecisionMatrixRow,
    DesignPackage,
    DesignResponse,
    FollowUpResponse,
    ImplementationPromptPack,
    TestPlan,
    ThreatModel,
    UsageMetrics,
)

MODEL = "gpt-4o-mini"

# Prefer project-local .env values over any stale shell-exported variables.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)


class DesignGenerator:
    def __init__(self, model: str = MODEL):
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if api_key.startswith('"') and api_key.endswith('"'):
            api_key = api_key[1:-1].strip()
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to a .env file or export it "
                "in your shell."
            )
        if "your-openai-api-key" in api_key.lower() or "your ope" in api_key.lower():
            raise EnvironmentError(
                "OPENAI_API_KEY appears to be a placeholder value. Replace it with a "
                "real key from platform.openai.com."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call_completion(self, prompt: str) -> tuple[str, UsageMetrics]:
        # Single gateway for LLM calls so error handling stays consistent.
        try:
            started = perf_counter()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are SystemDesign-GPT, an opinionated but practical "
                            "system design interviewer. Provide structured answers "
                            "and never stray from JSON when asked."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            latency_ms = int((perf_counter() - started) * 1000)
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("OpenAI API returned an empty message.")
            usage = self._extract_usage_metrics(response, latency_ms)
            return content, usage
        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    @staticmethod
    def _extract_usage_metrics(response: Any, latency_ms: int) -> UsageMetrics:
        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
        # Approximate public pricing for gpt-4o-mini, per 1M tokens.
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        estimated = round(input_cost + output_cost, 6)
        return UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimated,
        )

    def _parse_json(self, payload: str) -> dict:
        # The OpenAI API guarantees valid JSON when `response_format` is used.
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to decode JSON from LLM response despite JSON mode: {exc}"
            ) from exc

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            lines = [str(item).strip() for item in value if str(item).strip()]
            return "\n".join(lines)
        return str(value).strip()

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [
                str(item).strip() for item in value if item is not None and str(item).strip()
            ]
        text = str(value).strip()
        return [text] if text else []

    def _normalize_design_payload(self, payload: dict) -> dict:
        scalar_fields = [
            "high_level_architecture",
            "database_design",
            "consistency_and_transactions",
            "scaling_strategy",
            "caching_strategy",
            "capacity_estimation",
            "reliability_and_resilience",
            "security_and_compliance",
            "observability_and_slos",
            "deployment_and_release_strategy",
            "disaster_recovery",
            "cost_estimation",
            "testing_strategy",
            "mermaid_diagram",
        ]
        list_fields = [
            "assumptions",
            "functional_requirements",
            "non_functional_requirements",
            "api_contracts",
            "data_model_entities",
            "sequence_of_operations",
            "operational_runbook",
            "bottlenecks",
            "tradeoffs",
        ]

        normalized = dict(payload)
        for field in scalar_fields:
            normalized[field] = self._coerce_text(normalized.get(field))
        for field in list_fields:
            normalized[field] = self._coerce_list(normalized.get(field))

        components = normalized.get("components")
        if not isinstance(components, list):
            normalized["components"] = []
        else:
            normalized_components = []
            for component in components:
                if not isinstance(component, dict):
                    continue
                normalized_components.append(
                    {
                        "name": self._coerce_text(component.get("name")),
                        "type": self._coerce_text(component.get("type")),
                        "description": self._coerce_text(component.get("description")),
                        "connections": self._coerce_list(component.get("connections")),
                    }
                )
            normalized["components"] = normalized_components

        return normalized

    def _normalize_prompt_pack_payload(self, payload: dict, task: str) -> dict:
        normalized = dict(payload)
        normalized["generated_for_task"] = (
            self._coerce_text(normalized.get("generated_for_task")) or task
        )
        overview = self._coerce_list(normalized.get("recommended_tools_overview"))
        if not overview:
            overview = [
                "Cursor",
                "Windsurf",
                "GitHub Copilot Chat",
                "ChatGPT",
                "Claude",
            ]
        normalized["recommended_tools_overview"] = overview
        prompts = normalized.get("prompts")
        normalized_prompts: List[dict] = []
        if isinstance(prompts, list):
            for entry in prompts:
                if not isinstance(entry, dict):
                    continue
                title = self._coerce_text(entry.get("title"))
                objective = self._coerce_text(entry.get("objective"))
                prompt_text = self._coerce_text(entry.get("prompt"))
                tools = self._coerce_list(entry.get("recommended_tools"))
                if not prompt_text:
                    continue
                normalized_prompts.append(
                    {
                        "title": title or "Implementation Step",
                        "objective": objective
                        or "Implement a scoped part of the task.",
                        "recommended_tools": tools[:3] if tools else overview[:2],
                        "prompt": prompt_text,
                    }
                )
        normalized["prompts"] = normalized_prompts
        return normalized

    def generate_clarifying_questions(self, question: str) -> ClarificationResponse:
        prompt = build_clarification_prompt(question)
        raw, _ = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return ClarificationResponse(**payload)

    def generate_design(
        self, question: str, clarifications: List[str]
    ) -> DesignResponse:
        prompt = build_design_prompt(question, clarifications)
        raw, _ = self._call_completion(prompt)
        payload = self._parse_json(raw)
        payload = self._normalize_design_payload(payload)
        return DesignResponse(**payload)

    def _generate_design_with_metrics(
        self, question: str, clarifications: List[str]
    ) -> tuple[DesignResponse, UsageMetrics]:
        prompt = build_design_prompt(question, clarifications)
        raw, usage = self._call_completion(prompt)
        payload = self._parse_json(raw)
        payload = self._normalize_design_payload(payload)
        return DesignResponse(**payload), usage

    def generate_design_from_task(self, task: str) -> DesignResponse:
        bootstrap_context = [
            (
                "No user-provided clarifications are available. "
                "Infer reasonable defaults, list explicit assumptions, "
                "and highlight missing information under assumptions."
            )
        ]
        return self.generate_design(task, bootstrap_context)

    def _build_alternatives(self, task: str) -> List[ArchitectureAlternative]:
        variants = [
            ("Low Latency", "Minimize P95/P99 latency for user-facing APIs."),
            ("Low Cost", "Minimize cloud spend while preserving core SLAs."),
            ("Fast Delivery", "Minimize implementation timeline and migration risk."),
        ]
        alternatives: List[ArchitectureAlternative] = []
        for name, focus in variants:
            variant_task = (
                f"{task}\n\nAlternative strategy objective: {focus} "
                "Constrain tradeoffs explicitly for this objective."
            )
            design = self.generate_design_from_task(variant_task)
            alternatives.append(
                ArchitectureAlternative(
                    name=name,
                    focus=focus,
                    summary=design.high_level_architecture,
                    strengths=design.functional_requirements[:3],
                    risks=design.tradeoffs[:3],
                )
            )
        return alternatives

    @staticmethod
    def _build_decision_matrix(
        alternatives: List[ArchitectureAlternative],
    ) -> tuple[List[DecisionMatrixRow], str]:
        score_map = {
            "Low Latency": (5, 2, 3, 4, 3),
            "Low Cost": (3, 5, 3, 3, 4),
            "Fast Delivery": (3, 4, 4, 3, 5),
        }
        rows: List[DecisionMatrixRow] = []
        best_name = ""
        best_total = -1
        for alt in alternatives:
            latency, cost, complexity, reliability, speed = score_map.get(
                alt.name, (3, 3, 3, 3, 3)
            )
            row = DecisionMatrixRow(
                option=alt.name,
                latency_score=latency,
                cost_score=cost,
                complexity_score=complexity,
                reliability_score=reliability,
                delivery_speed_score=speed,
                notes=f"Focus: {alt.focus}",
            )
            rows.append(row)
            total = latency + cost + complexity + reliability + speed
            if total > best_total:
                best_total = total
                best_name = alt.name
        return rows, best_name

    def generate_design_package_from_task(self, task: str) -> DesignPackage:
        bootstrap_context = [
            (
                "No user-provided clarifications are available. "
                "Infer reasonable defaults, list explicit assumptions, "
                "and highlight missing information under assumptions."
            )
        ]
        design, usage = self._generate_design_with_metrics(task, bootstrap_context)
        quality = evaluate_design_quality(design)
        alternatives = self._build_alternatives(task)
        matrix, recommended = self._build_decision_matrix(alternatives)
        return DesignPackage(
            design=design,
            mermaid_diagram=build_diagram(design),
            quality_report=quality,
            alternatives=alternatives,
            decision_matrix=matrix,
            recommended_option=recommended,
            usage_metrics=usage,
        )

    def generate_implementation_prompt_pack(
        self, task: str, package: DesignPackage
    ) -> ImplementationPromptPack:
        design_json = package.model_dump_json()
        prompt = build_implementation_prompts_prompt(task, design_json)
        raw, usage = self._call_completion(prompt)
        payload = self._parse_json(raw)
        payload = self._normalize_prompt_pack_payload(payload, task)
        result = ImplementationPromptPack(**payload)
        result.usage_metrics = usage
        return result

    def generate_follow_up_response(
        self, task: str, package: DesignPackage, followup: str
    ) -> FollowUpResponse:
        package_json = package.model_dump_json()
        prompt = build_follow_up_prompt(task, package_json, followup)
        raw, _ = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return FollowUpResponse(**payload)

    def generate_threat_model(self, task: str, package: DesignPackage) -> ThreatModel:
        package_json = package.model_dump_json()
        prompt = build_threat_model_prompt(task, package_json)
        raw, _ = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return ThreatModel(**payload)

    def generate_test_plan(self, task: str, package: DesignPackage) -> TestPlan:
        package_json = package.model_dump_json()
        prompt = build_test_plan_prompt(task, package_json)
        raw, _ = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return TestPlan(**payload)
