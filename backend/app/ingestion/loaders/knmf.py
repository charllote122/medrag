"""Loader for the Kenya National Medicines Formulary (PDF).

Structure detected in KNMF 2023 1st Edition:
  [Chapter # + Name]        e.g. "14Cardiovascular Medicines"
  [Subsection]              e.g. "Antihypertensive medicines"
  [Drug Name]               e.g. "Hydrochlorothiazide (HCTZ)"
  ATC code: XXX             e.g. "ATC code: C03AA03"
  [Formulation], LOU N      e.g. "Tablet (scored), 25 mg, LOU 3"
  Indications and dose
    Adult: ...
    Paediatric: ...
  Contraindications: ...
  Precautions: ...
  Adverse effects: ...
  Interactions: ...

One RawDocument per drug. Metadata carries ATC code, LOU, formulation.
"""

import re
from pathlib import Path

from pypdf import PdfReader

from .base import RawDocument


# Matches section labels — lines that mark the end of a drug name and
# the start of its structured fields. If a line starts with any of these,
# the preceding line was the drug name.
SECTION_LABELS = {
    "ATC code:",
    "Indications and dose",
    "Contraindications:",
    "Precautions:",
    "Adverse effects:",
    "Adverse         effects:",
    "Interactions:",
    "Notes:",
    "Pregnancy:",
    "Breastfeeding:",
    "Renal Impairment:",
    "Renal impairment:",
    "Hepatic Impairment:",
    "Hepatic impairment:",
}

# Lines that should never be treated as drug names
NOISE_PATTERNS = re.compile(
    r"^(KENYA NATIONAL|KNMF-1|Page \d|)"
    r"|^\d{3}\s*KNMF"        # page footer like "275KNMF-1"
    r"|^[A-Z][A-Z\s&]+\s*$"  # all-caps line — probably a header
)

# Chapter heading: e.g. "14Cardiovascular Medicines" or "20. Medicines For Endocrine Disorders"
CHAPTER_PAT = re.compile(r"^(\d{1,2})(\.|\s|[A-Z])")

# Subsection: e.g. "20.1. Adrenal Hormones" or "Antihypertensive medicines"
SUBSECTION_PAT = re.compile(r"^\d{1,2}\.\d+(\.\d+)?\.?\s+[A-Z]")

# ATC code line
ATC_PAT = re.compile(r"^ATC\s*code:\s*([A-Z]\d{2}[A-Z]{2}\d{2})")

# LOU marker — Level of Use
LOU_PAT = re.compile(r"LOU\s*(\d)")


class KNMFLoader:
    source_org = "KNMF"
    source_title = "Kenya National Medicines Formulary 2023 (1st Edition)"
    source_url = "https://www.health.go.ke/"

    def can_load(self, path: Path) -> bool:
        return "knmf" in path.name.lower() and path.suffix == ".pdf"

    def load(self, path: Path) -> list[RawDocument]:
        reader = PdfReader(path)
        docs: list[RawDocument] = []

        current_chapter: str | None = None
        current_subsection: str | None = None
        current_drug: str | None = None
        current_atc: str | None = None
        current_lou: str | None = None
        current_page: int | None = None
        buffer: list[str] = []

        def flush():
            nonlocal current_drug, current_atc, current_lou, current_page, buffer
            if not current_drug or not buffer:
                return
            text = "\n".join(buffer).strip()
            if len(text) < 100:
                return

            section_parts = []
            if current_chapter:
                section_parts.append(current_chapter)
            if current_subsection:
                section_parts.append(current_subsection)
            section_parts.append(current_drug)
            section = " > ".join(section_parts)

            docs.append(
                RawDocument(
                    source_org=self.source_org,
                    source_title=self.source_title,
                    source_url=self.source_url,
                    section=section,
                    text=text,
                    page=current_page,
                    metadata={
                        "atc_code": current_atc or "",
                        "lou": current_lou or "",
                        "country": "KE",
                    },
                )
            )
            current_drug = None
            current_atc = None
            current_lou = None
            buffer = []

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                continue

            lines = text.split("\n")

            i = 0
            while i < len(lines):
                raw = lines[i]
                line = raw.strip()

                if not line:
                    if buffer:
                        buffer.append("")
                    i += 1
                    continue

                # Skip page headers/footers
                if (
                    line.startswith("KENYA NATIONAL MEDICINES FORMULARY")
                    or line.endswith("KNMF-1")
                    or line.startswith("fontTools is required")
                    or line.startswith("Ignoring wrong pointing")
                ):
                    i += 1
                    continue

                # Chapter heading
                if CHAPTER_PAT.match(line) and not SUBSECTION_PAT.match(line):
                    if len(line) < 80 and (
                        "Medicines" in line
                        or "Disorders" in line
                        or "Agents" in line
                        or "Disinfectants" in line
                        or "Diuretics" in line
                        or "Anaesthetics" in line
                    ):
                        flush()
                        current_chapter = line
                        current_subsection = None
                        i += 1
                        continue

                # Subsection heading
                if SUBSECTION_PAT.match(line) and len(line) < 100:
                    flush()
                    current_subsection = line
                    i += 1
                    continue

                # ATC code line — indicates the previous line was the drug name
                atc_match = ATC_PAT.match(line)
                if atc_match:
                    if buffer:
                        # The drug name is the last non-empty line in buffer
                        for j in range(len(buffer) - 1, -1, -1):
                            if buffer[j].strip():
                                current_drug = buffer[j].strip()
                                buffer = buffer[:j]
                                break
                    current_atc = atc_match.group(1)
                    current_page = page_num
                    buffer.append(line)
                    i += 1
                    continue

                # LOU line — often on the same line as formulation
                lou_match = LOU_PAT.search(line)
                if lou_match:
                    current_lou = f"LOU {lou_match.group(1)}"

                # Section labels
                is_label = any(line.startswith(lbl) for lbl in SECTION_LABELS)

                if not is_label and current_drug is None:
                    # Might be a drug name — buffered, waiting for ATC code to confirm
                    buffer.append(line)
                else:
                    buffer.append(line)

                i += 1

        flush()
        return docs
