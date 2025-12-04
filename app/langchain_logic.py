# app/langchain_logic.py
import os
import json
from typing import List, Optional, Dict, Any, Iterable

import backoff #type: ignore
from bs4 import BeautifulSoup
from langchain_core.prompts import ChatPromptTemplate #type: ignore
from langchain_openai import ChatOpenAI #type: ignore
from pydantic import BaseModel #type: ignore
import re

# ──────────────────────────────────────────────────────────────────────────────
# Controlled vocabularies (closed sets)
# ──────────────────────────────────────────────────────────────────────────────

JOB_CATEGORIES = [
    "Admin & Operations","Customer Support","Data","Design","Engineering","Finance","Human Resources","IT","Legal","Marketing","Product","Sales","All Others"
]


JOB_TYPES = [
    "full-time", "Part Time", "Internship", "Freelance", "Temporary",
    "4 day week", "AI", "German", "Multilingual", "Bilingual",
    "jobs in crypto", "web3", "high salary"
]

# Job Tags whitelist (as provided)
JOB_TAGS_WHITELIST = [
    ".NET","1-3 years","3-5 years","5+ years","agile","AI","Android","Angular","ASP.NET","Bash","BigQuery",
    "Bilingual","Blockchain","C#","DevOps","SecOps","Django","docker","Drupal","Elixir","Entry Level","Flask",
    "Flutter","Git","Go","Golang","GraphQL","High-Salary","iOS","Java","Javascript","jobs in crypto","jQuery",
    "Machine Learning","MongoDB","MySQL","Next.js","Node","node.js","noSQL","PHP","PostgreSQL","Python","R",
    "Rails","React","react native","Reactjs","Redux","Rust","Scala","Snowflake","Solidity","Spark","SQL",
    "Swift","Tableau","Tailwind","Terraform","Typescript","Ubutu","vue","vue.js","web3","WordPress",
    "work from anywhere ","Visa support","Relocation support","company off-sites","home-office budget",
    "Fertility benefits","coworking budget","wellbeing allowance","professional development budget",
    "mental health support","parental leave","Health insurance","Unlimited Time Off","Childcare support",
    "Flexible Schedule","Equity","Kubernetes","Linux","Ruby","Ruby on Rails","high-salary"
]

# Job Benefits whitelist (as provided)
BENEFITS_WHITELIST = [
    "home-office budget","Fertility benefits","company retreats","4 day work week ",
    "coworking budget","wellbeing allowance","professional development allowance",
    "mental health support","parental leave","Health insurance","Unlimited Time Off",
    "Childcare support","Flexible Schedule","Equity / Stocks","work from anywhere policy"
]

# Region whitelist (as provided)
REGION_VALUES = [
    "Worldwide","EMEA","Africa","Ghana","Kenya","Egypt","South Africa","Europe","Armenia","Austria","Belgium",
    "Bulgaria","Croatia","Cyprus","Czechia","Denmark","Estonia","Finland","France","Germany","Greece","Hungary",
    "Iceland","Ireland","Italy","Latvia","Lithuania","Luxembourg","Macedonia","Malta","Netherlands","Norway",
    "Portugal","Poland","Romania","Serbia","Slovakia","Slovenia","Spain","Switzerland","Sweden","Turkey",
    "Ukraine","UK","Georgia","UAE","India","LATAM","Argentina","Brazil","Colombia","AMER","Canada","US",
    "Mexico","APAC","Singapore","Australia","Asia"
]

# ──────────────────────────────────────────────────────────────────────────────
# Prompt (ALL fields are extracted by the LLM)
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM = (
    "You extract structured job info and classify into CLOSED SETS. "
    "Return ONLY valid JSON for the provided schema.\n"
    "Guidelines:\n"
    "- company_name: exact employer/brand (plain text, no URL). If unknown, return empty string.\n"
    "- job_category: choose ONE from Job Categories or empty string if unclear (title has priority).\n"
    "- job_tags: choose ONLY items that EXACTLY match the Job Tags whitelist (verbatim strings).\n"
    "- benefits: choose ONLY items that EXACTLY match the Job Benefits whitelist (verbatim strings).\n"
    "- job_type: choose ONLY items from the Job Types whitelist; map synonyms from hints/description "
    "  (e.g., 'Full time'/'FT' → 'full-time'). Include multiple if explicitly present.\n"
    "- job_region: choose ONE OR MORE from Job Regions (if multiple regions are explicitly mentioned); otherwise empty string.map hints or text.\n"
    "- salary: return a normalized string based on the text: "
    "  • convert 'k' to full numbers with thousand separators (e.g., '90k' → '90,000'); "
    "  • keep the currency symbol/code; "
    "  • ranges as '£90,000–£120,000'; "
    "  • if the text is a lower bound (e.g., 'from £90k'), format as '£90,000+'; "
    "  • drop non-monetary add-ons like '+ bonus' or 'plus benefits'. If unknown, return empty string.\n"
    "Return JSON with keys: company_name, job_category, benefits[], job_tags[], job_type[], job_region, salary."
)

USER_TMPL = """INPUT (free text + hints):
{job_json}

CONTROLLED LISTS
- Job Categories: {job_categories}
- Job Types: {job_types}
- Job Tags: {job_tags}
- Job Benefits: {benefits}
- Job Regions: {regions}
"""

class JobOutputSchema(BaseModel):
    company_name: str
    job_category: str
    benefits: List[str]
    job_tags: List[str]
    job_type: List[str]
    job_region: List[str]
    salary: str

def _model(model_name: Optional[str] = None):
    model_id = model_name or os.getenv("PRIMARY_MODEL", "gpt-4o")
    return ChatOpenAI(model=model_id, temperature=0).with_structured_output(JobOutputSchema)

def build_prompt(job_json: str) -> Dict[str, Any]:
    return {
        "job_json": job_json,
        "job_categories": JOB_CATEGORIES,
        "job_types": JOB_TYPES,
        "job_tags": JOB_TAGS_WHITELIST,
        "benefits": BENEFITS_WHITELIST,
        "regions": REGION_VALUES,
    }

# ──────────────────────────────────────────────────────────────────────────────
# Utilities (no extraction heuristics; only formatting/validation)
# ──────────────────────────────────────────────────────────────────────────────

def strip_html(html: Optional[str]) -> str:
    if not html:
        return ""
    return " ".join(BeautifulSoup(html, "html.parser").get_text().split()).strip()

def _unique_keep_order(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for x in items or []:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def _validate_one(value: str, allowed: List[str]) -> str:
    return value if value in allowed else ""

def _validate_many(values: Iterable[str], allowed: List[str]) -> List[str]:
    allowed_set = set(allowed)
    return [v for v in _unique_keep_order(values or []) if v in allowed_set]

def _normalize_company_shape(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    # very light normalization only (no guessing/extraction)
    n = n.replace("-dot-", ".").replace(" dot ", ".").replace(" dot-", ".")
    return n[:1].upper() + n[1:]

def _company_is_valid(name: str) -> bool:
    """
    Basic sanity for company_name without 'extracting':
    - non-empty, <= 100 chars
    - contains at least one letter
    - does not look like a sentence fragment (endswith common verbs/punctuation)
    """
    if not name: return False
    n = name.strip()
    if not n or len(n) > 100: return False
    if not re.search(r"[A-Za-z]", n): return False
    bad_endings = (" are", " is", " we", " hiring", " expanding", " growing", ":", ";")
    if any(n.lower().endswith(b) for b in bad_endings): return False
    return True

def _coerce_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    if isinstance(x, str) and x.strip():
        return [x.strip()]
    return []

def _merge_results(primary: JobOutputSchema, fallback: Optional[JobOutputSchema]) -> JobOutputSchema:
    """
    Per-field merge: prefer primary; if empty, use fallback's value.
    Validation happens later.
    """
    if fallback is None:
        return primary

    def first_non_empty(a, b) -> str:
        return (a or "").strip() if (a or "").strip() else (b or "").strip()

    return JobOutputSchema(
    company_name=first_non_empty(primary.company_name, fallback.company_name),
    job_category=first_non_empty(primary.job_category, fallback.job_category),
    benefits=_coerce_list(primary.benefits) or _coerce_list(fallback.benefits),
    job_tags=_coerce_list(primary.job_tags) or _coerce_list(fallback.job_tags),
    job_type=_coerce_list(primary.job_type) or _coerce_list(fallback.job_type),
    job_region=_coerce_list(primary.job_region) or _coerce_list(fallback.job_region), 
    salary=first_non_empty(primary.salary, fallback.salary),
)


# ──────────────────────────────────────────────────────────────────────────────
# Salary → "high salary" post-processing (LLM output only) — USD/EUR/GBP
# ──────────────────────────────────────────────────────────────────────────────

ALLOWED_HIGH_SALARY_CURRENCIES = {"USD", "EUR", "GBP"}

_CURRENCY_MAP = {
    "$": "USD", "USD": "USD", "usd": "USD",
    "€": "EUR", "EUR": "EUR", "eur": "EUR",
    "£": "GBP", "GBP": "GBP", "gbp": "GBP",
}

_NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+|\d{5,}")  # e.g., 90,000 or 120000

def _min_amount_from_llm_salary(salary: str) -> Optional[int]:
    """
    Parse the LLM's normalized salary string to get the MINIMUM numeric amount
    when currency ∈ ALLOWED_HIGH_SALARY_CURRENCIES. Returns an int or None.
    Examples:
      "$120,000–$150,000" → 120000
      "€100,000+" → 100000
      "GBP 110,000" → 110000
      "£200,000+" → 200000
    """
    if not salary:
        return None
    s = salary.strip()

    # Currency before number
    cur_before = re.search(r"(USD|EUR|GBP|\$|€|£)\s*(" + _NUM_RE.pattern + ")", s, flags=re.I)
    if cur_before:
        cur_raw, num_raw = cur_before.group(1), cur_before.group(2)
        cur = _CURRENCY_MAP.get(cur_raw, None)
        if cur in ALLOWED_HIGH_SALARY_CURRENCIES:
            return int(num_raw.replace(",", ""))

    # Number before currency
    num_after = re.search(r"(" + _NUM_RE.pattern + r")\s*(USD|EUR|GBP|\$|€|£)", s, flags=re.I)
    if num_after:
        num_raw, cur_raw = num_after.group(1), num_after.group(2)
        cur = _CURRENCY_MAP.get(cur_raw, None)
        if cur in ALLOWED_HIGH_SALARY_CURRENCIES:
            return int(num_raw.replace(",", ""))

    return None

# ──────────────────────────────────────────────────────────────────────────────
# Core
# ──────────────────────────────────────────────────────────────────────────────
@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def extract_job_info(job_dict: dict) -> Dict[str, Any]:
    """
    All fields are extracted by the LLM. Python just orchestrates:
    - call primary; if any important fields are empty, call fallback
    - merge per-field (primary preferred; fallback fills gaps)
    - validate against closed sets
    - company_name must be valid; if both models fail, use provided input
    - add 'high salary' to job_type iff LLM salary >= 100000 and currency is USD/EUR/GBP
    """
    # ─────────────────────────────────────────────────────────────
    # Preprocess input fields safely (handle both str & list)
    # ─────────────────────────────────────────────────────────────
    full_text = strip_html(job_dict.get("job_description", ""))
    title = (job_dict.get("job_title") or "").strip()
    salary_field = (job_dict.get("salary") or "").strip()  # hint to the LLM

    # Handle job_region (can be str or list)
    _job_region_raw = job_dict.get("job_region", "")
    if isinstance(_job_region_raw, list):
        job_region_hint = ", ".join([str(r).strip() for r in _job_region_raw if str(r).strip()])
    else:
        job_region_hint = str(_job_region_raw).strip()

    # Handle job_type (can be str or list)
    _job_type_raw = job_dict.get("job_type", "")
    if isinstance(_job_type_raw, list):
        job_type_hint = ", ".join([str(t).strip() for t in _job_type_raw if str(t).strip()])
    else:
        job_type_hint = str(_job_type_raw).strip()

    provided_company = (job_dict.get("company_name") or "").strip()

    payload = {
        "title": title,
        "description": full_text,
        "salary_field": salary_field,
        "job_region_hint": job_region_hint,
        "job_type_hint": job_type_hint,
        "provided_company_field": provided_company,  # context only
    }

    # ─────────────────────────────────────────────────────────────
    # Build prompt and model chains
    # ─────────────────────────────────────────────────────────────
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER_TMPL)])
    primary_chain = prompt | _model(os.getenv("PRIMARY_MODEL"))
    fallback_chain = prompt | _model(os.getenv("FALLBACK_MODEL", "gpt-4o-mini"))

    result_primary: Optional[JobOutputSchema] = None
    try:
        result_primary = primary_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
    except Exception:
        try:
            result_primary = fallback_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
        except Exception:
            result_primary = JobOutputSchema(
                company_name="", job_category="", benefits=[], job_tags=[],
                job_type=[], job_region=[], salary=""
            )

    # ─────────────────────────────────────────────────────────────
    # Fallback gap fill if needed
    # ─────────────────────────────────────────────────────────────
    needs_fallback = any([
        not (result_primary.company_name or "").strip(),
        not (result_primary.job_category or "").strip(),
        not _coerce_list(result_primary.job_region),  # ✅ FIXED: no .strip()
        not _coerce_list(result_primary.benefits),
        not _coerce_list(result_primary.job_tags),
        not _coerce_list(result_primary.job_type),
        not (result_primary.salary or "").strip(),
    ])

    result_merged = result_primary
    if needs_fallback:
        try:
            result_fallback = fallback_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
        except Exception:
            result_fallback = None
        result_merged = _merge_results(result_primary, result_fallback)

    # ─────────────────────────────────────────────────────────────
    # Company normalization and fallback
    # ─────────────────────────────────────────────────────────────
    company_final = (result_merged.company_name or "").strip()
    if not _company_is_valid(company_final):
        company_final = provided_company.strip()
    company_final = _normalize_company_shape(company_final)

    # ─────────────────────────────────────────────────────────────
    # Validate against closed sets (multi-region support)
    # ─────────────────────────────────────────────────────────────
    job_category_final = _validate_one((result_merged.job_category or "").strip(), JOB_CATEGORIES)
    benefits_final = _validate_many(_coerce_list(result_merged.benefits), BENEFITS_WHITELIST)
    job_tags_final = _validate_many(_coerce_list(result_merged.job_tags), JOB_TAGS_WHITELIST)
    job_type_final = _validate_many(_coerce_list(result_merged.job_type), JOB_TYPES)
    job_region_final = _validate_many(_coerce_list(result_merged.job_region), REGION_VALUES)

    # ─────────────────────────────────────────────────────────────
    # Salary post-processing
    # ─────────────────────────────────────────────────────────────
    salary_final = (result_merged.salary or "").strip()

    # Add "high salary" if min >= 100k in USD/EUR/GBP
    min_amt = _min_amount_from_llm_salary(salary_final)
    if min_amt is not None and min_amt >= 100000 and "high salary" not in job_type_final:
        job_type_final.append("high salary")

    # ─────────────────────────────────────────────────────────────
    # Return normalized structured result
    # ─────────────────────────────────────────────────────────────
    return {
        "company_name": company_final,
        "job_category": job_category_final,
        "job_tags": ", ".join(job_tags_final) if job_tags_final else "",
        "benefits": ", ".join(benefits_final) if benefits_final else "",
        "job_type": ", ".join(job_type_final) if job_type_final else "",
        "job_region": ", ".join(job_region_final) if job_region_final else "",
        "salary": salary_final,
    }


def normalize_job_post(job: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return extract_job_info(job)
    except Exception as e:
        return {
            "company_name": (job.get("company_name") or "").strip(),  # last-resort echo
            "job_category": "",
            "job_tags": "",
            "benefits": "",
            "job_type": "",
            "job_region": "",
            "salary": "",
            "error": str(e)
        }
