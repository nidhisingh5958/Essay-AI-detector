# EXP-DATA-001 — Generation Pipeline Pilot

## Status
**Designed, not run.** No generation has occurred. This is a design
document, written to be reviewed before any pilot execution — not a
report of results.

## Objective

Validate the generation pipeline design
([docs/generation-methodology.md](../../docs/generation-methodology.md),
[DEC-010](../../docs/decisions/DEC-010-machine-generation-model.md),
[DEC-011](../../docs/decisions/DEC-011-mixed-text-generation.md)) on a
small scale before committing to full dataset generation. This is a
**data-generation validation experiment**, not a detector-performance
evaluation — it produces no accuracy, precision, or recall claim, and
must not be cited as one.

## Hypothesis

The designed pipeline (Qwen2.5-1.5B-Instruct + the surgical-splice /
whole-essay-diff hybrid mechanism from DEC-011) can produce essays and
transformations that are: within the intended length tolerance of their
seed essay, free of generation-failure artifacts (Section 8 of
generation-methodology.md), and carry sentence-level ground truth that
actually matches what was requested (i.e., a `sentence_rewrite_single`
sample really only has one sentence's worth of text meaningfully changed).

This is a hypothesis to be checked, not assumed — if it fails, DEC-010
and/or DEC-011 get revisited (both already say so explicitly in their
"Revisit When" sections).

## Dataset / version

Human seed essays: 10, drawn from PERSUADE 2.0 **once acquisition
(DEC-009) has actually succeeded** — this experiment cannot run before
that. Not yet possible; blocked on Kaggle credentials
(see [project-status.md](../../docs/project-status.md)).

## Planned sample set

For each of the 10 seed essays, generate:

| Category | Count |
|---|---|
| `full_ai` | 10 |
| `light_polish` | 10 |
| `moderate_polish` | 10 |
| `sentence_rewrite_single` | 10 |
| `paragraph_rewrite_single` | 10 |
| `heavy_revision` | 10 |

60 generated/derived samples total, plus the 10 existing human
originals. (The full taxonomy in generation-methodology.md also includes
`sentence_rewrite_multi` and `paragraph_rewrite_multi` — omitted from
this pilot to keep it small, consistent with the "10 of each" scale
requested for this phase; they'll be exercised once the pilot validates
the core mechanism.)

## Configuration (planned)

- Model: Qwen2.5-1.5B-Instruct, revision to be pinned and recorded at
  actual run time (not yet downloaded).
- Generation config varies per sample per Section 7 of
  generation-methodology.md (temperature/top_p/seed), logged per sample.
- Length tolerance: ±15% of seed essay word count (starting value, to be
  checked against pilot results, not assumed correct).

## What the pilot will inspect (not yet performed)

1. **Generation quality** — manual read of a sample of outputs per
   category; does `light_polish` actually read as light, does
   `heavy_revision` preserve the original's meaning and argument?
2. **Length distribution** — target vs. actual length per sample;
   whether the ±15% tolerance is workable or needs adjustment.
3. **Transformation realism** — do the surgical-splice categories read
   coherently at the splice boundary given only adjacent-sentence
   context (a documented risk in DEC-011)?
4. **Metadata correctness** — every record validates against the schema
   in generation-methodology.md Section 9; `modified_spans` offsets
   correctly slice the final text.
5. **Sentence-level provenance accuracy** — for surgical-splice samples,
   confirm the spliced sentence(s) are exactly and only the ones marked
   in `modified_spans`. For diff-based samples, manually check whether
   the diff-based labeling looks right, and use these examples to
   actually set the similarity threshold and structure-drift tolerance
   that DEC-011 deferred.
6. **Duplicate rates** — near-duplicate check among the 10 `full_ai`
   samples (several may share a prompt).

## Explicit non-goals

- No detector/classifier is run against this pilot's output.
- No accuracy, precision, recall, or "the detector works" claim will be
  made from this experiment.
- No large-scale generation follows automatically from a successful
  pilot — scaling up is a separate, explicit decision after review.

## Result

Not yet run.

## Conclusion

Not yet run.

## Resulting decision

None yet — pending an actual pilot run and review.
