"""Citation verifier.

Checks that each sentence's [n] citations point at chunks that actually
share vocabulary with the sentence. This is a cheap first-line check,
not a semantic entailment model — but it catches gross citation errors
(LLM citing [5] for a claim only in [1]).

Returns a structured result with unsupported sentences flagged.
"""

import re
from dataclasses import dataclass, field

from ..retrieval.schemas import RetrievedChunk


# Sentences are split on . ! ? followed by whitespace + capital letter
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
CITATION = re.compile(r"\[(\d+)\]")
WORD = re.compile(r"[a-zA-Z]{3,}")


@dataclass
class Verification:
    supported: bool
    flagged: list[str] = field(default_factory=list)
    coverage: float = 0.0    # fraction of sentences with all citations supported


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in WORD.findall(text)}


def _sentence_supported(
    sentence: str, citations: list[int], chunks: list[RetrievedChunk]
) -> bool:
    """A sentence is supported if every cited chunk shares >=2 content words."""
    sent_kw = _keywords(sentence)
    if not sent_kw:
        return True  # nothing to check (very short sentence)

    for cite in citations:
        if cite < 1 or cite > len(chunks):
            return False
        chunk_kw = _keywords(chunks[cite - 1].text)
        overlap = sent_kw & chunk_kw
        if len(overlap) < 2:
            return False
    return True


def verify(answer: str, chunks: list[RetrievedChunk]) -> Verification:
    """Check every cited sentence against the chunk it cites."""
    sentences = SENT_SPLIT.split(answer.strip())
    flagged: list[str] = []
    total_cited = 0
    supported_cited = 0

    for sent in sentences:
        cites = [int(m) for m in CITATION.findall(sent)]
        if not cites:
            continue
        total_cited += 1
        if _sentence_supported(sent, cites, chunks):
            supported_cited += 1
        else:
            flagged.append(sent.strip())

    coverage = supported_cited / total_cited if total_cited else 1.0
    return Verification(
        supported=len(flagged) == 0,
        flagged=flagged,
        coverage=coverage,
    )


def strip_unsupported(answer: str, flagged: list[str]) -> str:
    """Remove flagged sentences from the answer."""
    for sent in flagged:
        answer = answer.replace(sent, "").strip()
    answer = re.sub(r"\s{2,}", " ", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer)
    return answer.strip()
