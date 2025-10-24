import os
import json
import re
from typing import List, Optional, Dict, Any

import backoff
from bs4 import BeautifulSoup
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# Controlled vocabularies
JOB_CATEGORIES = ["Engineering", "Marketing", "Product", "Design", "Operations", "Sales", "Game Launcher"]
JOB_TYPES = ["full-time", "Part Time", "Internship", "Freelance", "Temporary", "4 day week", "AI", "German", "Multilingual", "Bilingual", "jobs in crypto", "web3", "high salary"]
BENEFITS = ["Flexible working hours", "Health insurance", "Remote work", "Stock options", "4 day week", "Annual learning stipend"]
REGION_VALUES = ["Europe", "EMEA", "Worldwide"]

# Prompt templates
SYSTEM = (
    "You classify a job post into CLOSED SETS and extract the employer name.\n"
    "Return ONLY valid JSON for the provided schema.\n"
    "- company_name: exact employer/brand.\n"
    "- job_category: one from list (title priority).\n"
    "- benefits & job_tags: exact phrases from whitelist.\n"
    "- job_type: only from list. Add 'high salary' if comp >=100k.\n"
    "- job_region: match keywords or infer from countries.\n"
    "Return: JSON with keys: company_name, job_category, benefits[], job_tags[], job_type[], job_region (or null)."
)

USER_TMPL = """INPUT:
{job_json}

CONTROLLED LISTS
- Job Categories: {job_categories}
- Job Types: {job_types}
- Benefits (for tags too): {benefits}
- Job Regions: {regions}
"""

EU_EEA_UK_CH_NO_IS_LI = {"Hungary", "Germany", "France", "UK", "Sweden", "Netherlands", "Norway", "Ireland"}
MIDDLE_EAST_AFRICA = {"UAE", "South Africa", "Nigeria", "Egypt", "Kenya"}

class JobOutputSchema(BaseModel):
    company_name: str
    job_category: str
    benefits: List[str]
    job_tags: List[str]
    job_type: List[str]
    job_region: Optional[str]

def _model(model_name: Optional[str] = None):
    model_id = model_name or os.getenv("PRIMARY_MODEL", "gpt-4o")
    return ChatOpenAI(model=model_id, temperature=0).with_structured_output(JobOutputSchema)

def build_prompt(job_json: str) -> Dict[str, Any]:
    return {
        "job_json": job_json,
        "job_categories": JOB_CATEGORIES,
        "job_types": JOB_TYPES,
        "benefits": BENEFITS,
        "regions": REGION_VALUES,
    }

def strip_html(html: Optional[str]) -> str:
    if not html:
        return ""
    return re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text()).strip()

def detect_high_salary(text: str) -> bool:
    if re.search(r"(?i)(\$|USD|EUR|\u20ac|GBP|\u00a3)?\s*1\s*0{2}\s*k", text):
        return True
    nums = [int(n.replace(",", "")) for n in re.findall(r"(?i)(\d{3,6})", text) if n.isdigit()]
    return any(n >= 100000 for n in nums)

def find_phrases(text: str, phrases: List[str]) -> List[str]:
    found = []
    for p in phrases:
        if re.search(rf"(?i)(?<!\w){re.escape(p)}(?!\w)", text):
            found.append(p)
    return list(dict.fromkeys(found))

def region_from_text(job_region: str, full_text: str) -> Optional[str]:
    t = full_text.lower()
    countries = set(job_region.split(", ")) if job_region else set()
    if "worldwide" in t or "global" in t:
        return "Worldwide"
    if countries & EU_EEA_UK_CH_NO_IS_LI:
        return "Europe"
    if countries & MIDDLE_EAST_AFRICA or "emea" in t:
        return "EMEA"
    return None

def extract_company_name_heuristic(text: str) -> Optional[str]:
    m = re.search(r"(?i)join (.*?) | work at (.*?) | ([A-Z][A-Za-z]+) is a ", text)
    if m:
        return m.group(1) or m.group(2) or m.group(3)
    m = re.search(r"@([a-z0-9-]+)\.", text)
    if m:
        return m.group(1).capitalize()
    return None

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def extract_job_info(job_dict: dict) -> dict:
    full_text = strip_html(job_dict.get("job_description", ""))
    title = job_dict.get("job_title", "")
    salary = job_dict.get("salary", "")
    job_region = job_dict.get("job_region", "")

    payload = {
        "title": title,
        "description": full_text,
        "salary": salary,
        "job_region": job_region,
    }

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER_TMPL)])
    chain = prompt | _model(os.getenv("PRIMARY_MODEL"))

    try:
        result = chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
        result_dict = result.dict()
    except Exception:
        # Retry with fallback model
        fallback_chain = prompt | _model(os.getenv("FALLBACK_MODEL", "gpt-4o"))
        try:
            result = fallback_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
            result_dict = result.dict()
        except Exception:
            result_dict = {
                "company_name": extract_company_name_heuristic(full_text),
                "job_category": "Engineering",
                "benefits": find_phrases(full_text, BENEFITS),
                "job_tags": find_phrases(full_text, BENEFITS),
                "job_type": ["full-time"],
                "job_region": region_from_text(job_region, full_text),
            }

    if detect_high_salary(full_text) and "high salary" not in result_dict["job_type"]:
        result_dict["job_type"].append("high salary")

    return {
        "company_name": result_dict["company_name"],
        "job_category": result_dict["job_category"],
        "job_tags": ", ".join(result_dict["job_tags"]),
        "benefits": ", ".join(result_dict["benefits"]),
        "job_type": ", ".join(result_dict["job_type"]),
        "job_region": result_dict["job_region"] or None
    }

def normalize_job_post(job: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return extract_job_info(job)
    except Exception as e:
        return {
            "company_name": None,
            "job_category": None,
            "job_tags": "",
            "benefits": "",
            "job_type": "",
            "job_region": None,
            "error": str(e)
        }
