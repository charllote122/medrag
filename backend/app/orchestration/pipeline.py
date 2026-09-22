"""Query orchestration: the single entry point for /api/query.

Order of operations:
  1. Triage (patient profile only) — emergency/urgent/personal/out_of_corpus
     get a hardcoded response, no retrieval, no LLM generation.
  2. Retrieval — hybrid dense+sparse, then rerank.
  3. Generation — profile-aware prompt, LLM answer with citations.
  4. Verification — check each citation.
"""

import logging
import time
from dataclasses import dataclass, field

from ..db.session import SessionLocal
from ..generation.llm import generate
from ..generation.prompt_builder import build_prompt
from ..generation.verifier import strip_unsupported, verify
from ..profiles.registry import get_profile
from ..retrieval import retrieve, rerank
from ..triage import TriageClass, classify as triage_classify, fallback_answer

log = logging.getLogger(__name__)


@dataclass
class QueryResult:
    answer: str
    citations: list[dict] = field(default_factory=list)
    triage: str | None = None
    refused: bool = False
    debug: dict | None = None


def _do_triage(question: str, profile_name: str, debug: dict) -> QueryResult | None:
    """Run triage. Return a QueryResult if we should short-circuit, else None."""
    # Clinician profile: skip personal/urgent classes; still catch
    # emergency and out_of_corpus.
    try:
        result = triage_classify(question, profile_name)
    except Exception as e:
        log.exception("triage failed entirely")
        return None

    debug["triage"] = {
        "class": result.cls.value,
        "reason": result.reason,
    }

    if result.cls == TriageClass.INFORMATIONAL:
        return None

    # Clinician profile is more permissive
    if profile_name == "clinician" and result.cls in (
        TriageClass.PERSONAL,
        TriageClass.URGENT,
    ):
        return None

    answer = fallback_answer(result.cls) or "I can't answer that."
    return QueryResult(
        answer=answer,
        citations=[],
        triage=result.cls.value,
        refused=(result.cls != TriageClass.INFORMATIONAL),
        debug=debug,
    )


def run_query(question: str, profile_name: str) -> QueryResult:
    profile = get_profile(profile_name)
    t0 = time.time()
    debug: dict = {}

    # ── 1. Triage ────────────────────────────────────────────────
    triage_result = _do_triage(question, profile_name, debug)
    if triage_result is not None:
        if debug.get("triage"):
            debug["latency_ms"] = int((time.time() - t0) * 1000)
        triage_result.debug = debug
        return triage_result

    # ── 2. Retrieve ──────────────────────────────────────────────
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
            triage=None,
            refused=True,
            debug=debug,
        )

    # ── 3. Generate ──────────────────────────────────────────────
    system, user = build_prompt(question, top, profile)
    try:
        response = generate(system, user)
    except Exception as e:
        log.exception("LLM call failed")
        return QueryResult(
            answer=f"I couldn't generate an answer: {e}",
            citations=[],
            refused=True,
            debug=debug,
        )

    # ── 4. Verify citations ──────────────────────────────────────
    v = verify(response.text, top)
    if not v.supported and profile.name == "patient":
        answer = strip_unsupported(response.text, v.flagged)
    else:
        answer = response.text

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

    debug.update({
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
    })

    return QueryResult(
        answer=answer,
        citations=citations,
        triage=None,
        refused=False,
        debug=debug,
    )
