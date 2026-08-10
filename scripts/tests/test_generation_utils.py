import pytest

from generation_utils import (
    align_and_diff_sentences,
    assign_family_splits,
    budget_max_new_tokens,
    check_empty_output,
    check_excessive_repetition,
    check_instruction_artifacts,
    check_length_bounds,
    check_prompt_leakage,
    modified_sentence_indices,
    near_duplicate_pairs,
    pick_rewrite_paragraph_index,
    pick_rewrite_sentence_index,
    select_seed_essays,
    truncate_to_word_budget,
)


def test_budget_max_new_tokens_scales_with_target_and_has_overhead():
    small = budget_max_new_tokens(100)
    large = budget_max_new_tokens(500)
    assert large > small
    assert small > 100  # overhead + tokens-per-word factor both push it above raw word count


def test_truncate_to_word_budget_keeps_prefix_within_tolerance():
    text = "One two three. Four five six seven. Eight nine ten eleven twelve."
    ends = [15, 36, len(text)]  # end offsets of each sentence
    # sentence 1 = 3 words, sentences 1+2 = 7 words, sentences 1+2+3 = 12 words
    truncated = truncate_to_word_budget(text, ends, target_words=7, max_over_ratio=1.15)
    assert truncated == text[:36]  # first two sentences = 7 words, within budget (<=8.05); third would overshoot


def test_truncate_to_word_budget_always_keeps_at_least_one_sentence():
    text = "This sentence alone already has more than three words in it."
    ends = [len(text)]
    truncated = truncate_to_word_budget(text, ends, target_words=2, max_over_ratio=1.15)
    assert truncated == text


def test_align_and_diff_sentences_flags_structure_drift_on_count_mismatch():
    result = align_and_diff_sentences(["A.", "B.", "C."], ["A.", "B."])
    assert result["structure_drift"] is True
    assert result["pairs"] == []


def test_align_and_diff_sentences_pairs_up_matching_counts():
    result = align_and_diff_sentences(["The cat sat.", "It was calm."], ["The cat sat.", "It felt calm."])
    assert result["structure_drift"] is False
    assert len(result["pairs"]) == 2
    assert result["pairs"][0][2] == 1.0  # identical sentence -> similarity 1.0
    assert result["pairs"][1][2] < 1.0


def test_modified_sentence_indices_uses_threshold():
    diff = {"pairs": [("a", "a", 1.0), ("b", "c", 0.4), ("d", "d", 1.0)]}
    assert modified_sentence_indices(diff, similarity_threshold=0.9) == [1]
    assert modified_sentence_indices(diff, similarity_threshold=0.3) == []


def test_select_seed_essays_filters_and_samples_deterministically():
    records = [
        {"id": f"e{i}", "word_count": 200 + i * 10, "sentence_count": 10, "paragraph_count": 3}
        for i in range(20)
    ]
    records.append({"id": "too_short", "word_count": 5, "sentence_count": 1, "paragraph_count": 1})
    result1 = select_seed_essays(records, n=5, min_words=150, max_words=500, min_sentences=5, min_paragraphs=2, rng_seed=1)
    result2 = select_seed_essays(records, n=5, min_words=150, max_words=500, min_sentences=5, min_paragraphs=2, rng_seed=1)
    assert result1 == result2  # deterministic given same seed
    assert "too_short" not in result1
    assert len(result1) == 5


def test_select_seed_essays_raises_when_not_enough_candidates():
    records = [{"id": "e1", "word_count": 200, "sentence_count": 10, "paragraph_count": 3}]
    with pytest.raises(ValueError):
        select_seed_essays(records, n=5, min_words=150, max_words=500, min_sentences=5, min_paragraphs=2, rng_seed=1)


def test_assign_family_splits_covers_all_ids_and_is_deterministic():
    ids = [f"id{i}" for i in range(10)]
    split1 = assign_family_splits(ids, rng_seed=42)
    split2 = assign_family_splits(ids, rng_seed=42)
    assert split1 == split2
    assert set(split1.keys()) == set(ids)
    assert set(split1.values()) <= {"train", "validation", "test"}
    assert list(split1.values()).count("train") == 7  # 70% of 10


def test_pick_rewrite_sentence_index_respects_word_bounds():
    sentences = ["Short.", "This sentence has exactly eight good words total.", "A" * 200]
    idx = pick_rewrite_sentence_index(sentences, min_words=8, max_words=40, rng_seed=0)
    assert idx == 1


def test_pick_rewrite_sentence_index_none_when_nothing_qualifies():
    sentences = ["Too short.", "Also short."]
    assert pick_rewrite_sentence_index(sentences, min_words=20, max_words=40, rng_seed=0) is None


def test_pick_rewrite_paragraph_index_respects_min_words():
    paragraphs = ["Short para.", "This is a much longer paragraph with plenty of words in it to qualify."]
    idx = pick_rewrite_paragraph_index(paragraphs, min_words=10, rng_seed=0)
    assert idx == 1


def test_check_empty_output():
    assert check_empty_output("") is True
    assert check_empty_output("   ") is True
    assert check_empty_output("hello") is False


def test_check_length_bounds():
    assert check_length_bounds(100, min_words=50, max_words=200) is True
    assert check_length_bounds(10, min_words=50, max_words=200) is False
    assert check_length_bounds(300, min_words=50, max_words=200) is False


def test_check_prompt_leakage_detects_verbatim_instruction_overlap():
    instruction = "Rewrite only the following sentence, preserving its meaning, without commentary."
    leaking_output = "Rewrite only the following sentence, preserving its meaning, here you go."
    clean_output = "The volunteer experience shaped how she saw her community."
    assert check_prompt_leakage(instruction, leaking_output, min_overlap_words=6) is True
    assert check_prompt_leakage(instruction, clean_output, min_overlap_words=6) is False


def test_check_excessive_repetition_flags_degenerate_loop():
    repeated_words = ("the cat sat on the mat " * 10).split()
    flagged, ratio = check_excessive_repetition(repeated_words, n=3, ratio_ceiling=0.3)
    assert flagged is True
    assert ratio > 0.3


def test_check_excessive_repetition_passes_normal_text():
    words = "the quick brown fox jumps over the lazy dog near the riverbank".split()
    flagged, ratio = check_excessive_repetition(words, n=3, ratio_ceiling=0.3)
    assert flagged is False


def test_check_instruction_artifacts_detects_common_preambles():
    assert check_instruction_artifacts("Sure, here's the rewritten sentence: ...") is True
    assert check_instruction_artifacts("Here's the essay you requested.") is True
    assert check_instruction_artifacts("Volunteering taught her patience.") is False


def test_near_duplicate_pairs_finds_matches_and_ignores_distinct_texts():
    texts = [
        "This essay discusses community service and its benefits for society.",
        "this essay discusses community service and its benefits for society.",
        "A completely unrelated essay about driverless cars and technology policy.",
    ]
    pairs = near_duplicate_pairs(texts)
    assert pairs == [(0, 1)]
