def normalize_job_post(job: dict) -> dict:
    """
    Public entrypoint used by FastAPI.
    """
    from .graph import job_graph

    return job_graph.invoke({"job_dict": job})
