from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ClarificationResponse(BaseModel):
    questions: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly three clarifying questions to ask the candidate.",
    )


class Component(BaseModel):
    name: str
    type: str
    description: str
    connections: List[str] = Field(default_factory=list)


class DesignResponse(BaseModel):
    assumptions: List[str]
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    high_level_architecture: str
    components: List[Component]
    database_design: str
    scaling_strategy: str
    caching_strategy: str
    capacity_estimation: str
    bottlenecks: List[str]
    tradeoffs: List[str]
    mermaid_diagram: str
