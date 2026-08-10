# EXP-DATA-001 — Generation Pipeline Pilot: Results

> Status: **executed for real**, 2026-08-10. 60 samples generated against
> the actual acquired PERSUADE 2.0 corpus using Qwen2.5-1.5B-Instruct.
> This report evaluates the **data generation pipeline only** — no
> detector was trained, run, or used to label anything, no detection
> accuracy/F1 is reported or implied. Raw output:
> `data/generated/EXP-DATA-001/samples.jsonl` and `diffs.json`
> (gitignored, not committed). Design doc (pre-registered hypothesis):
> `experiments/EXP-DATA-001-generation-pilot/README.md`.

## 1. Dataset / source IDs

- Human corpus: PERSUADE 2.0 (`data/raw/persuade_2.0/persuade_2.0_human_scores_demo_id_github.csv`),
  filtered to `task == "Independent"` essays only (13,121 of 25,996) to
  keep the pilot self-contained (no source-text dependency).
- License: CC BY-NC-SA 4.0 (live-verified, DEC-009).

## 2. Seed essay IDs

10 essays selected deterministically (`generation_utils.select_seed_essays`,
`rng_seed=42`) from candidates with 150–320 words, ≥5 sentences (proxy
count), ≥2 paragraphs (proxy count):

| Seed ID | Words | Prompt | Split |
|---|---|---|---|
| 18D47A791678 | 259 | Mandatory extracurricular activities | validation |
| 72173F3A0279 | 267 | Community service | test |
| 83D8EED426D9 | 221 | Mandatory extracurricular activities | train |
| 841F9E15D42E | 238 | Community service | train |
| 87186C957B20 | 163 | Cell phones at school | validation |
| 94330AB7CD65 | 272 | Community service | train |
| 9A7C858EF23B | 232 | Cell phones at school | train |
| C5566100FDF2 | 172 | Cell phones at school | train |
| DA723916BCC0 | 280 | Mandatory extracurricular activities | train |
| EE3DDDA7F1B7 | 290 | Phones and driving | train |

**Family-level split assigned before any generation ran**
(`generation_utils.assign_family_splits`, 70/15/15, `rng_seed=42`) — 7
train / 2 validation / 1 test. Verified after generation: **zero
family/split invariant violations** across all 60 samples (every sample
sharing a `family_id` has the same `split` — checked programmatically,
not just by construction).

## 3. Generation model / version

Qwen2.5-1.5B-Instruct (Apache-2.0), loaded via `transformers`. Model
revision string recorded per sample in `generation_model_revision`
(resolves to the model name since no pinned commit SHA was available from
this load path — noted as a minor reproducibility gap, see Recommendations).

## 4. Generation configurations

| Category | Temperature | Top-p | Notes |
|---|---|---|---|
| full_ai | 0.85 | 0.95 | |
| light_polish | 0.6 | 0.9 | lower temp, intended to reduce drift — did not prevent it (see §7) |
| moderate_polish | 0.6 | 0.9 | |
| sentence_rewrite_single | 0.8 | 0.95 | |
| paragraph_rewrite_single | 0.8 | 0.95 | |

Every sample has a unique generation seed (recorded per-sample in
`generation_config.seed`), so any individual sample is independently
reproducible even though the batch as a whole used varied
temperature/seed by design (Section 7 of generation-methodology.md).

## 5. Category counts

6 categories × 10 seeds = **60 samples**, exactly as planned: 10 human
originals (reused, not generated), 10 full_ai, 10 light_polish, 10
moderate_polish, 10 sentence_rewrite_single, 10 paragraph_rewrite_single.

## 6. Length statistics (words)

| Category | n | min | median | max | Original median (for comparison) |
|---|---|---|---|---|---|
| original (human) | 10 | 163 | 248.5 | 290 | — |
| full_ai | 10 | 147 | 270.5 | 319 | 248.5 |
| light_polish | 10 | 100 | 182.5 | 380 | 248.5 |
| moderate_polish | 10 | 101 | 156.5 | 203 | 248.5 |
| sentence_rewrite_single | 10 | 162 | 251.0 | 288 | 248.5 (splice barely changes essay length) |
| paragraph_rewrite_single | 10 | 94 | 239.5 | 272 | 248.5 |

**full_ai length control is reasonable** — median close to the original
median, spread mostly within the intended tolerance band.
**Polish-category length control is not** — light_polish ranges from
100 to 380 words against seeds around 250 words; moderate_polish
consistently *undershoots* (median 156.5 vs. 248.5). This is a
**real, measured failure of the length-matching design for these two
categories specifically** — see §15.

## 7. Transformation statistics

**Structure-drift rate for whole-essay-instruction categories was high:**

| Category | Families with structure_drift (sentence count mismatch) | Families that aligned |
|---|---|---|
| light_polish | 7 / 10 | 3 / 10 |
| moderate_polish | 7 / 10 | 3 / 10 |

Manual inspection of a structure_drift case (seed `18D47A791678`,
moderate_polish) confirms this is **real stylistic consolidation by the
model**, not a segmentation bug: the model merged multiple original
sentences into fewer, more fluent ones even under an instruction
explicitly forbidding that ("do not add or remove sentences"). Example:

> Original: *"Students should participate in at least one extracurricular
> activities because they will earn respect from there teachers and
> classmates. its also a chance for them to show off there talents..."*
> (2 sentences)
>
> Moderate polish: *"Participating in one extracurricular activity will
> help students build relationships with both their teachers and peers,
> showcasing their abilities and potentially earning accolades..."*
> (1 sentence — genuinely consolidated, not a segmenter artifact)

**Diff-similarity distribution, for the families that did align** (3 of
10 each category; `difflib.SequenceMatcher` ratio per aligned sentence
pair, 1.0 = identical):

- light_polish: 24 sentence pairs, ratios ranged **0.07 to 0.85**, no
  pair scored a perfect 1.0.
- moderate_polish: 38 sentence pairs, ratios ranged **0.09 to 0.97**,
  one near-1.0 pair.

**No clean threshold emerges from this distribution.** It is
continuous/spread, not bimodal — there is no visible gap separating
"lightly touched" from "heavily touched" sentences. Per this experiment's
explicit instruction not to invent or force an unjustified threshold,
**no numeric similarity threshold is being fixed in DEC-011 based on
this pilot.** This is itself a finding: it suggests the underlying
assumption (that a "light polish" instruction produces a mix of
touched/untouched sentences with a recoverable diff threshold) does not
hold for this model at this instruction wording, rather than that the
threshold merely needs tuning.

**Surgical-splice categories performed much better:**
- `sentence_rewrite_single`: 6 passed cleanly, 2 flagged (false-positive
  prompt-leakage, see §16), 2 rejected for a real correctness issue
  (`splice_resegmentation_mismatch` — see §13).
- `paragraph_rewrite_single`: 9 passed cleanly, 1 flagged (same
  false-positive leakage pattern).

## 8. Duplicate findings

**Zero near-duplicates found** — checked pairwise (heuristic:
normalized prefix/suffix/length signature) across the 10 `full_ai` texts
alone, and again across all 50 generated/transformed (non-human) texts.
No duplication concern from this pilot.

## 9. QC pass/rejection counts

| Category | passed | flagged | rejected | skipped |
|---|---|---|---|---|
| original (human) | 10 | 0 | 0 | 0 |
| full_ai | 7 | 3 | 0 | 0 |
| light_polish | 1 | 2 | 7 | 0 |
| moderate_polish | 1 | 2 | 7 | 0 |
| sentence_rewrite_single | 6 | 2 | 2 | 0 |
| paragraph_rewrite_single | 9 | 1 | 0 | 0 |

No sample was skipped for lacking a suitable sentence/paragraph target
(all 10 seeds had a qualifying sentence and paragraph). All rejections
are logged with specific reasons in `samples.jsonl`'s `qc_notes` field —
none were silently discarded.

## 10. Sentence-level provenance validation

- All 33 `modified_spans` character ranges checked (across passed/flagged
  `sentence_rewrite_single` and `paragraph_rewrite_single` samples)
  correctly slice non-empty text at the recorded offsets — **zero
  invalid spans**.
- The `splice_resegmentation_mismatch` check (re-segmenting the spliced
  essay and confirming sentence count is unchanged) caught **2 real
  cases** where a single-sentence replacement, once spliced back,
  produced a different sentence count on re-parse — both correctly
  rejected rather than silently producing wrong ground truth (see §13).

## 11. Metadata validation

All 60 records contain every required schema field (`sample_id`,
`family_id`, `split`, `source_corpus`, `label`, `transformation_type`,
`source_sample_id`, `text`, `actual_length_words`, `target_length_words`,
`ground_truth_confidence`, `modified_spans`, `generation_config`,
`qc_status`, `qc_notes`) — checked programmatically, zero missing fields.

## 12. Examples of successful transformations

**full_ai** (seed `18D47A791678`, target 259 words, actual 279, passed
cleanly):
> *"I strongly believe that the inclusion of extracurricular activities
> as a requirement for all students is not only beneficial but essential
> for their holistic development. Extracurricular involvement offers
> numerous advantages that extend beyond academic performance,
> including social skills enhancement, leadership abilities, and
> personal growth opportunities..."*

Coherent, on-topic, well-structured — no leakage, no repetition, no
artifacts.

**sentence_rewrite_single** (seed `DA723916BCC0`, passed cleanly):
splice replaced one sentence with: *"Students will feel pressure on
themselves due to their desire to excel academically, and stress is also
inevitable when engaging in activities or sports."* — meaning preserved,
fits the surrounding context, `modified_spans` correctly identifies
exactly this one sentence.

**paragraph_rewrite_single** (seed `94330AB7CD65`, passed cleanly):
one paragraph replaced with a single well-formed sentence about
community service's environmental benefits — `modified_spans` correctly
resolves to exactly the sentence(s) inside the replaced paragraph's
character range.

## 13. Examples of failed transformations

**structure_drift** (seed `18D47A791678`, moderate_polish, rejected):
see the full before/after quoted in §7 — the model consolidated two
sentences into one despite explicit instruction not to change sentence
count.

**splice_resegmentation_mismatch** (seed `9A7C858EF23B`,
sentence_rewrite_single, rejected — `orig=14 sentences, spliced=15`):
the original essay is written in an informal, run-on style typical of
student writing (commas where periods might otherwise appear). The
rewritten replacement sentence uses more standard punctuation, and upon
re-segmenting the spliced essay, the parser found one additional sentence
boundary versus the original. **This QC check worked exactly as
intended** — it caught a real ground-truth risk (the `modified_spans`
would otherwise have pointed at the wrong sentence index) and rejected
the sample rather than silently producing incorrect provenance.

**False-positive prompt_leakage** (seed `87186C957B20`, full_ai, flagged
but not rejected): the check flagged a 6-word overlap between the
generation instruction and the output. Manual inspection found the
overlapping phrase — *"phones to school and use them"* — came from the
**essay prompt itself** (the instruction embeds the full prompt text,
and the essay legitimately discusses the policy described in that
prompt). Re-running a corrected check that excludes the prompt-text
portion of the instruction (keeping only the instructional wrapper
language) found **zero genuine leakage** in any of the 3 originally
flagged `full_ai` samples. **This is a QC check design flaw, not a
generation quality problem** — see §16.

## 14. Is Qwen2.5-1.5B-Instruct's quality sufficient?

**Nuanced, category-dependent answer, not a single yes/no:**

- **Full generation:** Yes — coherent, on-topic, no leakage/repetition/
  artifact issues found, reasonable length control. 7/10 passed cleanly,
  3/10 only flagged by what turned out to be a false-positive check
  (§16) — effectively 10/10 on manual review.
- **Surgical sentence/paragraph rewrite:** Yes — 6/10 and 9/10 passed
  cleanly respectively; the "failures" were either a false-positive QC
  check or a real (correctly caught) edge case, not bad generations.
- **Whole-essay light/moderate polish: No, not as currently designed.**
  The model does not reliably perform a light, structure-preserving edit
  when instructed to — it substantially rewrites content and often
  changes sentence count regardless of instruction wording. This may be
  a genuine model-capability limit (worth testing Phi-3.5-mini-instruct,
  DEC-010's documented escalation path, in a follow-up pilot) or may be
  addressable by fixing the *methodology* (see §16/§17) rather than the
  model. Not yet determined which — flagged as the top open question.

## 15. Is the current length-control strategy sufficient?

**No, not uniformly.** `budget_max_new_tokens` +
`truncate_to_word_budget` worked reasonably for `full_ai` (median close
to target). It does **not** meaningfully constrain `light_polish`/
`moderate_polish` output length, because those categories don't truncate
against a fixed target the way `full_ai` does — they're bounded only by
`max_new_tokens` sized from the *original* essay's length, and the model
frequently stops (or is asked to, via EOS) well short of or beyond that,
producing the 100–380 word spread observed. **Needs a dedicated length
mechanism for the polish categories**, not just reuse of the `full_ai`
approach — recorded as an open item, not fixed here.

## 16. What thresholds/configurations need revision

1. **`check_prompt_leakage` is measuring against the wrong scope.** It
   compares the *entire* instruction (including the embedded prompt
   text) against the output. Since essays are expected to reference their
   prompt, this produces false positives whenever a `full_ai` essay
   legitimately engages with its topic. **Fix:** compare only against the
   instructional wrapper text, excluding the prompt/target-sentence/
   target-paragraph content that the output is *supposed* to echo.
2. **Diff-similarity threshold for light/moderate polish cannot be
   responsibly fixed from this pilot's data** (§7) — the distribution is
   continuous, not separable, and the structure-drift rate (70%) means
   most families didn't even produce a comparable pair set. Setting a
   number now would be exactly the "invented, unjustified threshold"
   this experiment was designed to avoid.
3. **The alignment rule itself (`align_and_diff_sentences`, DEC-011)
   is too strict.** Requiring an *exact* sentence-count match before
   attempting any alignment discards 70% of polish-category attempts
   outright, even when much of the essay may be genuinely comparable
   sentence-by-sentence with only a local merge/split. See §17 for the
   proposed fix.
4. **`max_new_tokens` budgeting for `light_polish`/`moderate_polish`**
   needs its own target-length mechanism (§15), not reuse of the
   `full_ai` approach.

## 17. Recommendations before scaling

**Do not scale in the current form.** Specifically:

1. **Fix `check_prompt_leakage`** to exclude prompt/target-text content
   from the comparison (a straightforward code fix, not a methodology
   rethink) — do this before any further generation, since it's actively
   producing misleading QC signal right now.
2. **Redesign sentence alignment for the polish categories** away from
   "exact count match or reject" toward a proper sequence-alignment
   algorithm (e.g. `difflib.SequenceMatcher` operating on the *list* of
   sentences, using `get_opcodes()` to identify equal/replace/insert/
   delete blocks). This would recover usable — if coarser, block-level
   rather than strictly 1:1 — ground truth for most of the 70% currently
   rejected outright, instead of discarding them. This is a proposed
   fix, **not implemented in this pilot** (implementing and re-piloting
   it is explicitly out of scope for this stop point).
3. **Add explicit length control to the polish categories** — a
   dedicated target-length mechanism, not reuse of `full_ai`'s.
4. **Run a small follow-up pilot specifically on the polish categories**
   after the above fixes, before deciding whether the model itself
   (escalating to Phi-3.5-mini-instruct per DEC-010) also needs to
   change — don't conflate a methodology fix with a model change; test
   them one at a time.
5. **Minor:** raw PERSUADE text contains non-breaking-space characters
   (`\xa0`) that survived normalization into a couple of spliced
   outputs (cosmetic, not a correctness issue, but worth adding to
   `text_normalizer.py`'s scope in a future pass).
6. **Minor:** `generation_model_revision` currently falls back to the
   bare model name rather than a pinned commit SHA — worth capturing the
   actual revision hash at load time for stronger reproducibility.
7. **Keep the surgical-splice mechanism (sentence/paragraph rewrite)
   largely as-is** — it performed well; the `splice_resegmentation_
   mismatch` check is working correctly and should be kept.
8. **Keep `full_ai` largely as-is** — length control and quality were
   both reasonable.

## Explicit non-findings

This report makes no claim about detector accuracy, precision, recall,
or generalization — no detector was involved in producing or judging any
sample in this pilot.
