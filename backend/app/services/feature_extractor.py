"""
Linguistic feature extraction.

Computes sentence-level and essay-level features from an already-parsed
spaCy document (see sentence_segmenter.parse_document / segment_sentences
— the same parse is reused here, not recomputed).

This module only *computes* features. It makes no judgment about whether
a value is "human-like" or "AI-like" — that comparison against reference
distributions is Phase 5/6's job. See DEC-006 for why this specific set
of features was chosen and which categories (language-model features) are
deliberately not included here.
"""

from collections import Counter
from dataclasses import dataclass
from statistics import mean, pstdev

from spacy.tokens import Doc, Span
from wordfreq import zipf_frequency

from app.services.sentence_segmenter import Sentence

# Zipf-scale cutoff below which a word is counted as "rare" (DEC-006).
# This defines the *feature*, not a detection rule.
RARE_WORD_ZIPF_THRESHOLD = 3.0

# Sentence-length buckets in words, for the short/medium/long distribution
# feature (Section 6B). Provisional per DEC-006 — not a scoring threshold.
SHORT_SENTENCE_MAX_WORDS = 10
MEDIUM_SENTENCE_MAX_WORDS = 20

# Window size (tokens) for moving-average type-token ratio.
MATTR_WINDOW = 50

_POS_TAGS_OF_INTEREST = ("NOUN", "VERB", "ADJ", "ADV", "PRON")


@dataclass(frozen=True)
class SentenceFeatures:
    word_count: int
    char_count: int
    punctuation_count: int
    avg_word_length: float
    noun_ratio: float
    verb_ratio: float
    adj_ratio: float
    adv_ratio: float
    pronoun_ratio: float
    dependency_depth: int


@dataclass(frozen=True)
class EssayFeatures:
    sentence_count: int
    sentence_length_mean: float
    sentence_length_std: float
    sentence_length_cv: float
    short_sentence_ratio: float
    medium_sentence_ratio: float
    long_sentence_ratio: float
    type_token_ratio: float
    moving_average_ttr: float
    rare_word_ratio: float
    repeated_bigram_ratio: float
    repeated_trigram_ratio: float
    repeated_sentence_opening_ratio: float


def extract_sentence_features(span: Span) -> SentenceFeatures:
    tokens = [t for t in span if not t.is_space]
    word_tokens = [t for t in tokens if t.is_alpha]
    punctuation_count = sum(1 for t in tokens if t.is_punct)

    word_count = len(word_tokens)
    char_count = sum(len(t.text) for t in word_tokens)
    avg_word_length = char_count / word_count if word_count else 0.0

    pos_counts = Counter(t.pos_ for t in tokens)
    denom = len(tokens) or 1

    dependency_depth = _dependency_depth(tokens)

    return SentenceFeatures(
        word_count=word_count,
        char_count=char_count,
        punctuation_count=punctuation_count,
        avg_word_length=avg_word_length,
        noun_ratio=pos_counts["NOUN"] / denom,
        verb_ratio=pos_counts["VERB"] / denom,
        adj_ratio=pos_counts["ADJ"] / denom,
        adv_ratio=pos_counts["ADV"] / denom,
        pronoun_ratio=pos_counts["PRON"] / denom,
        dependency_depth=dependency_depth,
    )


def extract_essay_features(doc: Doc | None, sentences: list[Sentence]) -> EssayFeatures:
    """`sentences` should come from sentence_segmenter.segment_sentences
    over the same `doc`, so sentence boundaries here match whatever the
    rest of the pipeline (and the UI) uses."""

    sentence_word_counts = [sum(1 for t in s.span if t.is_alpha) for s in sentences]
    sentence_texts = [s.text for s in sentences]

    sentence_count = len(sentence_word_counts)
    sentence_length_mean = mean(sentence_word_counts) if sentence_word_counts else 0.0
    sentence_length_std = pstdev(sentence_word_counts) if len(sentence_word_counts) > 1 else 0.0
    sentence_length_cv = (
        sentence_length_std / sentence_length_mean if sentence_length_mean else 0.0
    )

    short = sum(1 for c in sentence_word_counts if c <= SHORT_SENTENCE_MAX_WORDS)
    medium = sum(
        1
        for c in sentence_word_counts
        if SHORT_SENTENCE_MAX_WORDS < c <= MEDIUM_SENTENCE_MAX_WORDS
    )
    long_ = sum(1 for c in sentence_word_counts if c > MEDIUM_SENTENCE_MAX_WORDS)
    n = sentence_count or 1

    words = [t.text.lower() for t in doc if t.is_alpha] if doc is not None else []

    return EssayFeatures(
        sentence_count=sentence_count,
        sentence_length_mean=sentence_length_mean,
        sentence_length_std=sentence_length_std,
        sentence_length_cv=sentence_length_cv,
        short_sentence_ratio=short / n,
        medium_sentence_ratio=medium / n,
        long_sentence_ratio=long_ / n,
        type_token_ratio=_type_token_ratio(words),
        moving_average_ttr=_moving_average_ttr(words, MATTR_WINDOW),
        rare_word_ratio=_rare_word_ratio(words),
        repeated_bigram_ratio=_repeated_ngram_ratio(words, 2),
        repeated_trigram_ratio=_repeated_ngram_ratio(words, 3),
        repeated_sentence_opening_ratio=_repeated_sentence_opening_ratio(sentence_texts),
    )


def _dependency_depth(tokens) -> int:
    if not tokens:
        return 0

    depths: dict[int, int] = {}

    def depth_of(token) -> int:
        if token.i in depths:
            return depths[token.i]
        if token.head.i == token.i:
            depth = 0
        else:
            depth = depth_of(token.head) + 1
        depths[token.i] = depth
        return depth

    return max(depth_of(t) for t in tokens)


def _type_token_ratio(words: list[str]) -> float:
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _moving_average_ttr(words: list[str], window: int) -> float:
    if not words:
        return 0.0
    if len(words) <= window:
        return _type_token_ratio(words)

    ratios = [
        _type_token_ratio(words[i : i + window]) for i in range(len(words) - window + 1)
    ]
    return mean(ratios)


def _rare_word_ratio(words: list[str]) -> float:
    if not words:
        return 0.0
    rare = sum(1 for w in words if zipf_frequency(w, "en") < RARE_WORD_ZIPF_THRESHOLD)
    return rare / len(words)


def _repeated_ngram_ratio(words: list[str], n: int) -> float:
    if len(words) < n:
        return 0.0
    ngrams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(c for c in counts.values() if c > 1)
    return repeated / len(ngrams)


def _repeated_sentence_opening_ratio(sentence_texts: list[str]) -> float:
    if len(sentence_texts) < 2:
        return 0.0
    openings = [" ".join(text.split()[:2]).lower() for text in sentence_texts]
    counts = Counter(openings)
    repeated = sum(c for c in counts.values() if c > 1)
    return repeated / len(openings)
