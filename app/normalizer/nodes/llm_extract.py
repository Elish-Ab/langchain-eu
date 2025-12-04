import os
import json
import backoff
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from app.normalizer.state import JobState
from app.normalizer.llm.prompt import SYSTEM, USER_TMPL, build_prompt
from app.normalizer.llm.model import _model
from app.normalizer.llm.schema import JobOutputSchema
from app.normalizer.utils.validation import coerce_list

def merge_results(primary: JobOutputSchema, fallback: Optional[JobOutputSchema]) -> JobOutputSchema:
    if fallback is None:
        return primary

    def first_non_empty(a, b) -> str:
        return (a or "").strip() if (a or "").strip() else (b or "").strip()

    return JobOutputSchema(
        company_name=first_non_empty(primary.company_name, fallback.company_name),
        company_website=first_non_empty(getattr(primary, "company_website", ""), getattr(fallback, "company_website", "")),
        job_category=first_non_empty(primary.job_category, fallback.job_category),
        benefits=coerce_list(primary.benefits) or coerce_list(fallback.benefits),
        job_tags=coerce_list(primary.job_tags) or coerce_list(fallback.job_tags),
        job_type=coerce_list(primary.job_type) or coerce_list(fallback.job_type),
        job_region=coerce_list(primary.job_region) or coerce_list(fallback.job_region),
        salary=first_non_empty(primary.salary, fallback.salary),
    )

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def node_llm_extract(state: JobState) -> JobState:
    payload = state["payload"]

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER_TMPL)])
    primary_chain = prompt | _model(os.getenv("PRIMARY_MODEL"))
    fallback_chain = prompt | _model(os.getenv("FALLBACK_MODEL", "gpt-4o-mini"))

    result_primary: Optional[JobOutputSchema] = None
    try:
        result_primary = primary_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
    except Exception:
        result_primary = None

    if result_primary is None:
        try:
            result_primary = fallback_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
        except Exception:
            result_primary = JobOutputSchema(
                company_name="", company_website="", job_category="", benefits=[], job_tags=[],
                job_type=[], job_region=[], salary=""
            )

    needs_fallback = any([
        not (result_primary.company_name or "").strip(),
        not (result_primary.job_category or "").strip(),
        not coerce_list(result_primary.job_region),
        not coerce_list(result_primary.benefits),
        not coerce_list(result_primary.job_tags),
        not coerce_list(result_primary.job_type),
        not (result_primary.salary or "").strip(),
    ])

    result_merged = result_primary
    result_fallback = None
    if needs_fallback:
        try:
            result_fallback = fallback_chain.invoke(build_prompt(json.dumps(payload, ensure_ascii=False)))
        except Exception:
            result_fallback = None
        result_merged = merge_results(result_primary, result_fallback)

    return {
        **state,
        "llm_primary": result_primary,
        "llm_fallback": result_fallback,
        "llm_merged": result_merged,
    }
