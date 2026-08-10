import math

import pytest

from app.services.language_model import (
    SentenceLMFeatures,
    compute_predictability_deltas,
    compute_sentence_lm_features,
    compute_token_log_probs,
)
from app.services.sentence_segmenter import parse_document, segment_sentences


def test_empty_text_yields_no_token_scores():
    assert compute_token_log_probs("") == []


def test_single_token_text_yields_no_token_scores():
    # Not enough tokens for even one next-token prediction.
    assert compute_token_log_probs("Hi") == []


def test_token_log_probs_are_valid_and_offsets_slice_correctly():
    text = "The cat sat on the mat."
    results = compute_token_log_probs(text)

    assert len(results) > 0
    for r in results:
        assert r.log_prob <= 0.0  # log of a probability in (0, 1]
        assert text[r.start_char : r.end_char] == r.token


def test_first_token_of_essay_is_never_scored():
    text = "The cat sat on the mat."
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    total_tokens = len(tokenizer(text, add_special_tokens=False)["input_ids"])

    results = compute_token_log_probs(text)
    assert len(results) == total_tokens - 1


def test_sentence_lm_features_aggregate_correctly():
    text = "Cats are wonderful animals. Dogs are loyal companions too."
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)
    token_log_probs = compute_token_log_probs(text)

    first = compute_sentence_lm_features(sentences[0], token_log_probs)
    second = compute_sentence_lm_features(sentences[1], token_log_probs)

    assert first is not None and second is not None
    assert first.token_count > 0
    assert second.token_count > 0
    assert first.perplexity == pytest.approx(math.exp(-first.mean_log_prob))
    assert second.perplexity == pytest.approx(math.exp(-second.mean_log_prob))

    # First sentence loses its very first token (no preceding context);
    # second sentence loses none, since its first token is conditioned on
    # everything before it in the essay.
    doc_tokens_in_first = [
        t for t in token_log_probs if sentences[0].start_char <= t.start_char < sentences[0].end_char
    ]
    assert first.token_count == len(doc_tokens_in_first)


def test_sentence_lm_features_none_when_no_tokens_are_scorable():
    text = "Hi"  # single token overall -> compute_token_log_probs returns []
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)
    token_log_probs = compute_token_log_probs(text)

    features = compute_sentence_lm_features(sentences[0], token_log_probs)
    assert features is None


def test_predictability_deltas_first_is_none_and_rest_are_differences():
    f1 = SentenceLMFeatures(mean_log_prob=-2.0, median_log_prob=-2.0, log_prob_variance=0.1, perplexity=7.4, token_count=5)
    f2 = SentenceLMFeatures(mean_log_prob=-3.5, median_log_prob=-3.5, log_prob_variance=0.2, perplexity=33.1, token_count=6)
    f3 = SentenceLMFeatures(mean_log_prob=-1.0, median_log_prob=-1.0, log_prob_variance=0.05, perplexity=2.7, token_count=4)

    deltas = compute_predictability_deltas([f1, f2, f3])

    assert deltas[0] is None
    assert deltas[1] == pytest.approx(f2.mean_log_prob - f1.mean_log_prob)
    assert deltas[2] == pytest.approx(f3.mean_log_prob - f2.mean_log_prob)


def test_predictability_deltas_propagate_none_for_missing_evidence():
    f1 = SentenceLMFeatures(mean_log_prob=-2.0, median_log_prob=-2.0, log_prob_variance=0.1, perplexity=7.4, token_count=5)
    deltas = compute_predictability_deltas([f1, None, f1])
    assert deltas == [None, None, None]


def test_long_essay_is_chunked_without_error():
    # ~1500 words, comfortably over distilgpt2's 1024-token context window,
    # to exercise the chunking path in compute_token_log_probs (DEC-008).
    sentence = "This sentence is part of a long essay about perseverance and growth. "
    text = sentence * 150
    results = compute_token_log_probs(text)
    assert len(results) > 1024  # spans multiple chunks
    for r in results:
        assert text[r.start_char : r.end_char] == r.token
