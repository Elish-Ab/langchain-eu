import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.langchain_logic import normalize_job_post



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger("job-normalizer")

app = FastAPI(title="Job Normalizer API", version="1.0")

class JobItem(BaseModel):
    location: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_linkedin: Optional[str] = None
    company_logo: Optional[str] = None
    job_region: Optional[str] = None
    job_tags: Optional[str] = None
    job_title: Optional[str] = None
    job_description: str
    focus_keyword: Optional[str] = None
    application_url: Optional[str] = None
    salary: Optional[str] = None
    benefits: Optional[str] = None
    job_category: Optional[str] = None
    job_type: Optional[str] = None
    published_within_5_days: Optional[str] = None

@app.get("/")
def health_check():
    return {"message": "this is langchain api"}
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/normalize-job")
def normalize_jobs(req: List[JobItem], request: Request):
    t0 = time.time()
    try:
        results = [normalize_job_post(job.model_dump()) for job in req]
        log.info("Normalized %d jobs in %.1fms", len(results), (time.time() - t0) * 1000)
        return results
    except Exception as e:
        log.exception("Error during normalization: %s", e)
        return JSONResponse(status_code=500, content={"detail": "internal_error"})

@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "internal_server_error"})
