"""Section-aware chunker."""

from dataclasses import dataclass

import tiktoken

from .loaders.base import RawDocument

_TOKENIZER = tiktoken.get_encoding("cl100k_base")

TARGET_TOKENS = 400
MAX_TOKENS = 500
OVERLAP_TOKENS = 60


@dataclass
class Chunk:
    text: str
    source_org: str
    source_title: str
    source_url: str
    section: str
    page: int | None
    chunk_index: int
    metadata: dict


def _tok(text: str) -> list[int]:
    return _TOKENIZER.encode(text)


def _detok(tokens: list[int]) -> str:
    return _TOKENIZER.decode(tokens)


def chunk_document(doc: RawDocument) -> list[Chunk]:
    tokens = _tok(doc.text)
    if not tokens:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + TARGET_TOKENS, len(tokens))
        text = _detok(tokens[start:end]).strip()

        if len(text) > 50:
            chunks.append(
                Chunk(
                    text=text,
                    source_org=doc.source_org,
                    source_title=doc.source_title,
                    source_url=doc.source_url,
                    section=doc.section,
                    page=doc.page,
                    chunk_index=idx,
                    metadata=doc.metadata,
                )
            )
            idx += 1

        if end == len(tokens):
            break
        start = end - OVERLAP_TOKENS

    return chunks


def chunk_documents(docs: list[RawDocument]) -> list[Chunk]:
    out: list[Chunk] = []
    for d in docs:
        out.extend(chunk_document(d))
    return out
