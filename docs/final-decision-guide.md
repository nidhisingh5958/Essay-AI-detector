# How the Detector Works

> Status: Phase 1. Most sections below are marked "not yet implemented"
> because most of the system doesn't exist yet — see
> [project-status.md](project-status.md). This document will be filled in
> incrementally, in the same order as the phases, so it stays truthful at
> every point rather than describing a finished system prematurely.

## 1. What problem are we solving?

Give an admissions reader (or a student checking their own essay) a way to
see *where* and *why* an essay's writing looks statistically unusual
relative to known human and machine writing — with explicit uncertainty —
rather than a single unexplained "AI probability."

## 2. What does the user provide?

A pasted essay (plain text) via the web UI. See `frontend/components/EssayInput/`.

## 3. How is the essay processed?

The raw pasted text is normalized before anything else looks at it
(`backend/app/services/text_normalizer.py`): Unicode is canonicalized
(NFC), line endings are unified to `\n`, and stray control characters are
stripped. Punctuation, quote style, and casing are left untouched
deliberately — those are candidate features for Phase 3, not things to
"clean up." The text is then validated (`services/validation.py`): empty/
whitespace-only input and input over the configured length limit
(currently 20,000 characters) are rejected with a clear error.

## 4. How are sentences identified?

Normalized text is split into sentences using spaCy's `en_core_web_sm`
statistical pipeline (`services/sentence_segmenter.py`), which uses a
trained parser rather than naive punctuation splitting — so abbreviations
like "Dr." or "U.S." don't create false sentence breaks. Each sentence
carries its character offsets into the normalized text, which the UI will
use for highlighting (Phase 9). See
[decisions/DEC-005-sentence-segmentation.md](decisions/DEC-005-sentence-segmentation.md)
for why this approach was chosen over regex splitting, NLTK, or a
non-statistical spaCy pipeline.

## 5. What signals do we measure?

As of Phase 3 (`services/feature_extractor.py`), for each **sentence**:
word/character/punctuation counts, average word length, the proportion of
its words that are nouns/verbs/adjectives/adverbs/pronouns, and how deep
its dependency (grammatical) tree is — a proxy for how syntactically
complex the sentence is. For the **whole essay**: how much sentence length
varies (mean, standard deviation, coefficient of variation, and a short/
medium/long distribution), vocabulary diversity (type-token ratio and a
windowed "moving average" version that's more stable for longer essays),
how many words are statistically rare (via the `wordfreq` library's word-
frequency data), and how much repeated language there is (repeated
2-word/3-word sequences, and repeated sentence openings).

As of Phase 4 (`services/language_model.py`), each sentence also gets
language-model-derived predictability signals: mean and median token
log-probability, perplexity, log-probability variance, and how much
predictability changes from the previous sentence. These come from a
small local model (distilgpt2) that only ever produces numbers — it is
never asked to judge the essay (see [DEC-004](decisions/DEC-004-no-llm-classifier.md)).

## 6. Why were these signals selected?

Each is a standard, literature-established measure of writing style
(stylometry/computational linguistics), not something invented for this
project — see
[decisions/DEC-006-phase3-feature-scope.md](decisions/DEC-006-phase3-feature-scope.md)
for the alternatives considered for the trickier cases (e.g. why
`wordfreq` rather than spaCy's own word-probability data, which turns out
to be unpopulated in the small model used here).

**Important caveat:** none of these features have been validated yet
against real human/AI-written text — that requires the dataset from Phase
5 and the comparison experiment (EXP-002) that hasn't run. DEC-006 is
marked *Provisional* for exactly this reason. Right now this document can
say what is measured, not yet which measurements actually distinguish
human from AI writing.

## 7. How are signals normalized? — Not yet implemented (Phase 6)

## 8. How are signals combined? — Not yet implemented (Phase 6)

## 9. How is uncertainty handled? — Not yet implemented (Phase 6)

## 10. How is evidence generated? — Not yet implemented (Phase 6/7)

## 11. How was the language model selected?

`distilgpt2` — small (82M parameters), runs fast on a normal laptop CPU,
explicitly suggested by the project brief, and shares its tokenizer with
`gpt2` so upgrading later (if distilgpt2's signal proves too weak) is a
one-line change. See
[decisions/DEC-007-local-language-model-choice.md](decisions/DEC-007-local-language-model-choice.md).
It scores the whole essay in one pass rather than each sentence in
isolation, so predictability is measured with real preceding-essay
context — see
[decisions/DEC-008-lm-scoring-method.md](decisions/DEC-008-lm-scoring-method.md).
Its *role* (instrument, never judge) was fixed before model selection —
see [decisions/DEC-004-no-llm-classifier.md](decisions/DEC-004-no-llm-classifier.md).

## 12. How was the scoring method selected? — Not yet implemented (Phase 6)

## 13. How was the dataset constructed?

The human-writing side is real, live-verified, and inspected as of Phase
5C: PERSUADE 2.0 (25,996 argumentative student essays) as the primary
corpus, ELLIPSE (6,482 essays from English Language Learners) for the
fairness analysis — both acquired via a script that checks the live
license against what was expected before downloading anything (see
[DEC-009](decisions/DEC-009-human-dataset-source.md) and the
[dataset inspection report](../reports/dataset-inspection.md)). Real
data-quality issues were found and documented (an unreliable word-count
column, a few duplicate IDs) rather than papered over. The
machine-written and mixed/AI-polished side is fully designed
([DEC-010](decisions/DEC-010-machine-generation-model.md),
[DEC-011](decisions/DEC-011-mixed-text-generation.md),
[generation-methodology.md](generation-methodology.md)) but **not yet
generated** — that's the next phase, pending review.

## 14. How was data leakage prevented?

The design principle is fixed even though generation hasn't happened
yet: every sample derived from one human seed essay shares a `family_id`
and must land in the same train/validation/test split, with split
assignment happening *before* generation runs, not after (see
[DEC-011](decisions/DEC-011-mixed-text-generation.md)).

## 15. How was the detector evaluated? — Not yet implemented (Phase 10)

## 16. What did it get wrong? — Not yet implemented (Phase 11), see [failure-analysis.md](failure-analysis.md)

## 17. What fairness issues were found? — Not yet implemented (Phase 12), see [fairness.md](fairness.md)

## 18. What alternatives were rejected?

See [alternatives-considered.md](alternatives-considered.md) — currently
covers the whole-system architecture choices made in Phase 1 (rejecting
LLM-as-classifier, RAG, multi-agent architecture, an end-to-end fine-tuned
transformer classifier, and a single-threshold detector). Feature- and
calibration-level alternatives will be added as those phases complete.

## 19. What are the current limitations?

The system can normalize, validate, and segment essay text, and compute a
provisional set of linguistic features and language-model predictability
signals per sentence and per essay — but it does not yet know whether
any of those features actually distinguish human from AI writing (no
reference distributions, no scoring), and it produces no classification.
distilgpt2 is a small, relatively weak language model (DEC-007). The
human corpus itself is real but domain-mismatched — argumentative/
proficiency-assessment student essays, not personal-narrative admissions
writing (DEC-009) — and has documented data-quality quirks (an
unreliable word-count column, a handful of duplicate IDs; see the
[inspection report](../reports/dataset-inspection.md)). No machine or
mixed sample has been generated yet. The frontend accepts text but the
"Analyze" action is still disabled, and the backend exposes no
`/api/analyze` endpoint. See [project-status.md](project-status.md) for
exactly what exists.

## 20. What would we improve next?

Pending review of the Phase 5C inspection findings: run the EXP-DATA-001
generation pilot (still not run) using the now-confirmed real prompt
text and paragraph structure from PERSUADE, then use the dataset to
actually test whether Phase 3/4 features carry human/AI signal
(EXP-002, EXP-003) — per [project-status.md](project-status.md).
