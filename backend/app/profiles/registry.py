from .base import ProfileConfig
from .patient import PATIENT
from .clinician import CLINICIAN

_PROFILES: dict[str, ProfileConfig] = {
    "patient": PATIENT,
    "clinician": CLINICIAN,
}


def get_profile(name: str) -> ProfileConfig:
    if name not in _PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    return _PROFILES[name]
