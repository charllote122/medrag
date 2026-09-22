from enum import Enum
from pydantic import BaseModel


class TriageMode(str, Enum):
    OFF = "off"
    REQUIRED = "required"


class ProfileConfig(BaseModel):
    name: str
    triage_mode: TriageMode
    allow_personalization: bool
    citation_threshold: float
    drop_answer_on_unsupported: bool
    readability_target: int | None
    mandatory_escalation_footer: bool
    system_prompt: str
