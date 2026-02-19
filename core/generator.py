from __future__ import annotations

import json
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from .prompts import build_clarification_prompt, build_design_prompt
from .schemas import ClarificationResponse, DesignResponse


MODEL = "gpt-4o-mini"

load_dotenv()


class DesignGenerator:
    def __init__(self, model: str = MODEL):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to a .env file or export it in your shell."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call_completion(self, prompt: str) -> str:
        # Single gateway for LLM calls so error handling stays consistent.
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are SystemDesign-GPT, an opinionated but practical system design interviewer. "
                            "Provide structured answers and never stray from JSON when asked."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1400,
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("OpenAI API returned an empty message.")
            return content
        except OpenAIError as exc:
            raise RuntimeError("OpenAI API call failed: " + str(exc)) from exc

    def _parse_json(self, payload: str) -> dict:
        # Recover the first JSON object even if the model wraps it with extra text.
        content = payload.strip()
        if not content:
            raise ValueError("LLM returned an empty response")
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Could not locate a JSON object in the LLM response")
        snippet = content[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response was not valid JSON: " + str(exc)) from exc

    def generate_clarifying_questions(self, question: str) -> ClarificationResponse:
        prompt = build_clarification_prompt(question)
        raw = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return ClarificationResponse(**payload)

    def generate_design(self, question: str, clarifications: List[str]) -> DesignResponse:
        prompt = build_design_prompt(question, clarifications)
        raw = self._call_completion(prompt)
        payload = self._parse_json(raw)
        return DesignResponse(**payload)
