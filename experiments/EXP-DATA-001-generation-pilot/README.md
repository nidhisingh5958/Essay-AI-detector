# EXP-DATA-001 — Generation Pipeline Pilot

## Status
**Executed 2026-08-10.** Full results: [reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md).
This document is preserved as the pre-registered design (objective,
hypothesis, planned scope) — see the report for what actually happened
and the "Scope note" below for one deliberate change from the original
plan.

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

**Result: partially confirmed, partially refuted** — see
[reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md) §14. The
surgical-splice half of the hypothesis held; the whole-essay-diff half
did not (70% structure-drift rate for light/moderate polish). DEC-011 has
been updated accordingly, not left to silently describe an unvalidated
design.

## Dataset / version

Human seed essays: 10, drawn from the actually-acquired PERSUADE 2.0
corpus (`data/raw/persuade_2.0/persuade_2.0_human_scores_demo_id_github.csv`,
DEC-009, Accepted), filtered to `task == "Independent"`.

## Scope note (deviation from the original plan, made deliberately)

The original plan below listed 6 *generated* categories (including
`heavy_revision`) plus the 10 human originals (~70 samples). The
instruction that authorized running this pilot specified a tighter scope:
**human original counted as one of 6 total categories** (human, full_ai,
light_polish, moderate_polish, sentence_rewrite_single,
paragraph_rewrite_single) — 60 samples total, `heavy_revision` and the
`_multi` variants deferred. The pilot was executed against that tighter,
explicitly-authorized scope, not the originally-sketched one. Noted here
so the discrepancy is visible rather than silently resolved.

## Planned sample set (original sketch — see Scope note for what actually ran)

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
this pilot to keep it small; they remain deferred, along with
`heavy_revision`, to a future pilot iteration.)

## Configuration (as actually run)

- Model: Qwen2.5-1.5B-Instruct (`generation_model_revision` recorded per
  sample; falls back to the bare model name rather than a pinned commit
  SHA — noted as a minor reproducibility gap in the report).
- Generation config varied per sample (temperature/top_p fixed per
  category, unique seed per sample) — see report §4.
- Length tolerance: ±15% of seed essay word count for `full_ai`
  (worked reasonably); no dedicated tolerance mechanism existed yet for
  the polish categories, which the report identifies as a gap (§15).

## What the pilot inspected

1. **Generation quality** — manual read of outputs per category; see
   report §12–14.
2. **Length distribution** — target vs. actual length per sample; see
   report §6, §15.
3. **Transformation realism** — surgical-splice categories read
   coherently; see report §12.
4. **Metadata correctness** — all 60 records validated against the
   schema, zero missing fields; see report §11.
5. **Sentence-level provenance accuracy** — 33 `modified_spans` checked,
   zero invalid; the `splice_resegmentation_mismatch` QC check caught 2
   real edge cases; see report §10, §13. The diff-similarity threshold
   was **not** set — the pilot found no basis for one (report §7, §16).
6. **Duplicate rates** — zero near-duplicates found; see report §8.

## Explicit non-goals (honored)

- No detector/classifier was run against this pilot's output.
- No accuracy, precision, recall, or "the detector works" claim is made.
- No large-scale generation follows automatically — scaling remains a
  separate, explicit decision pending review of the report's
  recommendations.

## Result

See [reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md) in full.
Summary: full-generation and surgical-splice categories work well;
whole-essay-instruction polish categories do not, for a real and
diagnosed reason (model consolidates sentences despite instructions not
to), not random noise.

## Conclusion

The pipeline is not ready to scale as originally designed. Surgical-splice
categories (`sentence_rewrite_single`, `paragraph_rewrite_single`) and
`full_ai` are validated and ready. The polish categories need a mechanism
change (proposed: sequence-alignment instead of exact-count matching,
plus dedicated length control) before they can be trusted — not a
threshold tune, which this pilot explicitly found no basis for.

## Resulting decision

[DEC-011](../../docs/decisions/DEC-011-mixed-text-generation.md) updated:
status changed to "Provisional — partially invalidated by pilot evidence,"
Evidence section rewritten with real findings, Revisit When section
rewritten with concrete next steps (not yet implemented).
[DEC-010](../../docs/decisions/DEC-010-machine-generation-model.md)
updated: Evidence section notes the model performed well where tested
cleanly, with the polish-category failures not yet attributable to model
quality specifically (methodology fix needs testing first).
