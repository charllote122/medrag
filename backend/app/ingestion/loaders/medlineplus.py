"""Loader for MedlinePlus patient-facing topic pages (HTML)."""

import re
from pathlib import Path

from bs4 import BeautifulSoup

from .base import RawDocument


class MedlinePlusLoader:
    source_org = "MedlinePlus"

    def can_load(self, path: Path) -> bool:
        return path.suffix == ".html" and "medlineplus" in str(path).lower()

    def load(self, path: Path) -> list[RawDocument]:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "lxml")

        title_tag = soup.find("title")
        title = (
            title_tag.get_text(strip=True).split("|")[0].strip()
            if title_tag
            else path.stem
        )

        url = f"https://medlineplus.gov/{path.stem.replace('_', '')}.html"

        main = soup.find("main") or soup.find(id="topic-summary") or soup.body
        if main is None:
            return []

        for tag in main.find_all(["nav", "aside", "script", "style", "footer"]):
            tag.decompose()

        docs: list[RawDocument] = []
        current_section = "Summary"
        current_parts: list[str] = []

        def flush():
            if current_parts:
                text = "\n\n".join(p for p in current_parts if p.strip())
                text = self._clean(text)
                if len(text) > 100:
                    docs.append(
                        RawDocument(
                            source_org=self.source_org,
                            source_title=title,
                            source_url=url,
                            section=current_section,
                            text=text,
                        )
                    )

        for el in main.descendants:
            if getattr(el, "name", None) in ("h1", "h2", "h3"):
                flush()
                current_section = el.get_text(" ", strip=True)
                current_parts = []
            elif getattr(el, "name", None) in ("p", "li"):
                txt = el.get_text(" ", strip=True)
                if txt:
                    current_parts.append(txt)

        flush()
        return docs

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
