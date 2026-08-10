"""
Language model instrumentation.

Per DEC-004, the local causal LM here is used strictly to compute
measurable quantities (token log-probabilities, perplexity, log-prob
variance). It never produces a classification, a percentage, or a
natural-language explanation — those come from our own scoring/evidence
code in later phases, operating on the numbers this module returns.

Scoring approach (whole-essay single pass, chunked only if needed; tokens
attributed back to sentences by character offset) is DEC-008. Model choice
(distilgpt2) is DEC-007.
"""

import math
from dataclasses import dataclass
from functools import lru_cache
from statistics import median, pvariance

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.services.sentence_segmenter import Sentence

MODEL_NAME = "distilgpt2"


@lru_cache(maxsize=1)
def _load_model():
    """Loads tokenizer + model once per process and reuses them (Section
    5/21: never reload per sentence/request)."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


@dataclass(frozen=True)
class TokenLogProb:
    token: str
    log_prob: float
    start_char: int
    end_char: int


def compute_token_log_probs(text: str) -> list[TokenLogProb]:
    """Compute each token's log-probability given the tokens preceding it
    in `text`, via one or more teacher-forced forward passes.

    The very first token of `text` (and, for essays long enough to need
    chunking, the first token of each subsequent chunk) has no preceding
    context within its scoring window and is not scored — see DEC-008.
    """
    if not text.strip():
        return []

    tokenizer, model = _load_model()
    max_len = model.config.n_positions

    encoding = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
    input_ids = encoding["input_ids"]
    offsets = encoding["offset_mapping"]

    if len(input_ids) < 2:
        return []

    results: list[TokenLogProb] = []
    for chunk_start in range(0, len(input_ids), max_len):
        chunk_ids = input_ids[chunk_start : chunk_start + max_len]
        chunk_offsets = offsets[chunk_start : chunk_start + max_len]
        if len(chunk_ids) < 2:
            continue  # trailing chunk too short to score any token

        ids_tensor = torch.tensor([chunk_ids])
        with torch.no_grad():
            logits = model(ids_tensor).logits[0]

        log_probs = torch.log_softmax(logits, dim=-1)

        for i in range(len(chunk_ids) - 1):
            target_id = chunk_ids[i + 1]
            token_log_prob = log_probs[i, target_id].item()
            start, end = chunk_offsets[i + 1]
            results.append(
                TokenLogProb(
                    token=text[start:end],
                    log_prob=token_log_prob,
                    start_char=start,
                    end_char=end,
                )
            )

    return results


@dataclass(frozen=True)
class SentenceLMFeatures:
    mean_log_prob: float
    median_log_prob: float
    log_prob_variance: float
    perplexity: float
    token_count: int


def compute_sentence_lm_features(
    sentence: Sentence, token_log_probs: list[TokenLogProb]
) -> SentenceLMFeatures | None:
    """Aggregate whole-essay token log-probabilities into per-sentence
    features, selecting tokens whose character span falls inside
    `sentence`. Returns None if no token in this sentence was scored
    (e.g. a one-token first sentence whose only token has no preceding
    context) — insufficient evidence, not a fabricated zero."""
    relevant = [
        t
        for t in token_log_probs
        if t.start_char >= sentence.start_char and t.end_char <= sentence.end_char
    ]
    if not relevant:
        return None

    log_probs = [t.log_prob for t in relevant]
    mean_lp = sum(log_probs) / len(log_probs)

    return SentenceLMFeatures(
        mean_log_prob=mean_lp,
        median_log_prob=median(log_probs),
        log_prob_variance=pvariance(log_probs) if len(log_probs) > 1 else 0.0,
        perplexity=math.exp(-mean_lp),
        token_count=len(relevant),
    )


def compute_predictability_deltas(
    sentence_features: list[SentenceLMFeatures | None],
) -> list[float | None]:
    """Change in mean log-probability between each sentence and the one
    before it (Section 6A). First sentence has no predecessor -> None.
    Either side missing (insufficient evidence) -> None, not a fabricated
    delta."""
    deltas: list[float | None] = [None]
    for prev, curr in zip(sentence_features, sentence_features[1:]):
        if prev is None or curr is None:
            deltas.append(None)
        else:
            deltas.append(curr.mean_log_prob - prev.mean_log_prob)
    return deltas
