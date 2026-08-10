"""
Sentence segmentation.

Uses the shared spaCy pipeline (see DEC-005) to split normalized essay
text into sentences with character offsets into that text. The same
pipeline instance is reused for Phase 3 linguistic features (POS tags,
dependency depth) so segmentation and feature extraction never disagree
about sentence boundaries.
"""

from dataclasses import dataclass
from functools import lru_cache

import spacy
from spacy.language import Language


@lru_cache(maxsize=1)
def get_nlp() -> Language:
    """Loads the spaCy pipeline once per process and reuses it.

    Not loaded at import time: tests that only need normalization/
    validation shouldn't pay the model-load cost, and it keeps
    `import app.main` fast until a request actually needs NLP.
    """
    return spacy.load("en_core_web_sm")


@dataclass(frozen=True)
class Sentence:
    index: int
    text: str
    start_char: int
    end_char: int


def segment_sentences(text: str) -> list[Sentence]:
    """Split `text` into sentences with offsets into `text` itself.

    Callers are expected to pass already-normalized text (see
    text_normalizer.normalize_text) so offsets line up with what the
    frontend renders.
    """
    if not text.strip():
        return []

    doc = get_nlp()(text)

    sentences: list[Sentence] = []
    for sent in doc.sents:
        raw = text[sent.start_char : sent.end_char]
        stripped = raw.strip()
        if not stripped:
            continue

        leading_ws = len(raw) - len(raw.lstrip())
        real_start = sent.start_char + leading_ws
        real_end = real_start + len(stripped)

        sentences.append(
            Sentence(
                index=len(sentences),
                text=stripped,
                start_char=real_start,
                end_char=real_end,
            )
        )

    return sentences
