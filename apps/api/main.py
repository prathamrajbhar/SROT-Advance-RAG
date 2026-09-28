import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import get_settings
from core.logging import RequestTracingMiddleware, setup_logging
from modules.health.router import router as health_router
from modules.onboarding.router import router as onboarding_router
from modules.documents import documents_router

setup_logging()
settings = get_settings()
logger = logging.getLogger("srot.api")



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        from core.s3 import get_s3_manager

        get_s3_manager().ensure_bucket_cors()
    except Exception as exc:
        logger.debug(f"S3 lifespan bucket check: {exc}")
    yield


app = FastAPI(
    title="SROT",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://srot.dev/errors/{exc.status_code}",
            "title": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "trace_id": trace_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    errors = exc.errors()
    clean_detail = "; ".join([f"{e.get('loc', ['body'])[-1]}: {e.get('msg', 'invalid')}" for e in errors])
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://srot.dev/errors/validation-error",
            "title": "Unprocessable Request Entity",
            "status": 422,
            "detail": clean_detail,
            "errors": errors,
            "trace_id": trace_id,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.error(f"Internal server error: {exc}", exc_info=True, extra={"trace_id": trace_id})
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://srot.dev/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An internal system error occurred. Our engineering team has logged this event.",
            "trace_id": trace_id,
        },
    )


app.include_router(health_router)  # /health & /ready at root
api_v1_prefix = "/api/v1"
app.include_router(health_router, prefix=api_v1_prefix)  # /api/v1/health & /api/v1/ready
app.include_router(onboarding_router, prefix=api_v1_prefix)  # /api/v1/onboarding/*
app.include_router(documents_router, prefix=api_v1_prefix)  # /api/v1/documents/*

