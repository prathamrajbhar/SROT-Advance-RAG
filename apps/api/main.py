from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await ensure_bucket_exists()
    except Exception:
        pass
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://srot.dev/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc),
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
