"""Cross-encoder reranker.

A cross-encoder looks at (query, chunk) TOGETHER and produces a relevance
score. Much more accurate than embedding similarity, but slower — so we
only rerank the top ~20 fused candidates, not the whole corpus.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (~90MB, fast on CPU)
"""

from functools import lru_cache

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import CrossEncoder

from .schemas import RetrievedChunk


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL, max_length=512)


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Score each (query, chunk) pair, return top_k by rerank_score."""
    if not chunks:
        return []

    model = _get_reranker()
    pairs = [(query, c.text) for c in chunks]
    scores = model.predict(pairs, show_progress_bar=False)

    for chunk, score in zip(chunks, scores):
        chunk.rerank_score = float(score)

    ranked = sorted(chunks, key=lambda c: c.rerank_score, reverse=True)
    return ranked[:top_k]
