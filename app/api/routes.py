import time
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import List

from app.api.schemas import JobItem
from app.normalizer import normalize_job_post

log = logging.getLogger("job-normalizer")
router = APIRouter()

@router.post("/normalize-job")
def normalize_jobs(req: List[JobItem], request: Request):
    t0 = time.time()
    try:
        results = [normalize_job_post(job.model_dump()) for job in req]
        log.info("Normalized %d jobs in %.1fms", len(results), (time.time() - t0) * 1000)
        return results
    except Exception as e:
        log.exception("Error during normalization: %s", e)
        return JSONResponse(status_code=500, content={"detail": "internal_error"})
