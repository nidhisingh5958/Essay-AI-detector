import pytest

from app.config import settings
from app.services.validation import EssayValidationError, validate_essay_text


def test_empty_string_is_rejected():
    with pytest.raises(EssayValidationError):
        validate_essay_text("")


def test_whitespace_only_is_rejected():
    with pytest.raises(EssayValidationError):
        validate_essay_text("   \n\t  ")


def test_essay_over_max_length_is_rejected():
    too_long = "a" * (settings.max_essay_chars + 1)
    with pytest.raises(EssayValidationError):
        validate_essay_text(too_long)


def test_essay_at_max_length_is_accepted():
    exactly_max = "a" * settings.max_essay_chars
    validate_essay_text(exactly_max)  # should not raise


def test_short_valid_essay_is_accepted():
    validate_essay_text("A short essay.")  # should not raise
