"""
FastAPI application entrypoint.

Phase 1 scope only: application wiring, CORS for local frontend dev, and a
health check. The /api/analyze endpoint and its supporting services
(sentence segmentation, feature extraction, language model, scoring) are
introduced in later phases per docs/project-status.md.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title=settings.app_name)

# Local Next.js dev server. Tightened before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
