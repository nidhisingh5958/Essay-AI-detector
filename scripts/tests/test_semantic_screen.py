"""
Tests for semantic_screen.py. The classification logic is tested as pure
functions (fast, no model). extract_facts/check_fact_preservation/
embedding_similarity are tested for real against the actually-loaded
spaCy and sentence-transformers models -- both load in low single-digit
seconds, unlike qwen_generate.py's multi-GB model, so exercising them
directly here is cheap enough to be worth it (matches the pattern
already used for feature_extractor.py's spaCy-backed tests).
"""

from semantic_screen import (
    check_fact_preservation,
    classify_screen_label,
    embedding_similarity,
    extract_facts,
)


def test_fact_flagged_always_escalates_to_review_regardless_of_similarity():
    # Even a near-identical embedding similarity should not auto-pass if
    # a number/entity mismatch was found -- this is the case that catches
    # "one C" -> "two Cs"-style drift that embeddings alone miss.
    assert classify_screen_label(similarity=0.95, fact_flagged=True) == "needs_review"


def test_high_similarity_no_fact_flag_is_likely_preserved():
    assert classify_screen_label(similarity=0.9, fact_flagged=False) == "likely_preserved"


def test_low_similarity_is_likely_changed():
    assert classify_screen_label(similarity=0.1, fact_flagged=False) == "likely_changed"


def test_middle_band_is_needs_review():
    # Calibrated band (default threshold=0.75, review_band=0.35 -> floor 0.40)
    assert classify_screen_label(similarity=0.55, fact_flagged=False) == "needs_review"


def test_boundary_at_preserved_threshold():
    assert classify_screen_label(similarity=0.75, fact_flagged=False, preserved_threshold=0.75, review_band=0.35) == "likely_preserved"
    # Just below the threshold falls into the review band, not "changed"
    assert classify_screen_label(similarity=0.749, fact_flagged=False, preserved_threshold=0.75, review_band=0.35) == "needs_review"


def test_boundary_at_review_band_floor():
    assert classify_screen_label(similarity=0.40, fact_flagged=False, preserved_threshold=0.75, review_band=0.35) == "needs_review"
    assert classify_screen_label(similarity=0.399, fact_flagged=False, preserved_threshold=0.75, review_band=0.35) == "likely_changed"


def test_custom_thresholds_are_respected():
    assert classify_screen_label(similarity=0.5, fact_flagged=False, preserved_threshold=0.4, review_band=0.1) == "likely_preserved"
    assert classify_screen_label(similarity=0.2, fact_flagged=False, preserved_threshold=0.4, review_band=0.1) == "likely_changed"


# --- model-backed functions, real spaCy + sentence-transformers calls ---


def test_extract_facts_finds_numbers_and_names():
    facts = extract_facts("Barack Obama visited three schools in Chicago on Monday.")
    assert "three" in facts["numbers"]
    assert any("obama" in n for n in facts["names"]) or any("chicago" in n for n in facts["names"])


def test_check_fact_preservation_catches_the_real_confirmation_round_case():
    # The actual failure found in EXP-DATA-001-R1-confirmation:
    # "at least one C" was rewritten as "two Cs".
    original = "Most students get good grades, if they have to have at least one C in order to not be able to participate in a sport."
    rewritten = "If they need just two Cs to miss a sport entirely, some students might struggle academically."
    result = check_fact_preservation(original, rewritten)
    assert result["flagged"] is True
    assert any("one" in n for n in result["missing_numbers"])


def test_check_fact_preservation_passes_pure_style_edit():
    original = "The teacher explained the lesson clearly to the students."
    rewritten = "The teacher clearly explained the lesson to the students."
    result = check_fact_preservation(original, rewritten)
    assert result["flagged"] is False


def test_embedding_similarity_high_for_paraphrase_low_for_unrelated():
    original = "Students should be allowed to use phones during lunch."
    paraphrase = "Pupils ought to be permitted to use their phones at lunchtime."
    unrelated = "The weather today is sunny and warm across the region."

    sim_paraphrase = embedding_similarity(original, paraphrase)
    sim_unrelated = embedding_similarity(original, unrelated)

    assert sim_paraphrase > sim_unrelated
    assert sim_paraphrase > 0.5
    assert sim_unrelated < 0.3
