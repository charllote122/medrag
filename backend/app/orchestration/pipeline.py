from dataclasses import dataclass
from ..profiles.registry import get_profile


@dataclass
class QueryResult:
    answer: str
    citations: list[dict]
    triage: str | None
    refused: bool


def run_query(question: str, profile_name: str) -> QueryResult:
    profile = get_profile(profile_name)
    # TODO: triage → retrieve → rerank → generate → verify
    return QueryResult(
        answer=f"[{profile.name} stub] You asked: {question}",
        citations=[],
        triage=None,
        refused=False,
    )
