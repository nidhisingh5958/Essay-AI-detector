"""
FastAPI application entrypoint.

Phase E adds POST /api/analyze (app.api.analyze), backed by the frozen
Phase B/C/D detection pipeline. This module only wires the app together
(routing, CORS, startup) -- no detection logic lives here.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load both frozen model artifacts once, at process startup, not on
    the first user request (Phase E item 15) -- and fail loudly here if
    an artifact is missing/corrupt (Phase B's standing rule: never serve
    requests with a partially-loaded detector). If this raises, the
    application does not start."""
    from app.services.detector import _load_essay_artifact, _load_sentence_artifact

    _load_essay_artifact()
    _load_sentence_artifact()
    logger.info("Detector artifacts loaded and ready.")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Local Next.js dev server. Tightened before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/api/health")
def health() -> dict:
    """Cheap readiness check only -- never runs model inference (Phase E
    item 20). `detector_loaded` reflects whether the startup preload
    above already ran; this is a free, in-memory check (an already-
    populated lru_cache), not a new inference call."""
    from app.services.detector import _load_essay_artifact, _load_sentence_artifact

    detector_loaded = bool(_load_essay_artifact.cache_info().currsize) and bool(_load_sentence_artifact.cache_info().currsize)
    return {"status": "ok", "app": settings.app_name, "detector_loaded": detector_loaded}
