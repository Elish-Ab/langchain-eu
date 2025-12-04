from .graph import job_graph

def normalize_job_post(job: dict) -> dict:
    """
    Public entrypoint used by FastAPI.
    """
    return job_graph.invoke({"job_dict": job})
