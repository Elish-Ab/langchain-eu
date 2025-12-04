from pydantic import BaseModel
from typing import List, Optional

class JobOutputSchema(BaseModel):
    company_name: str
    job_category: str
    benefits: List[str]
    job_tags: List[str]
    job_type: List[str]
    job_region: List[str]
    salary: str
    company_website: Optional[str] = ""  # LLM can fill if it sees it
