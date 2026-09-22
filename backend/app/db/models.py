from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 1024  # BGE-M3


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    org: Mapped[str] = mapped_column(String(32))  # WHO / CDC / NICE
    title: Mapped[str] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(String(32))  # guideline / label / schedule
    version: Mapped[str | None] = mapped_column(String(64))
    effective_date: Mapped[datetime | None] = mapped_column(DateTime)
    url: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="source")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    file_path: Mapped[str] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)

    source: Mapped[Source] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    page: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped[Document] = relationship(back_populates="chunks")


Index(
    "chunks_embedding_hnsw",
    Chunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped[str] = mapped_column(String(16))
    question: Mapped[str] = mapped_column(Text)
    triage: Mapped[str | None] = mapped_column(String(32))
    retrieved_chunk_ids: Mapped[list[int]] = mapped_column(JSON)
    answer: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[list[dict]] = mapped_column(JSON)
    refused: Mapped[bool] = mapped_column(default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
