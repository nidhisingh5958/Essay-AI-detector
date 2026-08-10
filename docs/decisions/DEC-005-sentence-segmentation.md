# DEC-005 — Sentence Segmentation Approach

## Status
Accepted

## Date
2026-08-10

## Context

Every downstream stage (feature extraction, language-model scoring,
sentence-level classification, passage grouping, UI highlighting) depends
on correctly identifying sentence boundaries and their character offsets
in the essay text. Admissions essays commonly contain abbreviations
("U.S.", "Dr.", "e.g."), ellipses, quoted dialogue, and varied punctuation
— naive splitting breaks on these.

## Problem

How should the essay be split into sentences, and how should each
sentence's position in the original text be tracked (needed later for UI
highlighting)?

## Alternatives Considered

### Alternative A: Regex/rule-based splitting on `.`, `!`, `?`
Advantages:
- Zero dependencies, trivial to implement, fast.

Disadvantages:
- Breaks on abbreviations ("Dr. Smith" → two sentences), decimals
  ("3.5 GPA"), ellipses, and quoted punctuation. These are common in
  admissions essays. Errors here corrupt every downstream feature
  (sentence length, rhythm, LM perplexity per sentence), so segmentation
  quality is not a place to cut corners.

### Alternative B: NLTK `punkt` sentence tokenizer
Advantages:
- Mature, widely used, reasonably good abbreviation handling via its
  unsupervised model.

Disadvantages:
- Adds a second NLP dependency alongside spaCy, which the project already
  requires for Phase 3 linguistic features (POS tags, dependency depth,
  Section 6E). Using both means two libraries to install, version-pin, and
  reason about for no accuracy benefit over spaCy's own segmentation.

### Alternative C: spaCy blank pipeline + rule-based `sentencizer` component
Advantages:
- Fast, no statistical model download, pure punctuation/rule-based
  boundaries.

Disadvantages:
- Same abbreviation/edge-case weaknesses as Alternative A, since the
  rule-based `sentencizer` is still fundamentally punctuation-driven. Also
  still requires loading a *second* spaCy pipeline in Phase 3 for
  POS/dependency features (a blank pipeline has no tagger/parser), meaning
  two pipelines loaded and two places sentence boundaries could disagree
  (the blank pipeline's rule boundaries vs. the statistical pipeline's
  parser-based boundaries used for dependency features).

### Alternative D: spaCy statistical pipeline (`en_core_web_sm`), sentence
boundaries from its dependency parser
Advantages:
- Handles abbreviations, quotes, and varied punctuation substantially
  better than rule-based approaches, since boundaries come from a trained
  parse rather than punctuation alone.
- The same loaded pipeline will be reused for Phase 3's POS-tag and
  dependency-based features (Section 6E), so sentence boundaries and
  linguistic features are guaranteed consistent (one document parse, one
  set of sentence spans) rather than computed by two different tools that
  could disagree.
- Provides exact character offsets (`sent.start_char` / `sent.end_char`)
  needed for UI highlighting without extra bookkeeping.

Disadvantages:
- Requires downloading a ~13MB model (`en_core_web_sm`) and loading it
  once at process start — a real but small one-time cost, already
  budgeted for since Phase 3 needs this model regardless.
- Slower per-document than pure regex/rule-based splitting — acceptable
  given essay-length inputs (a few hundred to ~4,000 words) and that the
  model is loaded once and reused (Section 5/21: "load it once and reuse
  it").

## Decision

Use spaCy's `en_core_web_sm` statistical pipeline for sentence
segmentation, taking sentence boundaries and character offsets directly
from `doc.sents`.

## Why

It directly solves the abbreviation/punctuation edge cases that break
naive approaches, and — critically — it is the same model Phase 3 will
load anyway for POS/dependency features, so there is no additional
dependency or double-loading cost, and sentence boundaries stay consistent
with the linguistic features computed over them.

## Evidence

Verified manually against the punctuation-heavy and abbreviation test
cases in `backend/tests/test_sentence_segmenter.py` (e.g. "Dr. Smith
argued... but was she right?" correctly segments into two sentences, not
three). No comparative accuracy experiment against NLTK punkt was run —
this is a structural/consistency decision (one shared pipeline for
segmentation and later features) rather than one requiring an accuracy
comparison between two adequate off-the-shelf tokenizers.

## Trade-offs

Model load time (~1-2s) and memory footprint at process startup, in
exchange for boundary accuracy and consistency with Phase 3 features.
Mitigated by loading once per process (`lru_cache`), not per request.

## Consequences

Positive:
- Sentence boundaries and linguistic features come from one parse, one
  model, no risk of disagreement between two different sentence-splitting
  tools.
- Character offsets for UI highlighting come for free.

Negative:
- `en_core_web_sm` must be downloaded as a setup step
  (`python -m spacy download en_core_web_sm`) — documented in the root
  README.

## Revisit When

If Phase 4/10 profiling shows the full `en_core_web_sm` pipeline (tagger +
parser + attribute_ruler + lemmatizer + ner + tok2vec) is a latency
bottleneck for long essays, in which case disabling unused pipeline
components (e.g. `ner`, which nothing currently consumes) would be
evaluated as a performance decision, not a segmentation-accuracy one.

## Implementation

`backend/app/services/sentence_segmenter.py`

## Tests / Experiments

`backend/tests/test_sentence_segmenter.py`
