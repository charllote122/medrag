from fastapi import APIRouter
from pydantic import BaseModel, Field
from ...orchestration.pipeline import run_query

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    profile: str = Field(..., pattern="^(patient|clinician)$")


class Citation(BaseModel):
    index: int
    source_org: str | None = None
    source_title: str | None = None
    page: int | None = None
    section: str | None = None
    url: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    triage: str | None
    refused: bool
    profile: str


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    result = run_query(req.question, req.profile)
    return QueryResponse(
        answer=result.answer,
        citations=result.citations,
        triage=result.triage,
        refused=result.refused,
        profile=req.profile,
    )
