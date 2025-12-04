from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request

from app.api.routes import router
from app.core.logging import setup_logging

# Initialize logging
setup_logging()

app = FastAPI(title="Job Normalizer API", version="2.0-langgraph")

# Routes
app.include_router(router)

@app.get("/")
def root():
    return {"message": "this is langgraph api"}

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    # last-resort safety
    return JSONResponse(status_code=500, content={"detail": "internal_server_error"})
