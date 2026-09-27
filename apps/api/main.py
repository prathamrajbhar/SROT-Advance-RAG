import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import get_settings
from core.logging import RequestTracingMiddleware, setup_logging
from core.redis import close_redis
from core.s3 import ensure_bucket_exists
from modules.admin.health import router as health_router
from modules.admin.router import router as admin_router
from modules.auth.router import router as auth_router
from modules.chat.router import router as chat_router
from modules.documents.router import router as documents_router
from modules.evaluation.router import router as eval_router
from modules.projects.router import router as projects_router

setup_logging()
settings = get_settings()
logger = logging.getLogger("srot.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await ensure_bucket_exists()
    except Exception as e:
        logger.warning(f"S3 bucket init deferred: {e}")
    yield
    await close_redis()


app = FastAPI(
    title="SROT Enterprise Multimodal RAG Platform",
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


# API Routers
api_v1_prefix = "/api/v1"
app.include_router(health_router, prefix=api_v1_prefix)
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(projects_router, prefix=api_v1_prefix)
app.include_router(documents_router, prefix=api_v1_prefix)
app.include_router(chat_router, prefix=api_v1_prefix)
app.include_router(eval_router, prefix=api_v1_prefix)
app.include_router(admin_router, prefix=api_v1_prefix)
