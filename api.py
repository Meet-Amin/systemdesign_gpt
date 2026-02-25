from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.diagram import build_diagram
from core.generator import DesignGenerator
from core.schemas import ClarificationResponse, DesignPackage, DesignResponse


app = FastAPI(title="SystemDesign-GPT API", version="1.0.0")


class ClarifyRequest(BaseModel):
    question: str = Field(..., min_length=3)


class DesignRequest(BaseModel):
    question: str = Field(..., min_length=3)
    clarifications: List[str] = Field(..., min_length=3)


class TaskDesignRequest(BaseModel):
    task: str = Field(..., min_length=3)


class DesignWithDiagramResponse(BaseModel):
    design: DesignResponse
    mermaid_diagram: str


class DesignPackageResponse(BaseModel):
    package: DesignPackage


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/clarify", response_model=ClarificationResponse)
def clarify(payload: ClarifyRequest) -> ClarificationResponse:
    try:
        generator = DesignGenerator()
        return generator.generate_clarifying_questions(payload.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/design", response_model=DesignWithDiagramResponse)
def design(payload: DesignRequest) -> DesignWithDiagramResponse:
    try:
        generator = DesignGenerator()
        result = generator.generate_design(payload.question, payload.clarifications)
        return DesignWithDiagramResponse(design=result, mermaid_diagram=build_diagram(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/design-from-task", response_model=DesignWithDiagramResponse)
def design_from_task(payload: TaskDesignRequest) -> DesignWithDiagramResponse:
    try:
        generator = DesignGenerator()
        result = generator.generate_design_from_task(payload.task)
        return DesignWithDiagramResponse(design=result, mermaid_diagram=build_diagram(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/design-package-from-task", response_model=DesignPackageResponse)
def design_package_from_task(payload: TaskDesignRequest) -> DesignPackageResponse:
    try:
        generator = DesignGenerator()
        package = generator.generate_design_package_from_task(payload.task)
        return DesignPackageResponse(package=package)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
