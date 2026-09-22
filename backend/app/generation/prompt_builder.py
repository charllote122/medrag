"""Build profile-aware prompts from retrieved chunks.

The retrieval is shared across profiles. The prompt contract is not.
This file is where patient vs clinician differ in how the LLM is asked
to write the answer.
"""

from ..profiles.base import ProfileConfig
from ..retrieval.schemas import RetrievedChunk


PATIENT_SYSTEM = """You are a health information assistant for the general public.

Rules:
1. Answer ONLY using the numbered source excerpts provided.
2. Every factual sentence MUST end with a citation like [1] or [2].
3. Use plain language — imagine you're explaining to a friend with no medical training.
4. NEVER diagnose the user. NEVER recommend a specific treatment for them.
5. If the excerpts don't answer the question, say so plainly.
6. End with a short "When to seek care" line, even if the excerpts don't mention it.
7. Do not use medical jargon unless the source uses it and you explain it."""


CLINICIAN_SYSTEM = """You are a clinical reference assistant for healthcare professionals.

Rules:
1. Answer ONLY using the numbered source excerpts provided.
2. Every factual sentence MUST end with a citation like [1] or [2].
3. Technical language is appropriate.
4. Where the source gives a recommendation grade, dosage, or threshold, include it.
5. If the excerpts do not answer the question, say ONLY:
   "The provided excerpts do not contain this information."
   Do NOT add related content or outside knowledge. Stop.
6. Do NOT add information from your training data. If it is not in the
   excerpts, it does not exist for this answer.
7. Be concise. This is a lookup tool, not an essay."""


def _system_for(profile: ProfileConfig) -> str:
    return PATIENT_SYSTEM if profile.name == "patient" else CLINICIAN_SYSTEM


def _format_sources(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] {c.source_org} — {c.source_title} — section: {c.section}\n"
            f"{c.text}\n"
        )
    return "\n".join(lines)


def build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    profile: ProfileConfig,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt)."""
    system = _system_for(profile)
    sources = _format_sources(chunks)
    user = (
        f"Question: {question}\n\n"
        f"Source excerpts:\n\n{sources}\n"
        f"Answer the question using only the excerpts above. "
        f"Cite each sentence with [n]."
    )
    return system, user
