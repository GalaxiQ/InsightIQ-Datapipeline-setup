import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.routes import schema, ingest, serve, transform, analysis

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

setup_logging()
logger = logging.getLogger("insightiq")

app = FastAPI(
    title="InsightIQ Platform",
    version="1.0.0",
    description="Multi-tenant ingestion + analytics + serving platform"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(serve, tags=["Serve"])
app.include_router(transform, prefix="/transform", tags=["Transform"])
app.include_router(analysis, prefix="/analysis", tags=["Analysis"])

@app.on_event("startup")
async def startup():
    logger.info("API started", extra={"env": settings.ENV})

@app.on_event("shutdown")
async def shutdown():
    logger.info("API stopped")

@app.get("/health")
async def health():
    return {"status": "ok"}
