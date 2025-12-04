from app.normalizer.state import JobState
from app.normalizer.vocab.categories import JOB_CATEGORIES
from app.normalizer.vocab.tags import JOB_TAGS_WHITELIST
from app.normalizer.vocab.benefits import BENEFITS_WHITELIST
from app.normalizer.vocab.types import JOB_TYPES
from app.normalizer.vocab.regions import REGION_VALUES

from app.normalizer.utils.company import company_is_valid, normalize_company_shape
from app.normalizer.utils.validation import validate_one, validate_many, coerce_list
from app.normalizer.utils.salary import min_amount_from_llm_salary

def node_validate_normalize(state: JobState) -> JobState:
    job_dict = state["job_dict"]
    llm_merged = state["llm_merged"]

    provided_company = (job_dict.get("company_name") or "").strip()

    company_final = (llm_merged.company_name or "").strip()
    if not company_is_valid(company_final):
        company_final = provided_company
    company_final = normalize_company_shape(company_final)

    job_category_final = validate_one((llm_merged.job_category or "").strip(), JOB_CATEGORIES)
    benefits_final = validate_many(coerce_list(llm_merged.benefits), BENEFITS_WHITELIST)
    job_tags_final = validate_many(coerce_list(llm_merged.job_tags), JOB_TAGS_WHITELIST)
    job_type_final = validate_many(coerce_list(llm_merged.job_type), JOB_TYPES)
    job_region_final = validate_many(coerce_list(llm_merged.job_region), REGION_VALUES)

    salary_final = (llm_merged.salary or "").strip()
    min_amt = min_amount_from_llm_salary(salary_final)
    if min_amt is not None and min_amt >= 100000 and "high salary" not in job_type_final:
        job_type_final.append("high salary")

    normalized = {
        "company_name": company_final,
        "job_category": job_category_final,
        "job_tags": ", ".join(job_tags_final) if job_tags_final else "",
        "benefits": ", ".join(benefits_final) if benefits_final else "",
        "job_type": ", ".join(job_type_final) if job_type_final else "",
        "job_region": ", ".join(job_region_final) if job_region_final else "",
        "salary": salary_final,
    }

    website_from_job = (job_dict.get("company_website") or "").strip()
    website_from_llm = (getattr(llm_merged, "company_website", "") or "").strip()

    website_initial = website_from_llm or website_from_job
    needs_lookup = not website_initial

    return {
        **state,
        "normalized": normalized,
        "company_website": website_initial,
        "needs_company_website_lookup": needs_lookup,
    }
