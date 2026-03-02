from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.diagram import build_diagram
from core.exporters import to_confluence_wiki, to_github_pr_comment
from core.features import diff_design_packages, estimate_cost
from core.generator import DesignGenerator
from core.history import (
    add_reviewer_comment,
    create_history_entry,
    get_history_entry,
    list_history_entries,
    set_review_status,
)
from core.schemas import (
    ClarificationResponse,
    CostEstimate,
    CostModelInput,
    DesignDiff,
    DesignPackage,
    DesignResponse,
    FollowUpResponse,
    HistoryEntry,
    ImplementationPromptPack,
    TestPlan,
    ThreatModel,
)
from core.security import get_api_key

generator_instance: DesignGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the DesignGenerator lifecycle."""
    global generator_instance
    created_here = False
    if generator_instance is None:
        generator_instance = DesignGenerator()
        created_here = True
    yield
    if created_here:
        generator_instance = None


app = FastAPI(
    title="SystemDesign-GPT API",
    version="1.0.0",
    lifespan=lifespan,
)


def get_generator() -> DesignGenerator:
    if generator_instance is None:
        raise HTTPException(
            status_code=503,
            detail="DesignGenerator is not available.",
        )
    return generator_instance


class ClarifyRequest(BaseModel):
    question: str = Field(..., min_length=3)


class DesignRequest(BaseModel):
    question: str = Field(..., min_length=3)
    clarifications: List[str]


class TaskDesignRequest(BaseModel):
    task: str = Field(..., min_length=3)


class DesignDiffRequest(BaseModel):
    from_task: str = Field(..., min_length=3)
    to_task: str = Field(..., min_length=3)


class FollowUpRequest(BaseModel):
    task: str = Field(..., min_length=3)
    followup: str = Field(..., min_length=3)
    package: DesignPackage


class CostEstimateRequest(BaseModel):
    task: str = Field(..., min_length=3)
    model_input: CostModelInput = Field(default_factory=CostModelInput)


class HistoryCreateRequest(BaseModel):
    task: str = Field(..., min_length=3)
    tags: List[str] = Field(default_factory=list)
    package: DesignPackage


class ReviewStatusRequest(BaseModel):
    status: str = Field(..., min_length=3)


class ReviewerCommentRequest(BaseModel):
    comment: str = Field(..., min_length=2)


class DesignWithDiagramResponse(BaseModel):
    design: DesignResponse
    mermaid_diagram: str


class DesignPackageResponse(BaseModel):
    package: DesignPackage


class PromptPackResponse(BaseModel):
    prompt_pack: ImplementationPromptPack


class DesignDiffResponse(BaseModel):
    diff: DesignDiff


class FollowUpResultResponse(BaseModel):
    result: FollowUpResponse


class ThreatModelResponse(BaseModel):
    threat_model: ThreatModel


class TestPlanResponse(BaseModel):
    test_plan: TestPlan


class CostEstimateResponse(BaseModel):
    estimate: CostEstimate


class HistoryEntryResponse(BaseModel):
    entry: HistoryEntry


class HistoryListResponse(BaseModel):
    entries: List[HistoryEntry]


class ExportResponse(BaseModel):
    markdown: str
    confluence_wiki: str
    github_pr_comment: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/clarify",
    response_model=ClarificationResponse,
    dependencies=[Depends(get_api_key)],
)
def clarify(
    payload: ClarifyRequest, generator: DesignGenerator = Depends(get_generator)
) -> ClarificationResponse:
    try:
        return generator.generate_clarifying_questions(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/design",
    response_model=DesignWithDiagramResponse,
    dependencies=[Depends(get_api_key)],
)
def design(
    payload: DesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> DesignWithDiagramResponse:
    try:
        result = generator.generate_design(payload.question, payload.clarifications)
        return DesignWithDiagramResponse(
            design=result, mermaid_diagram=build_diagram(result)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/design-from-task",
    response_model=DesignWithDiagramResponse,
    dependencies=[Depends(get_api_key)],
)
def design_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> DesignWithDiagramResponse:
    try:
        result = generator.generate_design_from_task(payload.task)
        return DesignWithDiagramResponse(
            design=result, mermaid_diagram=build_diagram(result)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/design-package-from-task",
    response_model=DesignPackageResponse,
    dependencies=[Depends(get_api_key)],
)
def design_package_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> DesignPackageResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        create_history_entry(payload.task, package, tags=[])
        return DesignPackageResponse(package=package)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/implementation-prompts-from-task",
    response_model=PromptPackResponse,
    dependencies=[Depends(get_api_key)],
)
def implementation_prompts_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> PromptPackResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        prompt_pack = generator.generate_implementation_prompt_pack(
            payload.task, package
        )
        return PromptPackResponse(prompt_pack=prompt_pack)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/design-diff-from-tasks",
    response_model=DesignDiffResponse,
    dependencies=[Depends(get_api_key)],
)
def design_diff_from_tasks(
    payload: DesignDiffRequest, generator: DesignGenerator = Depends(get_generator)
) -> DesignDiffResponse:
    try:
        from_package = generator.generate_design_package_from_task(payload.from_task)
        to_package = generator.generate_design_package_from_task(payload.to_task)
        diff = diff_design_packages(
            payload.from_task, from_package, payload.to_task, to_package
        )
        return DesignDiffResponse(diff=diff)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/follow-up",
    response_model=FollowUpResultResponse,
    dependencies=[Depends(get_api_key)],
)
def follow_up(
    payload: FollowUpRequest, generator: DesignGenerator = Depends(get_generator)
) -> FollowUpResultResponse:
    try:
        result = generator.generate_follow_up_response(
            payload.task, payload.package, payload.followup
        )
        return FollowUpResultResponse(result=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/threat-model-from-task",
    response_model=ThreatModelResponse,
    dependencies=[Depends(get_api_key)],
)
def threat_model_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> ThreatModelResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        model = generator.generate_threat_model(payload.task, package)
        return ThreatModelResponse(threat_model=model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/test-plan-from-task",
    response_model=TestPlanResponse,
    dependencies=[Depends(get_api_key)],
)
def test_plan_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> TestPlanResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        plan = generator.generate_test_plan(payload.task, package)
        return TestPlanResponse(test_plan=plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/cost-estimate-from-task",
    response_model=CostEstimateResponse,
    dependencies=[Depends(get_api_key)],
)
def cost_estimate_from_task(
    payload: CostEstimateRequest, generator: DesignGenerator = Depends(get_generator)
) -> CostEstimateResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        estimate = estimate_cost(package, payload.model_input)
        return CostEstimateResponse(estimate=estimate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/exports-from-task",
    response_model=ExportResponse,
    dependencies=[Depends(get_api_key)],
)
def exports_from_task(
    payload: TaskDesignRequest, generator: DesignGenerator = Depends(get_generator)
) -> ExportResponse:
    try:
        package = generator.generate_design_package_from_task(payload.task)
        markdown = package.model_dump_json(indent=2)
        confluence = to_confluence_wiki(payload.task, package, None)
        pr_comment = to_github_pr_comment(payload.task, package)
        return ExportResponse(
            markdown=markdown,
            confluence_wiki=confluence,
            github_pr_comment=pr_comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/design-history",
    response_model=HistoryListResponse,
    dependencies=[Depends(get_api_key)],
)
def design_history() -> HistoryListResponse:
    return HistoryListResponse(entries=list_history_entries())


@app.get(
    "/design-history/{version_id}",
    response_model=HistoryEntryResponse,
    dependencies=[Depends(get_api_key)],
)
def design_history_entry(version_id: str) -> HistoryEntryResponse:
    entry = get_history_entry(version_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return HistoryEntryResponse(entry=entry)


@app.post(
    "/design-history",
    response_model=HistoryEntryResponse,
    dependencies=[Depends(get_api_key)],
)
def create_design_history(payload: HistoryCreateRequest) -> HistoryEntryResponse:
    entry = create_history_entry(payload.task, payload.package, payload.tags)
    return HistoryEntryResponse(entry=entry)


@app.post(
    "/design-history/{version_id}/status",
    response_model=HistoryEntryResponse,
    dependencies=[Depends(get_api_key)],
)
def update_design_status(
    version_id: str, payload: ReviewStatusRequest
) -> HistoryEntryResponse:
    if payload.status not in {"draft", "approved", "needs_changes"}:
        raise HTTPException(status_code=400, detail="Invalid status value.")
    entry = set_review_status(version_id, payload.status)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return HistoryEntryResponse(entry=entry)


@app.post(
    "/design-history/{version_id}/comments",
    response_model=HistoryEntryResponse,
    dependencies=[Depends(get_api_key)],
)
def add_design_comment(
    version_id: str, payload: ReviewerCommentRequest
) -> HistoryEntryResponse:
    entry = add_reviewer_comment(version_id, payload.comment)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return HistoryEntryResponse(entry=entry)
