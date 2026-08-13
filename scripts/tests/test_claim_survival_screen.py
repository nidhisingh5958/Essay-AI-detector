"""
Tests for claim_survival_screen.py. Pure classification logic tested as
fast unit tests; sentence_coverage/run_claim_survival_screen tested
against the real spaCy + sentence-transformers models (same pattern as
test_semantic_screen.py).
"""

from claim_survival_screen import (
    classify_claim_survival_label,
    run_claim_survival_screen,
    sentence_coverage,
)

# --- pure classification logic ---


def test_no_signals_is_no_omission():
    assert classify_claim_survival_label(coverage_dropped=False, fact_flagged=False) == "no_omission_signal"


def test_coverage_drop_alone_flags_review():
    assert classify_claim_survival_label(coverage_dropped=True, fact_flagged=False) == "possible_omission_flagged"


def test_fact_flag_alone_flags_review():
    assert classify_claim_survival_label(coverage_dropped=False, fact_flagged=True) == "possible_omission_flagged"


def test_both_signals_flags_review():
    assert classify_claim_survival_label(coverage_dropped=True, fact_flagged=True) == "possible_omission_flagged"


# --- model-backed: sentence_coverage ---


def test_sentence_coverage_detects_a_dropped_sentence():
    # Original has two independent claims; rewrite keeps one, drops the
    # other and replaces it with an unrelated sentence.
    original = (
        "The school should extend the library hours until 9pm. "
        "Students often have nowhere quiet to study after dinner."
    )
    rewritten = (
        "The school should extend the library hours until 9pm. "
        "The cafeteria serves lunch at noon every day."
    )
    result = sentence_coverage(original, rewritten)
    assert len(result["dropped_sentences"]) == 1
    assert "nowhere quiet to study" in result["dropped_sentences"][0]["original_sentence"]


def test_sentence_coverage_no_drop_when_all_sentences_paraphrased():
    original = (
        "The cafeteria should offer healthier lunch options. "
        "Students often skip meals because the food is unappealing."
    )
    rewritten = (
        "I believe the cafeteria needs to serve healthier food at lunch. "
        "Many students skip eating because they don't like what's offered."
    )
    result = sentence_coverage(original, rewritten)
    assert result["dropped_sentences"] == []


def test_sentence_coverage_empty_text_returns_empty_result():
    result = sentence_coverage("", "Something.")
    assert result["per_sentence"] == []
    assert result["dropped_sentences"] == []
    assert result["min_coverage_similarity"] is None


# --- model-backed: run_claim_survival_screen combines both signals ---


def test_run_claim_survival_screen_flags_a_dropped_claim():
    original = (
        "The school should extend the library hours until 9pm. "
        "Students often have nowhere quiet to study after dinner."
    )
    rewritten = (
        "The school should extend the library hours until 9pm. "
        "The cafeteria serves lunch at noon every day."
    )
    result = run_claim_survival_screen(original, rewritten)
    assert result.screen_label == "possible_omission_flagged"
    assert len(result.coverage["dropped_sentences"]) == 1


def test_run_claim_survival_screen_no_flag_for_faithful_paraphrase():
    original = (
        "The cafeteria should offer healthier lunch options. "
        "Students often skip meals because the food is unappealing."
    )
    rewritten = (
        "I believe the cafeteria needs to serve healthier food at lunch. "
        "Many students skip eating because they don't like what's offered."
    )
    result = run_claim_survival_screen(original, rewritten)
    assert result.screen_label == "no_omission_signal"


def test_run_claim_survival_screen_fact_check_false_positive_on_reworded_time_phrase():
    # Documented, known limitation inherited from semantic_screen's
    # fact-check (same class of false positive as DEC-012's "school
    # hours" vs "regular hours" case): rewording "until 9pm" as "until 9
    # at night" changes the exact token spaCy tags as numeric, flagging a
    # faithful paraphrase for review. This is the correct failure
    # direction for a screen (never silently pass), but it is not a real
    # omission -- recorded here so the false-positive rate is visible,
    # not hidden.
    original = "The school should extend the library hours until 9pm."
    rewritten = "I believe the library should stay open until 9 at night."
    result = run_claim_survival_screen(original, rewritten)
    assert result.fact_check["flagged"] is True
    assert result.screen_label == "possible_omission_flagged"
    assert result.coverage["dropped_sentences"] == []


def test_run_claim_survival_screen_against_real_db12ba4206b8_paragraph_does_not_flag():
    # Documented, disclosed finding (see module docstring): this
    # historical "changed"-labeled sample (claim omission, per manual
    # review notes) does NOT trigger a coverage drop when re-measured
    # against the text currently on disk -- all four original sentences
    # score 0.63-0.73 against their best rewrite match. Preserved here as
    # a regression/documentation test, not a claim the screen is
    # validated -- see EXP-DATA-001-R3 for the real validation.
    original = (
        "Community service. It's what prisoners and volunteers do each and every day. "
        "Personally, I don't think you should require us students to do community service. "
        "The service takes up what free time we have to do what we need and want to do."
    )
    rewritten = (
        "Community service is something that prisoners and volunteers engage in daily. "
        "Personally, I believe it would be inappropriate of us students to be required to "
        "participate in such activities. The service consumes our available leisure time, "
        "preventing us from fulfilling other personal desires and needs."
    )
    result = run_claim_survival_screen(original, rewritten)
    assert result.coverage["dropped_sentences"] == []
    for entry in result.coverage["per_sentence"]:
        assert 0.6 < entry["similarity"] < 0.8
