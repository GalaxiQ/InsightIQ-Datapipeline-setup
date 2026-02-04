import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.routes import schema, ingest, serve

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

setup_logging()
logger = logging.getLogger("insightiq-api")

app = FastAPI(
    title="InsightIQ Platform",
    version="1.0.0",
    description="Stateless ingestion + analytics + serving platform"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", extra={
        "path": request.url.path,
        "method": request.method
    })
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

# Routes
app.include_router(schema, prefix="/schema", tags=["Schema"])
app.include_router(ingest, prefix="/ingest", tags=["Ingest"])
app.include_router(serve, prefix="/serve", tags=["Serve"])

@app.on_event("startup")
async def startup():
    logger.info("API started", extra={"env": settings.ENV})

@app.on_event("shutdown")
async def shutdown():
    logger.info("API stopped")

@app.get("/health")
async def health():
    return {"status": "ok"}
