import importlib.util
import types
from pathlib import Path


_MODULE_PATH = Path(__file__).with_name("__init__.py")
_SPEC = importlib.util.spec_from_file_location("normalizer", _MODULE_PATH)
normalizer = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(normalizer)

normalize_job_post = normalizer.normalize_job_post


def test_normalize_job_post_strips_llm_fields():
    dummy_state = {
        "llm_primary": {"job_category": "Design"},
        "llm_fallback": {"job_category": "Design"},
        "llm_merged": {"job_category": "Design"},
        "normalized": {
            "company_name": "Dealfront",
            "job_category": "Design",
            "job_tags": "AI, company off-sites",
            "benefits": "company retreats, mental health support, Flexible Schedule",
            "job_type": "full-time",
            "job_region": "Europe",
            "salary": "",
        },
        "company_website": "https://www.dealfront.com",
        "needs_company_website_lookup": True,
        "experience_level": "senior",
    }

    dummy_graph = types.SimpleNamespace(invoke=lambda _: dummy_state)

    result = normalize_job_post({}, job_graph_override=dummy_graph)

    assert result == {
        "company_name": "Dealfront",
        "job_category": "Design",
        "job_tags": "AI, company off-sites",
        "benefits": "company retreats, mental health support, Flexible Schedule",
        "job_type": "full-time",
        "job_region": "Europe",
        "salary": "",
        "company_website": "https://www.dealfront.com",
        "experience_level": "senior",
    }
    assert "llm_primary" not in result
