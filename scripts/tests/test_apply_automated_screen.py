"""
Tests for apply_automated_screen.extract_span_pair. Pure logic, no model
calls -- it only slices strings.
"""

from apply_automated_screen import extract_span_pair


def _human(text: str) -> dict:
    return {"transformation_type": "original", "text": text}


def test_paragraph_pair_uses_full_rewritten_paragraph_even_when_sentences_merge():
    # Regression test for a real bug found 2026-08-13 while building the
    # claim-survival screen: reconstructing `rewritten` from
    # modified_spans char offsets truncated the paragraph when the model
    # merged two original sentences into one, silently dropping the
    # merged sentence's content from the extracted pair. Splitting both
    # texts by paragraph index instead is robust to this.
    human_text = (
        "Dear Principal,\n\n"
        "Community service. It's what prisoners and volunteers do "
        "each and every day. Personally, I don't think you should "
        "require us students to do it.\n\n"
        "Sincerely,\nStudent"
    )
    # The rewrite merges the first two original sentences into one --
    # modified_spans (as the real generation code computes them) can
    # cover only the LAST two resegmented sentences of the new paragraph,
    # excluding the merged first one.
    rewritten_text = (
        "Dear Principal,\n\n"
        "Community service is something that prisoners and volunteers "
        "engage in daily. Personally, I believe it would be "
        "inappropriate of us students to be required to do it.\n\n"
        "Sincerely,\nStudent"
    )
    record = {
        "transformation_type": "paragraph_light_controlled",
        "intended_span_index": 1,
        "modified_spans": [{"sentence_index": 1, "char_start": 0, "char_end": 1}],  # deliberately wrong/narrow
        "text": rewritten_text,
    }
    original, rewritten = extract_span_pair(_human(human_text), record)
    assert "Community service. It's what prisoners" in original
    assert rewritten.startswith("Community service is something that prisoners")
    assert "inappropriate of us students" in rewritten


def test_paragraph_pair_uses_full_rewritten_paragraph_even_when_rewrite_adds_a_blank_line():
    # Regression test for a second real bug found 2026-08-13 (same day,
    # while validating the first fix): splitting BOTH texts on "\n\n" at
    # the same paragraph index breaks when the model's own replacement
    # text contains a blank-line break -- that produces MORE "\n\n"
    # paragraphs in the rewritten essay than in the human one, so the
    # same-index split captures only the first fragment of the actual
    # rewrite (seed 7AF7BFC4BF8D: captured 95 of the real 247 rewritten
    # words). Locating the unchanged prefix/suffix instead is exact
    # regardless of the rewrite's internal formatting.
    human_text = "Dear Principal,\n\nOne paragraph of original content here.\n\nSincerely,\nStudent"
    # The model's rewrite splits the target paragraph into two of its own
    # paragraphs -- a real, observed generation behavior, not a
    # hypothetical.
    rewritten_text = (
        "Dear Principal,\n\n"
        "First half of the rewritten content.\n\n"
        "Second half of the rewritten content.\n\n"
        "Sincerely,\nStudent"
    )
    record = {
        "transformation_type": "paragraph_light_controlled",
        "intended_span_index": 1,
        "modified_spans": [{"sentence_index": 1, "char_start": 0, "char_end": 1}],
        "text": rewritten_text,
    }
    original, rewritten = extract_span_pair(_human(human_text), record)
    assert original == "One paragraph of original content here."
    assert rewritten == "First half of the rewritten content.\n\nSecond half of the rewritten content."


def test_sentence_pair_still_uses_modified_spans_offsets():
    human_text = "First sentence here. Second sentence here. Third sentence here."
    rewritten_text = "First sentence here. Second sentence REWRITTEN here. Third sentence here."
    record = {
        "transformation_type": "sentence_light_controlled",
        "intended_span_index": 1,
        "modified_spans": [{"sentence_index": 1, "char_start": 22, "char_end": 52}],
        "text": rewritten_text,
    }
    original, rewritten = extract_span_pair(_human(human_text), record)
    assert original == "Second sentence here."
    assert rewritten == rewritten_text[22:52]


def test_returns_none_when_no_modified_spans():
    record = {"transformation_type": "paragraph_light_controlled", "modified_spans": None}
    assert extract_span_pair(_human("Anything."), record) is None
