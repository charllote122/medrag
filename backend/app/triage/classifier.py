"""Triage classifier.

Runs an LLM-based classification before retrieval. Returns a TriageResult
that the pipeline uses to decide whether to proceed to RAG.
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum

from ..generation.llm import generate
from .prompts import build_triage_prompt

log = logging.getLogger(__name__)


class TriageClass(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    PERSONAL = "personal"
    OUT_OF_CORPUS = "out_of_corpus"
    INFORMATIONAL = "informational"


@dataclass
class TriageResult:
    cls: TriageClass
    reason: str
    raw: str


FALLBACKS = {
    TriageClass.EMERGENCY: (
        "This sounds like a medical emergency. Call emergency services now. "
        "US: 911. EU: 112. UK: 999. "
        "Do not wait. Do not use this system to evaluate an emergency."
    ),
    TriageClass.URGENT: (
        "You should see a doctor within 24 hours. If symptoms worsen, "
        "call emergency services. I can't give personal medical advice."
    ),
    TriageClass.PERSONAL: (
        "I can't assess your personal medical situation or recommend "
        "treatment for you. Please talk to a clinician who knows your "
        "history. In the meantime, I can answer general questions about "
        "type 2 diabetes or high blood pressure if that would help."
    ),
    TriageClass.OUT_OF_CORPUS: (
        "I don't have information about this in my sources. "
        "I cover topics from NICE and MedlinePlus, including "
        "type 2 diabetes and high blood pressure."
    ),
}


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def classify(question: str, profile: str) -> TriageResult:
    system, user = build_triage_prompt(question, profile)
    try:
        response = generate(system, user, temperature=0.0, max_tokens=150)
    except Exception as e:
        log.exception("triage LLM call failed")
        return TriageResult(
            cls=TriageClass.INFORMATIONAL,
            reason=f"triage_llm_error: {e}",
            raw="",
        )

    parsed = _parse_json(response.text)
    if not parsed or "class" not in parsed:
        log.warning("triage: could not parse JSON: %r", response.text[:200])
        return TriageResult(
            cls=TriageClass.INFORMATIONAL,
            reason="triage_parse_error",
            raw=response.text,
        )

    raw_cls = str(parsed.get("class", "")).lower().strip()
    try:
        cls = TriageClass(raw_cls)
    except ValueError:
        log.warning("triage: unknown class %r", raw_cls)
        cls = TriageClass.INFORMATIONAL

    return TriageResult(
        cls=cls,
        reason=str(parsed.get("reason", ""))[:300],
        raw=response.text,
    )


def fallback_answer(cls: TriageClass) -> str | None:
    return FALLBACKS.get(cls)
