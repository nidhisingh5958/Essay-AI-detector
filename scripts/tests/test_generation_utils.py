import pytest

from generation_utils import (
    align_and_diff_sentences,
    assign_family_splits,
    budget_max_new_tokens,
    check_ai_self_reference,
    check_empty_output,
    check_excessive_repetition,
    check_instruction_artifacts,
    check_instruction_leakage,
    check_length_bounds,
    find_family_split_violations,
    modified_sentence_indices,
    near_duplicate_pairs,
    near_duplicate_pairs_scoped,
    pick_rewrite_paragraph_index,
    pick_rewrite_sentence_index,
    select_seed_essays,
    truncate_to_word_budget,
    validate_semantic_preservation,
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


def test_align_and_diff_sentences_does_not_understate_similarity_for_long_sentences():
    """Regression test: difflib.SequenceMatcher's default autojunk=True
    treats characters as "popular" (excluded from matching) once a
    sequence passes 200 characters -- for a long sentence differing by
    only one word, that default badly understated similarity (observed:
    ~0.28 instead of ~0.97 for the fixture below) during EXP-DATA-001-R1
    confirmation-round development. align_and_diff_sentences must pass
    autojunk=False to avoid this."""
    original = (
        "Community service teaches students responsibility and empathy, and it also "
        "helps young people build lasting connections within their own neighborhoods."
    )
    edited = (
        "Community service teaches students responsibility and compassion, and it also "
        "helps young people build lasting connections within their own neighborhoods."
    )
    result = align_and_diff_sentences([original], [edited])
    assert result["structure_drift"] is False
    similarity = result["pairs"][0][2]
    assert similarity > 0.9  # one word differs in a ~180-character sentence -- should read as highly similar


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


def test_find_family_split_violations_empty_when_invariant_holds():
    records = [
        {"family_id": "A", "split": "train"},
        {"family_id": "A", "split": "train"},
        {"family_id": "A", "split": "train"},
        {"family_id": "B", "split": "test"},
        {"family_id": "B", "split": "test"},
    ]
    assert find_family_split_violations(records) == []


def test_find_family_split_violations_catches_a_split_family():
    # Regression fixture for the hard leakage invariant (DEC-011 Section
    # 13): a family whose members ended up in different splits must be
    # caught, not silently accepted.
    records = [
        {"family_id": "A", "split": "train"},
        {"family_id": "A", "split": "test"},  # violation
        {"family_id": "B", "split": "validation"},
        {"family_id": "B", "split": "validation"},
    ]
    violations = find_family_split_violations(records)
    assert len(violations) == 1
    assert violations[0]["family_id"] == "A"
    assert violations[0]["splits"] == ["test", "train"]


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


# --- check_instruction_leakage: the 5 scenarios required after the
# EXP-DATA-001 QC bug fix (meta-instruction only, never prompt/essay
# content) ---

META_INSTRUCTION = (
    "Write a persuasive essay of approximately 163 words responding to the "
    "following prompt. Write in the voice of a student. Return only the "
    "essay, with no preamble or title."
)


def test_leakage_1_legitimate_topic_wording_passes():
    # Mirrors the real EXP-DATA-001 false positive: essay content overlaps
    # with the *prompt* ("...bring their phones to school and use them
    # during..."), which is never passed to this check -- only the meta
    # wrapper above is.
    output = (
        "I support allowing students to bring their phones to school and use "
        "them during lunch, as long as they stay off during class time."
    )
    assert check_instruction_leakage(META_INSTRUCTION, output) is False


def test_leakage_2_actual_instruction_leakage_fails():
    output = (
        "Write a persuasive essay of approximately 163 words responding to "
        "the following prompt, as you requested. Phones are useful tools."
    )
    assert check_instruction_leakage(META_INSTRUCTION, output) is True


def test_leakage_3_ai_self_reference_flagged_separately():
    output = (
        "Phones can be distracting in class. As an AI language model, I "
        "don't have personal experiences with school policies, but I can "
        "offer some perspective."
    )
    assert check_ai_self_reference(output) is True
    # Not necessarily an instruction-wrapper leak -- distinct failure mode.
    assert check_instruction_leakage(META_INSTRUCTION, output) is False


def test_leakage_4_generation_preamble_flagged_by_artifacts_check():
    output = "Sure, here's the essay: Phones can be distracting in class."
    assert check_instruction_artifacts(output) is True


def test_leakage_5_normal_essay_discussing_its_prompt_passes():
    output = (
        "Community service teaches students responsibility. Volunteering at "
        "a shelter or park cleanup builds character and connects students "
        "to their neighborhoods."
    )
    assert check_instruction_leakage(META_INSTRUCTION, output) is False
    assert check_ai_self_reference(output) is False
    assert check_instruction_artifacts(output) is False


def test_leakage_regression_old_bug_is_preserved_as_evidence():
    """EXP-DATA-001 (2026-08-10) found that comparing against the WHOLE
    formatted instruction -- including the embedded source prompt text --
    produced false positives: a legitimate, on-topic essay got flagged
    merely for echoing its own assigned topic's wording. This test
    preserves that failure mode as a documented regression: feeding the
    full instruction+prompt (the old, buggy call pattern) still flags a
    clean essay, which is exactly why callers must now pass only the meta
    wrapper (see check_instruction_leakage's docstring) and why
    run_exp_data_001.py was changed to do so."""
    whole_instruction_including_prompt = (
        META_INSTRUCTION
        + "\n\nPrompt: Your principal is reconsidering the school's cell phone "
        "policy. Policy 1: Allow students to bring phones to school and use "
        "them during lunch periods and other free times."
    )
    legitimate_essay = (
        "I support Policy 1: allow students to bring phones to school and "
        "use them during lunch periods and other free times, as long as "
        "they remain off during class."
    )
    # The old (buggy) call pattern -- kept here only to prove the bug is
    # real and stays caught, not as a recommended usage.
    assert check_instruction_leakage(whole_instruction_including_prompt, legitimate_essay) is True
    # The fixed call pattern -- meta wrapper only.
    assert check_instruction_leakage(META_INSTRUCTION, legitimate_essay) is False


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


def test_check_ai_self_reference_detects_mid_text_disclaimers():
    assert check_ai_self_reference("As an AI, I don't have personal opinions, but here goes.") is True
    assert check_ai_self_reference("Phones can be distracting. As a language model, I can't say for sure.") is True
    assert check_ai_self_reference("Community service builds character and connects students to their town.") is False


def test_near_duplicate_pairs_finds_matches_and_ignores_distinct_texts():
    texts = [
        "This essay discusses community service and its benefits for society.",
        "this essay discusses community service and its benefits for society.",
        "A completely unrelated essay about driverless cars and technology policy.",
    ]
    pairs = near_duplicate_pairs(texts)
    assert pairs == [(0, 1)]


# --- near_duplicate_pairs_scoped: the 5 required regression scenarios ---
# (family-aware duplicate detection, added after EXP-DATA-001-R1 found the
# flat check flags expected same-family similarity as if it were a bug)

_HUMAN_ORIGINAL_FAM1 = (
    "Community service teaches students responsibility and empathy. "
    "Volunteering at a shelter or park cleanup builds character. "
    "Students who serve their community often report a greater sense of belonging."
)
_LIGHT_EDIT_FAM1 = (
    "Community service teaches students responsibility and compassion. "
    "Volunteering at a shelter or park cleanup builds character. "
    "Students who serve their community often report a greater sense of belonging."
)
_PARAGRAPH_EDIT_FAM1 = (
    "Community service instills a sense of duty and empathy in young people. "
    "Volunteering at a shelter or park cleanup builds character. "
    "Students who serve their community often report a greater sense of belonging."
)


def test_scoped_1_same_family_transformed_samples_are_allowed():
    items = [
        ("fam1__sentence_light", "fam1", _LIGHT_EDIT_FAM1),
        ("fam1__paragraph_light", "fam1", _PARAGRAPH_EDIT_FAM1),
    ]
    result = near_duplicate_pairs_scoped(items, near_similarity_threshold=0.9)
    assert result["cross_family"] == []
    # They are similar (same family, expected) -- may appear as informational same_family, never as cross_family.
    assert all(pair[0] != pair[1] for pair in result["same_family"])


def test_scoped_2_same_family_original_and_transformed_are_allowed():
    items = [
        ("fam1__human", "fam1", _HUMAN_ORIGINAL_FAM1),
        ("fam1__sentence_light", "fam1", _LIGHT_EDIT_FAM1),
    ]
    result = near_duplicate_pairs_scoped(items, near_similarity_threshold=0.9)
    assert result["cross_family"] == []
    assert len(result["same_family"]) == 1  # flagged as similar, but same-family, so never "suspicious"
    pair_ids = result["same_family"][0][:2]
    assert set(pair_ids) == {"fam1__human", "fam1__sentence_light"}


def test_scoped_3_identical_outputs_from_different_families_are_flagged():
    items = [
        ("fam1__full_ai", "fam1", "Phones should be allowed in class for emergencies only."),
        ("fam2__full_ai", "fam2", "Phones should be allowed in class for emergencies only."),
    ]
    result = near_duplicate_pairs_scoped(items)
    assert len(result["cross_family"]) == 1
    assert result["cross_family"][0][:2] == ("fam1__full_ai", "fam2__full_ai")
    assert result["cross_family"][0][2] == 1.0
    assert result["same_family"] == []


def test_scoped_4_near_identical_outputs_from_different_families_are_flagged():
    items = [
        ("fam1__full_ai", "fam1", "Phones should be allowed in class for genuine emergencies only, nothing else."),
        ("fam2__full_ai", "fam2", "Phones should be allowed in class for real emergencies only, nothing else."),
    ]
    result = near_duplicate_pairs_scoped(items, near_similarity_threshold=0.85)
    assert len(result["cross_family"]) == 1
    assert result["cross_family"][0][2] >= 0.85


def test_scoped_5_unrelated_outputs_are_not_flagged():
    items = [
        ("fam1__full_ai", "fam1", "Community service teaches responsibility and builds character over time."),
        ("fam2__full_ai", "fam2", "Driverless cars raise complex questions about liability, safety, and regulation."),
    ]
    result = near_duplicate_pairs_scoped(items)
    assert result["cross_family"] == []
    assert result["same_family"] == []


def test_validate_semantic_preservation_accepts_known_values_only():
    assert validate_semantic_preservation("preserved") is True
    assert validate_semantic_preservation("questionable") is True
    assert validate_semantic_preservation("changed") is True
    assert validate_semantic_preservation("not_yet_reviewed") is True
    assert validate_semantic_preservation("definitely_fine") is False
