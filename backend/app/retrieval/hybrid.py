"""Hybrid retrieval: dense (pgvector) + sparse (Postgres FTS) + RRF fusion.

Why hybrid?
  - Dense handles paraphrase ("high blood sugar" ~ "hyperglycemia")
  - Sparse handles exact terms (drug names, doses, ICD codes)
  - Neither alone is good enough for medical text

Why RRF?
  - Reciprocal Rank Fusion is a simple, robust way to merge two
    ranked lists without needing to normalize scores.
    Each result gets score = sum(1 / (k + rank)) across lists.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..ingestion.embedder import embed_query
from .schemas import RetrievedChunk


RRF_K = 60  # standard constant from the original RRF paper


def _dense_search(db: Session, query: str, limit: int = 30) -> list[RetrievedChunk]:
    """Vector similarity search via pgvector HNSW index."""
    qvec = embed_query(query)
    sql = text("""
        SELECT
            c.id,
            c.text,
            c.section,
            c.meta->>'source_org'   AS source_org,
            c.meta->>'source_title' AS source_title,
            c.meta->>'source_url'   AS source_url,
            1 - (c.embedding <=> CAST(:qvec AS vector)) AS score
        FROM chunks c
        ORDER BY c.embedding <=> CAST(:qvec AS vector)
        LIMIT :limit
    """)
    rows = db.execute(sql, {"qvec": qvec, "limit": limit}).all()
    return [
        RetrievedChunk(
            chunk_id=r.id,
            text=r.text,
            section=r.section or "",
            source_org=r.source_org or "",
            source_title=r.source_title or "",
            source_url=r.source_url or "",
            dense_score=float(r.score),
        )
        for r in rows
    ]


def _sparse_search(db: Session, query: str, limit: int = 30) -> list[RetrievedChunk]:
    """Full-text search via Postgres tsvector + ts_rank."""
    sql = text("""
        SELECT
            c.id,
            c.text,
            c.section,
            c.meta->>'source_org'   AS source_org,
            c.meta->>'source_title' AS source_title,
            c.meta->>'source_url'   AS source_url,
            ts_rank(
                to_tsvector('english', c.text),
                plainto_tsquery('english', :q)
            ) AS score
        FROM chunks c
        WHERE to_tsvector('english', c.text) @@ plainto_tsquery('english', :q)
        ORDER BY score DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"q": query, "limit": limit}).all()
    return [
        RetrievedChunk(
            chunk_id=r.id,
            text=r.text,
            section=r.section or "",
            source_org=r.source_org or "",
            source_title=r.source_title or "",
            source_url=r.source_url or "",
            sparse_score=float(r.score),
        )
        for r in rows
    ]


def _rrf_fuse(
    dense: list[RetrievedChunk],
    sparse: list[RetrievedChunk],
    k: int = RRF_K,
) -> list[RetrievedChunk]:
    """Merge two ranked lists with Reciprocal Rank Fusion."""
    by_id: dict[int, RetrievedChunk] = {}

    for rank, chunk in enumerate(dense, start=1):
        by_id[chunk.chunk_id] = chunk
        chunk.fusion_score += 1.0 / (k + rank)

    for rank, chunk in enumerate(sparse, start=1):
        if chunk.chunk_id in by_id:
            by_id[chunk.chunk_id].sparse_score = chunk.sparse_score
            by_id[chunk.chunk_id].fusion_score += 1.0 / (k + rank)
        else:
            chunk.fusion_score = 1.0 / (k + rank)
            by_id[chunk.chunk_id] = chunk

    return sorted(by_id.values(), key=lambda c: c.fusion_score, reverse=True)


def retrieve(
    db: Session,
    query: str,
    top_k: int = 10,
    dense_limit: int = 30,
    sparse_limit: int = 30,
) -> list[RetrievedChunk]:
    """Full retrieval pipeline: dense + sparse + RRF fusion."""
    dense = _dense_search(db, query, limit=dense_limit)
    sparse = _sparse_search(db, query, limit=sparse_limit)
    fused = _rrf_fuse(dense, sparse)
    return fused[:top_k]
