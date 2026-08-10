"""
Central configuration for the backend.

Kept intentionally small during Phase 1. Values here will grow as later
phases introduce the language model, feature extraction, and scoring
pipeline (see docs/decisions/ for the reasoning behind each addition).
"""

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Detector for Admissions Essays"
    api_prefix: str = "/api"

    # Input limits (documented rationale: docs/architecture.md, Performance section)
    max_essay_chars: int = 20_000
    min_essay_chars: int = 1


settings = Settings()
