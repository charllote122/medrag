"""Query orchestration: the single entry point for /api/query."""

import logging
import time
from dataclasses import dataclass, field

from ..db.session import SessionLocal
from ..generation.llm import generate
from ..generation.prompt_builder import build_prompt
from ..generation.verifier import strip_unsupported, verify
from ..profiles.registry import get_profile
from ..retrieval import retrieve, rerank

log = logging.getLogger(__name__)


@dataclass
class QueryResult:
    answer: str
    citations: list[dict] = field(default_factory=list)
    triage: str | None = None
    refused: bool = False
    debug: dict | None = None


def run_query(question: str, profile_name: str) -> QueryResult:
    profile = get_profile(profile_name)
    t0 = time.time()

    # ── 1. Retrieve ──────────────────────────────────────────────
    db = SessionLocal()
    try:
        fused = retrieve(db, question, top_k=20)
        top = rerank(question, fused, top_k=5)
    finally:
        db.close()

    if not top:
        return QueryResult(
            answer="I couldn't find relevant information in my sources.",
            citations=[],
            refused=True,
        )

    # ── 2. Generate ──────────────────────────────────────────────
    system, user = build_prompt(question, top, profile)
    try:
        response = generate(system, user)
    except Exception as e:
        log.exception("LLM call failed")
        return QueryResult(
            answer=f"I couldn't generate an answer: {e}",
            citations=[],
            refused=True,
        )

    # ── 3. Verify citations ──────────────────────────────────────
    v = verify(response.text, top)
    if not v.supported:
        log.warning(
            "verifier flagged %d/%d sentences; coverage=%.2f",
            len(v.flagged), len(v.flagged) + 1, v.coverage,
        )
        # For patient profile: strict — drop unsupported sentences
        # For clinician: lenient — keep but flag in debug
        if profile.name == "patient":
            answer = strip_unsupported(response.text, v.flagged)
        else:
            answer = response.text
    else:
        answer = response.text

    # ── 4. Assemble citations ────────────────────────────────────
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

    # ── 5. Debug payload ─────────────────────────────────────────
    debug = {
        "latency_ms": int((time.time() - t0) * 1000),
        "model": response.model,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "verification": {
            "supported": v.supported,
            "coverage": round(v.coverage, 3),
            "flagged_count": len(v.flagged),
        },
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
