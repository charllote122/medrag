"""Base types for source loaders."""

from dataclasses import dataclass, field
from typing import Protocol
from pathlib import Path


@dataclass
class RawDocument:
    """One logical section of one source document."""
    source_org: str
    source_title: str
    source_url: str
    section: str
    text: str
    page: int | None = None
    effective_date: str | None = None
    metadata: dict = field(default_factory=dict)


class Loader(Protocol):
    source_org: str

    def can_load(self, path: Path) -> bool:
        ...

    def load(self, path: Path) -> list[RawDocument]:
        ...
