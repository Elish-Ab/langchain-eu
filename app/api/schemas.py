from pydantic import BaseModel
from typing import Optional, List

class JobItem(BaseModel):
    location: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_linkedin: Optional[str] = None
    company_logo: Optional[str] = None
    job_region: Optional[str] = None
    job_tags: Optional[str] = None
    job_title: Optional[str] = None
    job_description: str
    focus_keyword: Optional[str] = None
    application_url: Optional[str] = None
    salary: Optional[str] = None
    benefits: Optional[str] = None
    job_category: Optional[str] = None
    job_type: Optional[str] = None
    published_within_5_days: Optional[str] = None

class NormalizedJobItem(BaseModel):
    company_name: str = ""
    company_website: str = ""
    company_linkedin: str = ""
    company_logo: str = ""
    job_category: str = ""
    job_tags: str = ""
    benefits: str = ""
    job_type: str = ""
    job_region: str = ""
    salary: str = ""
    experience_level: str = ""
