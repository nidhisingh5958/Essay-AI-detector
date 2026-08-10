import unicodedata

from app.services.text_normalizer import normalize_text


def test_normalizes_crlf_and_cr_line_endings():
    assert normalize_text("line one\r\nline two\rline three") == "line one\nline two\nline three"


def test_strips_control_characters_but_keeps_newline_and_tab():
    text = "hello\x00world\x07\n\ttab kept"
    assert normalize_text(text) == "helloworld\n\ttab kept"


def test_preserves_ordinary_punctuation_and_smart_quotes():
    # Curly quotes/em-dashes are candidate features (Section 6B) — must not
    # be silently rewritten to ASCII equivalents.
    text = "She said, “I’m ready”—and meant it."
    assert normalize_text(text) == text


def test_unicode_nfc_normalization_canonicalizes_combining_characters():
    composed = "café"  # precomposed 'e with acute accent'
    decomposed = unicodedata.normalize("NFD", composed)  # 'e' + combining acute accent
    assert decomposed != composed  # sanity check the fixture actually decomposed
    assert normalize_text(decomposed) == composed


def test_empty_string_stays_empty():
    assert normalize_text("") == ""
