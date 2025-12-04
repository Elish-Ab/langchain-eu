from app.normalizer.state import JobState
from typing import Dict, Any

def node_finalize(state: JobState) -> Dict[str, Any]:
    out = dict(state["normalized"])
    out["company_website"] = state.get("company_website", "")
    out["experience_level"] = state.get("experience_level", "")
    return out
