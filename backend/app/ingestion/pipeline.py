"""Ingestion pipeline: load -> chunk -> embed -> store."""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from ..db.models import Chunk as ChunkRow, Document, Source
from ..db.session import SessionLocal
from .chunker import Chunk, chunk_documents
from .embedder import embed_texts
from .loaders import find_loader

log = logging.getLogger(__name__)


def _get_or_create_source(db: Session, doc: Chunk) -> Source:
    src = (
        db.query(Source)
        .filter(Source.org == doc.source_org, Source.title == doc.source_title)
        .one_or_none()
    )
    if src is None:
        src = Source(
            org=doc.source_org,
            title=doc.source_title,
            doc_type="guideline",
            url=doc.source_url,
        )
        db.add(src)
        db.flush()
    return src


def _get_or_create_document(db: Session, source: Source, url: str) -> Document:
    d = (
        db.query(Document)
        .filter(Document.source_id == source.id, Document.file_path == url)
        .one_or_none()
    )
    if d is None:
        d = Document(source_id=source.id, file_path=url)
        db.add(d)
        db.flush()
    return d


def ingest_files(paths: list[Path], db: Session | None = None) -> dict:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    stats = {"files": 0, "sections": 0, "chunks": 0, "skipped": 0}
    try:
        all_docs = []
        for p in paths:
            loader = find_loader(p)
            if loader is None:
                log.warning("no loader for %s - skipping", p)
                stats["skipped"] += 1
                continue
            docs = loader.load(p)
            log.info("%s -> %d sections", p.name, len(docs))
            all_docs.extend(docs)
            stats["files"] += 1

        stats["sections"] = len(all_docs)
        if not all_docs:
            return stats

        chunks = chunk_documents(all_docs)
        stats["chunks"] = len(chunks)
        log.info("chunked into %d chunks", len(chunks))

        BATCH = 2
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            vecs = embed_texts([c.text for c in batch])
            log.info(
                "embedded batch %d/%d",
                i // BATCH + 1,
                (len(chunks) + BATCH - 1) // BATCH,
            )

            for chunk, vec in zip(batch, vecs):
                source = _get_or_create_source(db, chunk)
                doc = _get_or_create_document(db, source, chunk.source_url)
                row = ChunkRow(
                    document_id=doc.id,
                    page=chunk.page,
                    section=chunk.section,
                    text=chunk.text,
                    embedding=vec,
                    meta={
                        "source_org": chunk.source_org,
                        "source_title": chunk.source_title,
                        "source_url": chunk.source_url,
                        "chunk_index": chunk.chunk_index,
                    },
                )
                db.add(row)
            db.flush()

        db.commit()
    finally:
        if close_db:
            db.close()

    return stats
