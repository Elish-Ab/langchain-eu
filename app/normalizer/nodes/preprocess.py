from app.normalizer.state import JobState
from app.normalizer.utils.text import strip_html

def node_preprocess(state: JobState) -> JobState:
    job_dict = state["job_dict"]

    full_text = strip_html(job_dict.get("job_description", ""))
    title = (job_dict.get("job_title") or "").strip()
    salary_field = (job_dict.get("salary") or "").strip()

    _job_region_raw = job_dict.get("job_region", "")
    job_region_hint = ", ".join(map(str, _job_region_raw)) if isinstance(_job_region_raw, list) else str(_job_region_raw).strip()

    _job_type_raw = job_dict.get("job_type", "")
    job_type_hint = ", ".join(map(str, _job_type_raw)) if isinstance(_job_type_raw, list) else str(_job_type_raw).strip()

    provided_company = (job_dict.get("company_name") or "").strip()

    payload = {
        "title": title,
        "description": full_text,
        "salary_field": salary_field,
        "job_region_hint": job_region_hint,
        "job_type_hint": job_type_hint,
        "provided_company_field": provided_company,
    }

    return {**state, "payload": payload}
