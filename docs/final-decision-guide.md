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

## 5. What signals do we measure? — Not yet implemented (Phase 3/4)

## 6. Why were these signals selected? — Not yet implemented (Phase 3/4, tied to `experiments/`)

## 7. How are signals normalized? — Not yet implemented (Phase 6)

## 8. How are signals combined? — Not yet implemented (Phase 6)

## 9. How is uncertainty handled? — Not yet implemented (Phase 6)

## 10. How is evidence generated? — Not yet implemented (Phase 6/7)

## 11. How was the language model selected? — Not yet implemented (Phase 4).
The *role* it's allowed to play (instrument, not judge) is already fixed —
see [decisions/DEC-004-no-llm-classifier.md](decisions/DEC-004-no-llm-classifier.md).

## 12. How was the scoring method selected? — Not yet implemented (Phase 6)

## 13. How was the dataset constructed? — Not yet implemented (Phase 5)

## 14. How was data leakage prevented? — Not yet implemented (Phase 5)

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

At Phase 2, the system can normalize, validate, and segment essay text
into sentences, but it does not measure any features or produce any
classification yet. The frontend accepts text but the "Analyze" action is
still disabled, and the backend exposes no `/api/analyze` endpoint. See
[project-status.md](project-status.md) for exactly what exists.

## 20. What would we improve next?

Proceed to Phase 3 (linguistic feature extraction: sentence rhythm,
vocabulary, repetition) per [project-status.md](project-status.md).
