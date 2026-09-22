"""Embedding wrapper (memory-conscious)."""

import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 32,
        convert_to_numpy=True,
    )
    return vecs.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def embedding_dim() -> int:
    return _get_model().get_sentence_embedding_dimension()
