from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.diagram import build_diagram
from core.generator import DesignGenerator
from core.schemas import (
    ClarificationResponse,
    DesignPackage,
    DesignResponse,
    ImplementationPromptPack,
)
from core.security import get_api_key

generator_instance: DesignGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the DesignGenerator lifecycle."""
    global generator_instance
    generator_instance = DesignGenerator()
    yield
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


class DesignWithDiagramResponse(BaseModel):
    design: DesignResponse
    mermaid_diagram: str


class DesignPackageResponse(BaseModel):
    package: DesignPackage


class PromptPackResponse(BaseModel):
    prompt_pack: ImplementationPromptPack


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
