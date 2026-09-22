from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...orchestration.pipeline import run_query

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    profile: str = Field(..., pattern="^(patient|clinician)$")


class Citation(BaseModel):
    index: int
    chunk_id: int | None = None
    source_org: str | None = None
    source_title: str | None = None
    section: str | None = None
    source_url: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    triage: str | None
    refused: bool
    profile: str
    debug: dict | None = None


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    result = run_query(req.question, req.profile)
    return QueryResponse(
        answer=result.answer,
        citations=result.citations,
        triage=result.triage,
        refused=result.refused,
        profile=req.profile,
        debug=result.debug,
    )


@router.post("/debug/retrieve")
def debug_retrieve(req: QueryRequest) -> dict:
    result = run_query(req.question, req.profile)
    return {
        "question": req.question,
        "profile": req.profile,
        "triage": result.triage,
        "refused": result.refused,
        "answer": result.answer,
        "citations": result.citations,
        "debug": result.debug,
    }
