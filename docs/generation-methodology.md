# Machine & Mixed Text Generation Methodology

> Status: **Pilot-tested and redesigned (EXP-DATA-001 + EXP-DATA-001-R1,
> 2026-08-10).** EXP-DATA-001 (60 samples) found the whole-essay-
> instruction-plus-diff mechanism for light/moderate polish did not
> reliably produce sentence-level ground truth (70% structural drift, no
> separable similarity threshold — see
> [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md)). Rather than
> patching that mechanism with a threshold, it was **redesigned**: whole-
> essay polish is now Regime C (essay-level-only ground truth, never used
> for sentence metrics), and a new controlled-span mechanism produces
> sentence-level light/moderate examples using the *same* surgical-splice
> guarantee as the original sentence/paragraph rewrite categories. This
> redesign was targeted-validated in EXP-DATA-001-R1 (15 samples) — see
> [reports/EXP-DATA-001-R1.md](../reports/EXP-DATA-001-R1.md). The
> document below reflects the current (post-redesign) methodology, not
> the original pre-pilot sketch. Related decisions:
> [DEC-010](decisions/DEC-010-machine-generation-model.md) (generation
> model), [DEC-011](decisions/DEC-011-mixed-text-generation.md)
> (mixed-sample mechanism, including the full redesign rationale).

## 1. The core idea: families, not independent samples

Every generated/derived sample traces back to exactly one human **seed
essay**. A seed essay `S` produces a **family** of samples, organized
into the three ground-truth regimes [DEC-011](decisions/DEC-011-mixed-text-generation.md)
settled on after EXP-DATA-001's pilot findings (original design tried a
diff-based approach for whole-essay polish; that was abandoned for
sentence-level use after the pilot — see DEC-011's "Post-Pilot
Methodology Redesign" for why):

| Sample | Label | Regime | How it's made |
|---|---|---|---|
| `S` itself | `human` | — | Already exists, unmodified |
| `S.full_ai` | `machine` | — | Fully generated for the same prompt, same target length. **Validated, EXP-DATA-001.** |
| `S.sentence_rewrite_single` | `ai_assisted` | A (sentence, exact) | One sentence surgically replaced, full-rewrite instruction. **Validated, EXP-DATA-001.** |
| `S.sentence_light_controlled` | `ai_assisted` | A (sentence, exact) | Same splice mechanism, light-copy-edit instruction. **Redesign, EXP-DATA-001-R1.** |
| `S.sentence_moderate_controlled` | `ai_assisted` | A (sentence, exact) | Same splice mechanism, moderate-reword instruction. **Redesign, EXP-DATA-001-R1.** |
| `S.sentence_rewrite_multi` | `ai_assisted` | A (sentence, exact) | 2–4 sentences surgically replaced. Not yet exercised in any pilot. |
| `S.paragraph_rewrite_single` | `ai_assisted` | B (paragraph, exact) | One paragraph surgically replaced. **Validated, EXP-DATA-001.** |
| `S.paragraph_rewrite_multi` | `ai_assisted` | B (paragraph, exact) | 2+ paragraphs surgically replaced. Not yet exercised. |
| `S.light_polish` | `ai_assisted` | C (essay-level only) | Whole-essay light copy-edit instruction. **Essay-level ground truth only — see below.** |
| `S.moderate_polish` | `ai_assisted` | C (essay-level only) | Whole-essay moderate rephrase instruction. **Essay-level ground truth only.** |
| `S.heavy_revision` | `ai_assisted` | C (essay-level only) | Whole-essay heavy rewrite instruction. Not yet exercised. |

All members of a family share `family_id = S.id` and **must stay
together across train/validation/test splits** — see Section 6.

**Regime C (whole-essay) samples carry `ground_truth_confidence:
"essay_level_only"` and must never be used for sentence- or passage-level
evaluation** — not because of a missing threshold, but because
EXP-DATA-001 found the underlying transformation (sentence consolidation,
70% structural drift) makes sentence-level attribution genuinely
ambiguous, not just hard to measure. See DEC-011.

This design directly satisfies the "don't let the detector learn topic
differences" requirement: `S.full_ai` and every mixed variant are
generated for *the same prompt* as `S`, targeting *the same length* as
`S` — so any topic/length signal in the human corpus is mirrored on the
machine/mixed side by construction, not left to chance.

## 2. Where prompts come from (and a deliberate deviation from a generic
design)

An earlier sketch of this pipeline (before [DEC-009](decisions/DEC-009-human-dataset-source.md)
fixed the actual human corpus) imagined hand-authored prompt category
files like `personal_experience.json` or `academic_interest.json` — the
kind of prompt taxonomy that fits genuine admissions essays. That doesn't
fit the corpus DEC-009 actually selected: **PERSUADE 2.0 and ELLIPSE are
argumentative and independent-prompt student essays, on their own fixed
sets of prompts** (PERSUADE: 15 prompts across two task types; ELLIPSE:
44 independent prompts — corrected after acquisition; earlier research
had estimated ~29, see `dataset-source-comparison.md`) — not open-ended
personal-narrative topics.

So prompts are **extracted from the acquired corpus's own metadata**,
not invented ahead of time:

```
scripts/extract_prompts.py   (written and run, 2026-08-10)
  reads the acquired PERSUADE file
  groups essays by their existing prompt_name/task field
  writes data/prompts/persuade_2.0/<prompt_id>.json:
    { "prompt_id", "prompt_text", "task_type", "source_corpus",
      "essay_count", "length_stats_words": {"min", "median", "p10", "p90", "max"} }
```

This is deliberately a *derived* artifact (generated by a script from
real corpus metadata), not a hand-authored file — inventing specific
prompt text here would mean guessing at content that must instead come
from the real corpus. Run against the actual acquired PERSUADE file: 15
prompt files written to `data/raw`-adjacent `data/prompts/persuade_2.0/`
(gitignored, derived data), each with real instruction text pulled from
the `assignment` column (2 tests in `scripts/tests/test_extract_prompts.py`).

## 3. Full machine generation (`full_ai`)

For seed essay `S` with `prompt_id`, `task_type`, and `word_count`:

1. Build an instruction from the prompt's own text (extracted per
   Section 2) plus a target length: *"Write a [task_type] essay
   responding to: [prompt_text]. Target length: approximately
   [word_count] words."*
2. Generate with [DEC-010](decisions/DEC-010-machine-generation-model.md)'s
   model (Qwen2.5-1.5B-Instruct), with a **per-sample varied** generation
   config (temperature, top_p, seed all vary — see Section 7, Diversity)
   rather than one fixed config for every call.
3. Record actual length vs. target length (Section 5).

No text is spliced here — the entire output is the sample, labeled
`machine`, `ground_truth_confidence: "high"` (every token is AI-authored,
trivially certain).

## 4. Mixed/AI-assisted generation

Per [DEC-011](decisions/DEC-011-mixed-text-generation.md) (as redesigned
post-EXP-DATA-001), every mixed category falls into exactly one of three
ground-truth regimes:

### Regime A/B — Surgical-splice categories (exact ground truth)

`sentence_rewrite_single`, `sentence_light_controlled`,
`sentence_moderate_controlled`, `sentence_rewrite_multi`,
`paragraph_rewrite_single`, `paragraph_rewrite_multi`:

1. Segment `S` with the same sentence segmenter already built in Phase 2
   (`backend/app/services/sentence_segmenter.py`) — reusing this instead
   of a second implementation means the boundaries the detector will
   later see are the same kind the generation pipeline used.
2. Select target sentence(s)/paragraph(s) (word-count-filtered to avoid
   degenerate single-token "sentences").
3. Send only the target span plus one sentence of surrounding context on
   each side, with an instruction to transform just that span, preserving
   meaning and matching tone/context. **Instruction *intensity* (full
   rewrite vs. light copy-edit vs. moderate reword) is a parameter of
   this one mechanism** — `sentence_rewrite_single` and
   `sentence_light_controlled`/`sentence_moderate_controlled` differ only
   in which instruction wording is sent, not in how ground truth is
   produced.
4. Splice the result back into `S` at the exact original character
   offsets.
5. Record the exact sentence-index range replaced as `modified_spans`.
6. **Resegmentation safety check** (kept unconditionally, per explicit
   instruction not to relax it): re-segment the spliced essay and confirm
   the sentence count is unchanged. If it isn't — e.g. informal/run-on
   original punctuation causing the parser to disagree after a splice —
   **reject the sample** (`splice_resegmentation_mismatch`) rather than
   guess at which sentence index is now correct. EXP-DATA-001 caught 2
   real cases this way.

Ground truth here needs no diffing: we chose exactly which sentences
would be replaced, so we know exactly which ones are AI-authored,
regardless of instruction intensity.

### Regime C — Whole-essay categories (essay-level-only ground truth)

`light_polish`, `moderate_polish`, `heavy_revision`:

1. Send the whole essay with an instruction scoped to that severity.
2. **No sentence-level label is ever produced from this regime.**
   `modified_spans` is always `None`; `ground_truth_confidence` is always
   `"essay_level_only"`.
3. Sentence-level diffing/alignment (`generation_utils.align_and_diff_sentences`)
   MAY still be computed for this regime, but **strictly as a diagnostic**
   — detecting gross structural drift and logging an observed similarity
   range for documentation (as EXP-DATA-001's report did) — **never** to
   populate `modified_spans`. EXP-DATA-001 found this regime's
   transformations (measured: 70% structural drift, no sentence scoring a
   perfect similarity match even where alignment succeeded) make
   sentence-level attribution genuinely ambiguous, not just hard to
   threshold — see DEC-011's "Post-Pilot Methodology Redesign" for the
   full reasoning, including why a more sophisticated alignment algorithm
   was considered and rejected for producing labels (Alternative D there).
4. Structural drift observed during generation is logged as an
   informative QC note, not grounds for rejection — the essay-level claim
   ("this essay was AI-polished") holds regardless of how much internal
   restructuring occurred.

Usable for essay-level evaluation only; must be excluded from sentence/
passage-level evaluation metrics in Phase 10 (this exclusion is a
deliberate design choice to remember, not an oversight to catch later).

## 5. Length matching

Every generated/rewritten sample targets its seed essay's own word count
(±15%, chosen as a starting tolerance — not yet validated against real
output at scale, see Limitations), rather than one fixed length for a
whole batch. `target_length_words`, `actual_length_words`, and
`source_length_words` are all recorded per sample (see metadata schema,
Section 9) so the resulting length-distribution match (or mismatch) can
be measured directly during the pilot instead of assumed.

**Finding from a smoke test of DEC-010's model (2 generations, not the
full pilot):** phrasing a length request inside the instruction alone
("approximately 120 words") did not reliably constrain output length —
one test generation ran to 186+ words before hitting the `max_new_tokens`
cutoff rather than stopping near the requested target. Length control
therefore needs an explicit mechanism, not just a phrased request:
budget `max_new_tokens` more precisely from the target word count (with
a generous but bounded ceiling), and if the model still overruns, truncate
to the nearest sentence boundary at or before the target rather than
mid-sentence. This still needs to be implemented and checked against
real output distributions in EXP-DATA-001 — noted here now because it
was observed directly, not to be forgotten before that pilot is designed
in code.

## 6. Leakage prevention (hard invariant)

**Split assignment happens once, at the family level, before any
generation runs.** A seed essay is assigned to train/validation/test
first; every sample in its family is then generated "into" that same
split. Generating everything first and splitting afterward is the
specific ordering bug this invariant exists to prevent — see
[DEC-011](decisions/DEC-011-mixed-text-generation.md) and the existing
sentence-segmentation-level precedent in
[DEC-005](decisions/DEC-005-sentence-segmentation.md)'s discussion of
consistent boundaries.

## 7. Diversity

To avoid near-identical outputs for essays sharing a prompt (a known
failure mode of small instruction models under low-temperature/greedy
decoding), each generation call varies:

- **Temperature** and **top_p** — sampled per-call from a small range
  (e.g. temperature in [0.7, 1.0]), not fixed across a batch.
- **Seed** — unique per sample, but recorded, so any individual sample's
  generation is independently reproducible even though the batch as a
  whole isn't deterministic end-to-end.

## 8. Quality control (generation-failure checks, not difficulty checks)

Every generated/spliced sample is validated before being accepted into
the dataset. These check for **generation failures**, not for "this looks
ambiguous" — realistic mixed data should include genuinely ambiguous
cases, and QC must not quietly filter them out just because they'd be
hard to classify:

1. Non-empty output.
2. Length within an absolute floor/ceiling (catches truncated or runaway
   generations) and within the target-length tolerance band for
   full-generation samples.
3. No verbatim leakage of the **meta-instructional wrapper** into the
   output (`check_instruction_leakage`) — **compared only against the
   meta/wrapper language, never against the source prompt, target
   sentence/paragraph, or any other topic content the output is
   *expected* to legitimately reference.** EXP-DATA-001 found the
   original version of this check compared against the whole formatted
   instruction (including embedded prompt text) and produced false
   positives on every `full_ai` sample it flagged, since essays
   naturally echo their own assigned topic. Fixed 2026-08-10; regression
   test preserved in `scripts/tests/test_generation_utils.py`.
4. No AI self-reference (`check_ai_self_reference`) — a distinct check
   from instruction leakage, searching anywhere in the text (not just an
   opening preamble) for phrases like "as an AI language model."
5. No excessive repetition — reusing the repeated-bigram-ratio feature
   already built in `backend/app/services/feature_extractor.py` (Phase 3)
   against a generous ceiling, since a degenerate repetition loop is a
   known small-model failure mode and this project already has the
   exact measurement for it.
6. No leftover instruction-following artifacts (e.g. a "Sure, here's the
   rewritten sentence:" preamble the model failed to omit).
7. For Regime A/B (surgical-splice) samples: the final text must still
   segment cleanly with the same sentence segmenter, and `modified_spans`
   offsets must correctly slice the final text — the
   `splice_resegmentation_mismatch` check (Section 4) is a hard rejection
   here, unconditionally, since it's the guarantee the whole regime's
   "exact ground truth" claim rests on.
8. For Regime C (whole-essay) samples: structural drift is logged as an
   informative note, not a rejection reason (Section 4) — it no longer
   invalidates the sample now that Regime C makes no sentence-level claim.
9. Duplicate / near-duplicate detection: exact duplicates via a hash of
   normalized text; near-duplicates via n-gram overlap between
   full-generation samples that share a prompt (flagging, e.g., >0.6
   Jaccard similarity on word 5-grams as a candidate near-duplicate,
   pending real examples to check that threshold against).

**Every rejection is logged with its reason** (e.g. to
`data/generation_rejects.jsonl` once implemented) — never silently
discarded, per the explicit requirement to record rejection reasons
rather than just dropping hard cases.

## 9. Metadata schema

Every sample gets a record (illustrative example below — this is a
hand-written example for design review, not real generated data):

```json
{
  "sample_id": "persuade_00001__sentence_rewrite_single",
  "family_id": "persuade_00001",
  "source_corpus": "persuade_2.0",
  "prompt_id": "prompt_007",
  "label": "ai_assisted",
  "transformation_type": "sentence_rewrite_single",
  "source_sample_id": "persuade_00001",
  "modified_spans": [
    {"sentence_index": 4, "char_start": 812, "char_end": 941}
  ],
  "ground_truth_confidence": "high",
  "generation_model": "Qwen2.5-1.5B-Instruct",
  "generation_model_revision": "<pinned HF commit sha, not yet recorded>",
  "generation_config": {"temperature": 0.85, "top_p": 0.95, "seed": 4821},
  "prompt_template_id": "sentence_rewrite_v1",
  "target_length_words": 612,
  "actual_length_words": 609,
  "source_length_words": 612,
  "generation_timestamp": "2026-08-10T00:00:00Z",
  "qc_status": "passed",
  "qc_notes": []
}
```

Field notes:
- `family_id` is the leakage-prevention key (Section 6).
- `source_sample_id` is `null` for `human` and `full_ai` (no splice
  source); for mixed samples it points at the human original.
- `modified_spans` is `[]` for `human`, spans the whole text for
  `full_ai`, and lists exact sentence/char ranges for the surgical-splice
  categories; for diff-based categories it lists whichever sentences were
  judged AI-touched by the alignment check.
- `ground_truth_confidence` is one of `high` (splice or full generation),
  `approximate` (diff-based), `essay_level_only` (heavy revision).
- `qc_status` is `passed`, or a specific rejection reason (`empty_output`,
  `length_out_of_bounds`, `prompt_leakage`, `excessive_repetition`,
  `structure_drift`, `near_duplicate`, ...).

## 10. What this document does not cover yet

- A diff-similarity threshold for Regime C was investigated and
  deliberately **not set** — EXP-DATA-001 found no separable distribution
  to threshold, and Regime C no longer needs one (see Section 4).
- Length control for the new controlled-span light/moderate categories
  (Regime A) — check EXP-DATA-001-R1's findings; not yet confirmed
  whether span-level length drift is also a problem.
- `scripts/generate_samples.py`, `scripts/generate_mixed_samples.py`
  (full-scale, production versions) — still don't exist; should follow
  the three-regime structure once written. `scripts/extract_prompts.py`
  exists and has been run for real (Section 2).
- `sentence_rewrite_multi`, `paragraph_rewrite_multi` — designed, not yet
  exercised in any pilot.

## 11. Pilots run so far

**EXP-DATA-001** (2026-08-10, 60 samples, 10 seeds × 6 categories):
validated `full_ai` and the original surgical-splice categories; found
the whole-essay-diff mechanism for light/moderate polish did not produce
reliable sentence-level ground truth. Full results:
[reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md) — preserved as
project history, not overwritten by the redesign.

**EXP-DATA-001-R1** (2026-08-10, targeted validation of the post-pilot
redesign — controlled-span light/moderate categories, Regime C
reclassification, and the QC leakage fix): see
[reports/EXP-DATA-001-R1.md](../reports/EXP-DATA-001-R1.md).

Both are **data-generation validation experiments**, not
detector-performance evaluations — no classification or accuracy claim
is made from either.
