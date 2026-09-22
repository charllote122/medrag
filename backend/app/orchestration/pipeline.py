"""Query orchestration: the single entry point for /api/query.

Right now (Day 3) this returns retrieved chunks as a debug payload.
Day 4 will add generation + citation verification + triage.
"""

from dataclasses import dataclass, field

from ..db.session import SessionLocal
from ..profiles.registry import get_profile
from ..retrieval import retrieve, rerank


@dataclass
class QueryResult:
    answer: str
    citations: list[dict] = field(default_factory=list)
    triage: str | None = None
    refused: bool = False
    debug: dict | None = None


def run_query(question: str, profile_name: str) -> QueryResult:
    profile = get_profile(profile_name)

    db = SessionLocal()
    try:
        # Stage 1: hybrid retrieval (dense + sparse + RRF)
        fused = retrieve(db, question, top_k=20)

        # Stage 2: cross-encoder rerank → top 5
        top = rerank(question, fused, top_k=5)
    finally:
        db.close()

    citations = [
        {
            "index": i + 1,
            "chunk_id": c.chunk_id,
            "section": c.section,
            "source_org": c.source_org,
            "source_title": c.source_title,
            "source_url": c.source_url,
        }
        for i, c in enumerate(top)
    ]

    # Placeholder answer — Day 4 replaces this with real generation
    preview = "\n\n".join(
        f"[{i+1}] {c.section} ({c.source_org})\n{c.text[:300]}..."
        for i, c in enumerate(top)
    )
    answer = f"[Day-3 debug retrieval for profile={profile.name}]\n\n{preview}"

    debug = {
        "fused_count": len(fused),
        "top_count": len(top),
        "chunks": [
            {
                "rank": i + 1,
                "chunk_id": c.chunk_id,
                "section": c.section,
                "source_org": c.source_org,
                "dense_score": round(c.dense_score, 4),
                "sparse_score": round(c.sparse_score, 4),
                "fusion_score": round(c.fusion_score, 4),
                "rerank_score": round(c.rerank_score, 4),
                "text_preview": c.text[:200],
            }
            for i, c in enumerate(top)
        ],
    }

    return QueryResult(
        answer=answer,
        citations=citations,
        triage=None,
        refused=False,
        debug=debug,
    )
