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
    api_contracts: List[str]
    data_model_entities: List[str]
    sequence_of_operations: List[str]
    high_level_architecture: str
    components: List[Component]
    database_design: str
    consistency_and_transactions: str
    scaling_strategy: str
    caching_strategy: str
    capacity_estimation: str
    reliability_and_resilience: str
    security_and_compliance: str
    observability_and_slos: str
    deployment_and_release_strategy: str
    disaster_recovery: str
    cost_estimation: str
    testing_strategy: str
    operational_runbook: List[str]
    bottlenecks: List[str]
    tradeoffs: List[str]
    mermaid_diagram: str


class UsageMetrics(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0


class QualityDimension(BaseModel):
    name: str
    score: int = Field(..., ge=0, le=10)
    rationale: str


class QualityReport(BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    dimensions: List[QualityDimension]
    missing_areas: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ArchitectureAlternative(BaseModel):
    name: str
    focus: str
    summary: str
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class DecisionMatrixRow(BaseModel):
    option: str
    latency_score: int = Field(..., ge=1, le=5)
    cost_score: int = Field(..., ge=1, le=5)
    complexity_score: int = Field(..., ge=1, le=5)
    reliability_score: int = Field(..., ge=1, le=5)
    delivery_speed_score: int = Field(..., ge=1, le=5)
    notes: str


class DesignPackage(BaseModel):
    design: DesignResponse
    mermaid_diagram: str
    quality_report: QualityReport
    alternatives: List[ArchitectureAlternative] = Field(default_factory=list)
    decision_matrix: List[DecisionMatrixRow] = Field(default_factory=list)
    recommended_option: str = ""
    usage_metrics: UsageMetrics = Field(default_factory=UsageMetrics)


class VibePrompt(BaseModel):
    title: str
    objective: str
    recommended_tools: List[str] = Field(default_factory=list)
    prompt: str


class ImplementationPromptPack(BaseModel):
    generated_for_task: str
    recommended_tools_overview: List[str] = Field(default_factory=list)
    prompts: List[VibePrompt] = Field(default_factory=list)
    usage_metrics: UsageMetrics = Field(default_factory=UsageMetrics)
