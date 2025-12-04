from typing import Any, Dict

def _finalize_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return the normalized payload only, stripping intermediate LLM details."""

    normalized = state.get("normalized") if isinstance(state, dict) else {}
    normalized_payload = dict(normalized or {})
    normalized_payload["company_website"] = state.get("company_website", "")
    normalized_payload["experience_level"] = state.get("experience_level", "")
    return normalized_payload


def normalize_job_post(job: dict, *, job_graph_override: Any | None = None) -> dict:

    """
    Public entrypoint used by FastAPI.
    """
    if job_graph_override is None:
        from .graph import job_graph

        job_graph_override = job_graph

    state = job_graph_override.invoke({"job_dict": job})
    return _finalize_response(state)
    """
    Public entrypoint used by FastAPI.
    """
    if job_graph_override is None:
        from .graph import job_graph

        job_graph_override = job_graph

    state = job_graph_override.invoke({"job_dict": job})
    return _finalize_response(state)
  
  
def normalize_job_post(job: dict) -> dict:
    """
    Public entrypoint used by FastAPI.
    """
    from .graph import job_graph

    return job_graph.invoke({"job_dict": job})

