"""Data shapes for retrieval.

A RetrievedChunk carries both the text and enough metadata to
build a citation later. Score fields let you inspect how a chunk
was ranked at each stage.
"""

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: int
    text: str
    section: str
    source_org: str
    source_title: str
    source_url: str

    # Scores at each stage of the pipeline
    dense_score: float = 0.0     # 1 - cosine_distance, from pgvector
    sparse_score: float = 0.0    # ts_rank from Postgres FTS
    fusion_score: float = 0.0    # RRF score
    rerank_score: float = 0.0    # cross-encoder score

    def citation_key(self) -> str:
        """Short label for inline citation like [1], [2]."""
        return f"{self.source_org}:{self.section[:40]}"
