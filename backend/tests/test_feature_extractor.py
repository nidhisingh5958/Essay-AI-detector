import pytest

from app.services.feature_extractor import (
    extract_essay_features,
    extract_sentence_features,
)
from app.services.sentence_segmenter import parse_document, segment_sentences


def _parse(text):
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)
    return doc, sentences


def test_sentence_word_and_char_counts():
    _, sentences = _parse("The quick brown fox jumps.")
    features = extract_sentence_features(sentences[0].span)
    assert features.word_count == 5
    assert features.punctuation_count == 1
    assert features.char_count == sum(len(w) for w in ["The", "quick", "brown", "fox", "jumps"])


def test_sentence_avg_word_length_is_zero_for_no_words():
    _, sentences = _parse("...")
    features = extract_sentence_features(sentences[0].span)
    assert features.word_count == 0
    assert features.avg_word_length == 0.0


def test_sentence_pos_ratios_sum_to_at_most_one():
    _, sentences = _parse("She quickly wrote a brilliant essay.")
    features = extract_sentence_features(sentences[0].span)
    total = (
        features.noun_ratio
        + features.verb_ratio
        + features.adj_ratio
        + features.adv_ratio
        + features.pronoun_ratio
    )
    assert 0.0 <= total <= 1.0
    assert features.noun_ratio > 0  # "essay"
    assert features.verb_ratio > 0  # "wrote"
    assert features.adv_ratio > 0  # "quickly"


def test_dependency_depth_is_positive_for_a_real_sentence():
    _, sentences = _parse("The student who studied hard passed the difficult exam.")
    features = extract_sentence_features(sentences[0].span)
    assert features.dependency_depth >= 2  # has embedded relative clause


def test_essay_sentence_length_stats():
    text = "Short one. This one has five words. This sentence has exactly seven words total."
    doc, sentences = _parse(text)
    features = extract_essay_features(doc, sentences)
    assert features.sentence_count == 3
    assert features.sentence_length_mean == pytest.approx((2 + 5 + 7) / 3, rel=1e-6)
    assert features.sentence_length_std >= 0
    assert features.sentence_length_cv >= 0


def test_essay_sentence_length_buckets_sum_to_one():
    text = "Hi. " * 3 + "This is a medium length sentence with several words in it. " * 3
    doc, sentences = _parse(text)
    features = extract_essay_features(doc, sentences)
    total = (
        features.short_sentence_ratio
        + features.medium_sentence_ratio
        + features.long_sentence_ratio
    )
    assert total == pytest.approx(1.0)
    assert features.short_sentence_ratio > 0


def test_type_token_ratio_lower_with_more_repetition():
    doc_repetitive, sentences_repetitive = _parse("I learned. I learned. I learned. I learned.")
    doc_varied, sentences_varied = _parse(
        "I learned resilience. Patience taught me humility. Growth requires effort."
    )
    repetitive = extract_essay_features(doc_repetitive, sentences_repetitive)
    varied = extract_essay_features(doc_varied, sentences_varied)
    assert repetitive.type_token_ratio < varied.type_token_ratio


def test_repeated_bigram_ratio_detects_repeated_phrase():
    text = "In conclusion, life is beautiful. In conclusion, life is short."
    doc, sentences = _parse(text)
    features = extract_essay_features(doc, sentences)
    assert features.repeated_bigram_ratio > 0


def test_repeated_bigram_ratio_is_zero_for_fully_unique_text():
    text = "Mountains rise slowly over centuries of pressure and time."
    doc, sentences = _parse(text)
    features = extract_essay_features(doc, sentences)
    assert features.repeated_bigram_ratio == 0.0


def test_repeated_sentence_opening_ratio():
    text = (
        "In conclusion, I grew. "
        "In conclusion, I changed. "
        "The weather was nice that day."
    )
    doc, sentences = _parse(text)
    features = extract_essay_features(doc, sentences)
    assert features.repeated_sentence_opening_ratio == pytest.approx(2 / 3)


def test_rare_word_ratio_higher_for_uncommon_vocabulary():
    doc_common, sentences_common = _parse("The dog ran to the park and played with a ball.")
    doc_rare, sentences_rare = _parse(
        "The perspicacious pedagogue elucidated abstruse epistemological quandaries."
    )
    common = extract_essay_features(doc_common, sentences_common)
    rare = extract_essay_features(doc_rare, sentences_rare)
    assert rare.rare_word_ratio > common.rare_word_ratio


def test_empty_essay_features_do_not_error():
    doc, sentences = _parse("")
    assert doc is None
    features = extract_essay_features(None, sentences)
    assert features.sentence_count == 0
    assert features.type_token_ratio == 0.0
    assert features.rare_word_ratio == 0.0
