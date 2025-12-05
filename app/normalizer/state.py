# app/normalizer/state.py
from typing import TypedDict, Optional, Dict, Any
from app.normalizer.llm.schema import JobOutputSchema

class JobState(TypedDict, total=False):
    job_dict: Dict[str, Any]
    payload: Dict[str, Any]
    llm_primary: Optional[JobOutputSchema]
    llm_fallback: Optional[JobOutputSchema]
    llm_merged: JobOutputSchema
    normalized: Dict[str, Any]
    company_website: str
    needs_company_website_lookup: bool
    experience_level: str
