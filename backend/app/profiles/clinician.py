from .base import ProfileConfig, TriageMode

SYSTEM_PROMPT = """You are a clinical reference assistant.
Answer using ONLY the provided guideline excerpts. Cite every claim with [n]
including section reference. Technical language is appropriate.
If the answer isn't in the excerpts, say so."""

CLINICIAN = ProfileConfig(
    name="clinician",
    triage_mode=TriageMode.OFF,
    allow_personalization=False,
    citation_threshold=0.70,
    drop_answer_on_unsupported=False,
    readability_target=None,
    mandatory_escalation_footer=False,
    system_prompt=SYSTEM_PROMPT,
)
