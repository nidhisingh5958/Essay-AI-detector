"""
Input validation for essay text.

Treats pasted essay text as untrusted input (Section 23 of the project
brief): it is validated for length only here. It is never interpreted as
HTML/markup by this backend or the frontend (React escapes text content by
default), so no HTML-stripping is performed — stripping would risk
destroying legitimate essay content (e.g. a student writing about "the
<3 minute mile").
"""

from app.config import settings


class EssayValidationError(ValueError):
    """Raised when essay text fails basic validation."""


def validate_essay_text(text: str) -> None:
    if len(text.strip()) < settings.min_essay_chars:
        raise EssayValidationError("Essay text is empty.")

    if len(text) > settings.max_essay_chars:
        raise EssayValidationError(
            f"Essay exceeds the maximum supported length of "
            f"{settings.max_essay_chars} characters "
            f"(received {len(text)})."
        )
