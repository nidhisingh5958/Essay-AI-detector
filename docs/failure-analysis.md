# Failure Analysis

This document has two parts, kept explicitly separate so neither is
mistaken for the other:

1. **Data generation pipeline failures** (below) — real, already found
   during EXP-DATA-001. These are failures of the *dataset construction*
   process, not the detector.
2. **Detector failures** (Phase 11, still a placeholder) — no detector
   exists yet, so this part remains empty until one does.

---

## Part 1: Data Generation Pipeline Failures (EXP-DATA-001 through R3, 2026-08-10 to 2026-08-13)

Preserved here per explicit instruction not to erase or minimize them.
Full context: [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md),
[reports/EXP-DATA-001-R1-confirmation.md](../reports/EXP-DATA-001-R1-confirmation.md),
[reports/EXP-DATA-001-R2.md](../reports/EXP-DATA-001-R2.md),
[reports/EXP-DATA-001-R3.md](../reports/EXP-DATA-001-R3.md),
[DEC-011](decisions/DEC-011-mixed-text-generation.md),
[DEC-012](decisions/DEC-012-semantic-preservation-screen.md),
[DEC-013](decisions/DEC-013-claim-survival-screen.md).

**The single most important finding across all of these experiments,
stated plainly and preserved as permanent project history — see Failure
4 for detail:**

> **Structural QC can pass samples that nevertheless alter the author's
> meaning.**

This is not a one-off bug that got fixed and closed. It is a validated
property of this generation pipeline that shaped its entire subsequent
design (the semantic-preservation review protocol, DEC-012's automated
screen, and the sentence/paragraph-separated evidence tracking in
DEC-011) and must not be quietly forgotten or re-litigated by future work
on it.

**Where this evidence led, 2026-08-13**: the failures documented below
(especially Failures 4, 7–8, 11–12) are the direct basis for the
post-R3 strategic decision to include only `sentence_light_controlled_v2`
in the primary dataset and exclude `sentence_moderate_controlled_v2` and
both paragraph-level categories, and to reframe the automated screens as
risk-triage tools rather than a safety gate. See
[final-decision-guide.md](final-decision-guide.md) and
[DEC-011](decisions/DEC-011-mixed-text-generation.md)'s "Strategic
Decision" section. None of the failures below are superseded or
invalidated by that decision — they are its evidentiary basis, and
remain permanent project history regardless of which categories a future
dataset revision includes.

### Failure 1: Whole-essay light/moderate polish does not produce reliable sentence-level ground truth

**What was attempted:** send a whole human essay to Qwen2.5-1.5B-Instruct
with an instruction to lightly or moderately polish it, then diff the
before/after sentences to label which ones the model touched.

**What happened:** 70% of families (7/10) in both `light_polish` and
`moderate_polish` failed an exact-sentence-count alignment check —
manually confirmed as genuine sentence consolidation by the model (it
merges sentences despite explicit instructions not to), not a
segmentation bug. Among the 30% that did align, similarity scores were
continuous across the full range (0.07–0.97) with no separation between
"touched" and "untouched" sentences — no sentence in `light_polish`
scored a perfect match even where alignment succeeded.

**Why it failed:** the underlying assumption — that a "light polish"
instruction produces a *recoverable mix* of touched and untouched
sentences — does not hold for this model at this instruction wording.
This is a property of how the model edits, not a measurement problem
solvable with a better threshold or a smarter alignment algorithm (a
sequence-alignment-based fix was considered and specifically rejected for
this reason — see DEC-011).

**What changed as a result:** whole-essay polish was reclassified as
essay-level-only ground truth (Regime C) and is never used for
sentence-level claims. A new controlled-span mechanism (apply light/
moderate instructions to a single pre-selected sentence, then splice)
replaced it as the source of sentence-level light/moderate examples —
targeted-validated in EXP-DATA-001-R1
([report](../reports/EXP-DATA-001-R1.md)).

### Failure 2: Prompt-leakage QC check flagged legitimate on-topic essays

**What was attempted:** detect generation failures where the model
echoes its own instructions instead of producing real content, by
checking for 6-word overlaps between the instruction and the output.

**What happened:** all 3 `full_ai` samples this check flagged were false
positives. The overlapping phrases came from the *essay prompt* embedded
in the instruction (e.g. "...bring their phones to school and use
them...") — the essay was legitimately discussing the policy it was
asked to write about.

**Why it failed:** the check compared against the *entire* formatted
instruction, including prompt/target content the output is *expected* to
reference, rather than only the instructional meta-language.

**What changed as a result:** `check_prompt_leakage` was replaced with
`check_instruction_leakage`, which requires callers to pass only the
meta-instructional wrapper text. A regression test preserves the
original failure case in `scripts/tests/test_generation_utils.py` so it
cannot silently reappear.

### Failure 3 (a correctly-caught edge case, not a bug): resegmentation mismatch after sentence splicing

**What was attempted:** splice a rewritten sentence into an essay at
exact character offsets, then re-segment the spliced essay to confirm
the sentence count is unchanged (a safety check on the surgical-splice
mechanism's ground-truth guarantee).

**What happened:** 2 of 10 `sentence_rewrite_single` samples failed this
check — the original essay's informal, run-on punctuation style caused
the parser to find a different sentence boundary after the rewritten
(more standard-punctuation) sentence was spliced in.

**Why this is listed as a "failure" but not a bug:** the QC check did
exactly what it was designed to do — catch a case where `modified_spans`
would otherwise have pointed at the wrong sentence index — and rejected
the sample rather than silently producing incorrect ground truth. Listed
here as evidence the safety mechanism works, and as a reminder that
informal/non-standard punctuation in real student writing is a genuine
source of segmentation disagreement worth being aware of elsewhere in the
pipeline (e.g. Phase 3 feature extraction).

### Failure 4: structural QC does not catch semantic drift at the sentence level

**What was attempted:** validate that `sentence_light_controlled`/
`sentence_moderate_controlled` samples (surgical splice, "exact ground
truth" by construction) actually produce faithful light/moderate edits,
using length-ratio and resegmentation checks as the quality gate.

**What happened:** in EXP-DATA-001-R1-confirmation (50 records, 10
previously-unseen seeds), manual semantic review found **4 samples that
passed every automated check** (`qc_status: "passed"`, `resegmentation_ok:
true`, length ratio within bounds) had still changed the essay's actual
meaning. Concretely: `BCB916A9A9F3__sentence_moderate_controlled` altered
a factual detail from "at least one C" to "two Cs" — a number changed,
not just phrasing. `4C3FC32093AB__sentence_light_controlled` and its
moderate sibling both replaced a specific grievance ("students...cant get
involved because of their C average") with a generic, unrelated sentence
("I think...you need to address this issue") carrying no equivalent
claim. Combined across both sentence-level categories: 33% of reviewed
samples were judged `"preserved"`, 47% `"changed"`.

**Why it failed:** length ratio and resegmentation validate *structure*
(did the span stay the right size, does the essay still parse into the
same sentence count) — neither one reads the text for meaning. A rewrite
can be the "right" length and sit in a perfectly valid sentence boundary
while still saying something different from the original.

**What changed as a result:** a `semantic_preservation` field was added
(`not_yet_reviewed`/`preserved`/`questionable`/`changed`), populated only
by manual human review — never by a model call, which would just move the
same blind spot into a different opaque check. DEC-011 records
sentence-level controlled transformation as **not ready for scale**
pending one of: a second automated signal that can catch this, mandatory
semantic review as a gate, or more surrounding context per edit. Full
results: [reports/EXP-DATA-001-R1-confirmation.md](../reports/EXP-DATA-001-R1-confirmation.md).

### Failure 5: structural-artifact insertion during single-sentence rewrite

**What happened:** `3AF8147D6DB0__sentence_moderate_controlled` (asked to
moderately reword one sentence) produced output beginning with
`"Sincerely,\n\n"` — a letter-closing artifact with no relationship to
the single-sentence instruction — before the actual reworded content.
Passed structural QC (correct length, correct resegmentation) because
neither check inspects content for this kind of artifact.

**Why it failed:** the model appears to occasionally default to
letter/email formatting conventions regardless of the specific,
narrowly-scoped instruction given. Not investigated further (single
occurrence in this round); worth watching for recurrence at larger scale.

**What changed as a result:** nothing yet — recorded as a data point
supporting Failure 4's broader conclusion (structural QC is
insufficient), not as a separate fix. If this recurs at scale, a
dedicated "no letter-formatting artifacts" check would be a reasonable,
narrowly-scoped addition.

### Failure 6 (a correctly-diagnosed measurement bug, not a generation problem): `difflib` `autojunk` understated similarity

**What happened:** while building the family-aware near-duplicate check,
a fixture test showed `difflib.SequenceMatcher` scoring a single-word
change in a ~200-character sentence as ~0.28 similarity — clearly wrong
for what's almost the same sentence. Root cause: `SequenceMatcher`'s
default `autojunk=True` treats characters as "popular" (excluded from
matching) once a sequence passes 200 characters.

**Why this matters beyond the immediate fix:** `align_and_diff_sentences`
(used in EXP-DATA-001 to compute Regime C's similarity range, 0.07–0.97)
had the same unfixed default. The fix (`autojunk=False`) was applied, but
EXP-DATA-001's specific similarity numbers were not recomputed
retroactively — they should be read as approximate, not exact, going
forward. The *structural* finding from that pilot (70% sentence-count
mismatch) is unaffected, since it's a count comparison, not a similarity
score.

**What changed as a result:** `autojunk=False` added to both
`SequenceMatcher` call sites; a regression test
(`test_align_and_diff_sentences_does_not_understate_similarity_for_long_sentences`)
added to `scripts/tests/test_generation_utils.py` to keep this caught.

### Failure 7: paragraph-level rewrites can drop an entire claim while passing length-ratio QC

**What was attempted:** validate that `paragraph_light_controlled`/
`paragraph_moderate_controlled` (previously the more reliable of the two
regimes) hold up on a fresh set of seeds
(EXP-DATA-001-R2, [report](../reports/EXP-DATA-001-R2.md) §1).

**What happened:** both the light and moderate rewrites of one seed
(`DB12BA4206B8`) dropped the paragraph's entire opening claim/framing
("Community service. It's what prisoners and volunteers do each and
every day.") while otherwise reading as faithful paraphrases of the rest
of the paragraph. Both passed structural QC (length ratio 1.05–1.07, well
within bounds) because expanding wording elsewhere compensated for the
dropped sentence's length.

**Why it failed:** length-ratio QC checks the *aggregate* size of the
rewritten span, not whether every claim in the original survived
somewhere in the output. A rewrite can lose a whole sentence's worth of
content and still land inside a length-ratio window if it's verbose
elsewhere.

**What changed as a result:** nothing implemented yet — recorded as
concrete evidence that paragraph-level, despite being the more reliable
regime overall, is **not yet ready for scale** (DEC-011's
category-specific conclusion) and needs a claim-survival check (e.g.
verifying major entities/claims from the original appear somewhere in
the rewrite) before it can be.

### Failure 8 (partially resolved, not eliminated): sentence-level `moderate` instruction wording drives most remaining semantic drift

**What was attempted:** EXP-DATA-001-R2 redesigned the sentence-level
mechanism (full-paragraph context instead of one sentence before/after)
and, critically, held temperature/top_p **constant** between light and
moderate for the first time — removing the confound present in
EXP-DATA-001-R1-confirmation (which used temperature 0.5 for light, 0.7
for moderate, making it impossible to attribute the difference between
them to either cause).

**What happened:** with the confound removed, `sentence_light_controlled_v2`
reached 9/10 preserved and 0/10 changed (from 33%/47% before) — a large
improvement. `sentence_moderate_controlled_v2` still showed 3/9 (33%)
changed — a real, substantial improvement from before, but not resolved.
Observed drift included a descriptive claim turned prescriptive, a
complete topic substitution, and a causal/agent reversal (a complaint
about who should do community service was flipped in direction).

**Why it failed (as far as this evidence shows):** with context and
temperature no longer differing between the two categories, the
remaining difference points at the **instruction wording itself** —
"moderately reword... for clarity and flow" appears to license more
substantive rewriting than "lightly copy-edit," and that latitude is
what produces drift.

**What changed as a result:** DEC-011 now records
`sentence_light_controlled_v2` as promising enough for a further, larger
validation round on its own, while `sentence_moderate_controlled_v2`
remains not ready, with the *next* fix now localized to instruction
redesign specifically (not more context, not temperature) — not yet
attempted.

### Failure 9 (a correctly-diagnosed measurement bug, not a generation problem): paragraph-level screen input silently truncated when sentences merge

**What was attempted:** while building the claim-survival screen
(DEC-013) for paragraph-level rewrites, test the new sentence-coverage
signal against `DB12BA4206B8` — the one real sample manually labeled
`"changed"` for claim omission (Failure 7) — to see whether the signal
would have caught it.

**What happened:** the test initially appeared to succeed (a coverage
drop was detected), but investigation found this was an artifact, not a
real detection: `apply_automated_screen.py`'s `extract_span_pair`
reconstructed the "rewritten" half of the comparison pair from
`modified_spans` character offsets. When the rewrite merged two original
sentences into one, the resegmented `modified_spans` range covered only
part of the new paragraph, silently dropping the merged sentence's text
from what the screen actually compared. Re-reading the *actual* rewrite
text directly (not through this extraction) shows the claim in question
("prisoners and volunteers...") reads as preserved, not dropped, in the
text currently on disk — all four original sentences score 0.63–0.73
against their best match once the extraction bug is fixed.

**Why it matters beyond the immediate fix:** this same `extract_span_pair`
function supplies DEC-012's automated screen's input for paragraph
categories too — meaning some of EXP-DATA-001-R2's already-reported
`automated_screen_*` values for paragraph samples may have been computed
against truncated rewritten text. **Not retroactively recomputed** —
per explicit instruction to preserve existing evidence, EXP-DATA-001-R2's
sample file and report are frozen as-is; this caveat is recorded instead
of silently "fixing" historical numbers. It also means the specific
factual basis for `DB12BA4206B8`'s `"changed"` manual label (originally
attributed to a dropped opening claim) is now in question — the record
itself was not altered to investigate further, since doing so would mean
editing frozen, preserved evidence.

**What changed as a result:** `extract_span_pair` now reconstructs
paragraph-level pairs by splitting both the original and rewritten essay
text on the same paragraph index, instead of from `modified_spans`
offsets — robust because splicing only changes characters within one
paragraph, so paragraph boundaries elsewhere are unaffected by
construction. Regression tests added
(`scripts/tests/test_apply_automated_screen.py`). Applies going forward,
starting with EXP-DATA-001-R3. See DEC-012's "Out-of-Sample Validation"
section and DEC-013 for full detail.

### Failure 10 (a correctly-caught edge case, not a bug): sentence segmenter can bundle a salutation into the first "sentence," and a rewrite can drop it

**What was attempted:** EXP-DATA-001-R3's sentence-light larger
confirmation (25 fresh seeds, `sentence_light_controlled_v2`, otherwise
identical mechanism to EXP-DATA-001-R2).

**What happened:** for seed `B71DB7CEB4A8`, the human essay opens `"Dear
Principal,\n\nIn my opinion I say that Policy 1 is a whole better than
Policy 2."` — because there is no terminating punctuation after "Dear
Principal,", the sentence segmenter treats the salutation and the first
real sentence as one combined "sentence." That combined span became the
rewrite target; the model's light-edit rewrite of the opinion clause
dropped the salutation entirely, shrinking the span enough to trip
`modification_scope_drift` (length ratio 0.65, outside the [0.7, 1.3]
window) — correctly flagged, not silently passed.

**Why this is listed as a "failure" but not a bug:** same pattern as
Failure 3 — the QC check did exactly what it exists to do. On manual
review the underlying opinion claim itself was judged `preserved`; the
salutation loss isn't a claim/fact/entity change by
generation-methodology.md Section 12's protocol, but it is a real,
disclosed side effect of a segmentation edge case interacting with the
generation mechanism, worth being aware of at larger scale (letter-style
essays with informal punctuation after a greeting are common in this
corpus).

**What changed as a result:** nothing implemented yet — recorded as a
data point. If this recurs at scale, excluding a leading
salutation-only fragment from the rewrite-target candidate pool would be
a narrowly-scoped fix.

### Failure 11: paragraph-level `moderate` rewrite lost track of the essay's first-person narrator identity

**What was attempted:** EXP-DATA-001-R3's paragraph claim-survival
validation (12 fresh seeds, unchanged paragraph mechanism).

**What happened:** `80664125F8D0__paragraph_moderate_controlled` (a
student's letter about sports-eligibility grade requirements, written
first-person as "I currently hold a C in two classes... I enjoy
soccer...") was rewritten starting **"As a teacher, I support..."** and
continued **"I'm receiving a C in two of my classes, which means I won't
be eligible to try out for the sports I wish to join"** — internally
incoherent (a teacher would not be trying out for student sports). The
model lost track of who the first-person narrator is mid-rewrite.

**Why it failed:** not investigated further (single occurrence); a
plausible contributor is that "moderate" instruction wording licenses
more restructuring latitude, and restructuring a first-person student
narrative under that latitude apparently allows the model to drift into
a different, generic persona ("as a teacher") that doesn't fit the
content that follows it.

**What changed as a result:** nothing implemented yet. Notable
downstream effect: this sample WAS flagged by both the DEC-012 and
DEC-013 automated screens, but only because of an unrelated fact-check
false positive on date phrasing in the same paragraph — neither screen
actually detected the identity swap itself (see Failure 12 and
DEC-012/DEC-013 for the broader pattern this round). Recorded as a data
point for any future work on paragraph-level moderate rewriting.

### Failure 12: the automated semantic screens' "0 changed mislabeled preserved" safety property broke for the first time

**What was attempted:** validate DEC-012's automated semantic screen
(previously 0/8 calibration, 0/5 EXP-DATA-001-R2 out-of-sample) and the
new DEC-013 claim-survival screen against EXP-DATA-001-R3's fresh
paragraph batch.

**What happened:** 2 of 3 real `"changed"` paragraph samples this round
were labeled `likely_preserved`/`no_omission_signal` by both screens —
`1F8012FFBEBE__paragraph_light_controlled` (a stated-priority reversal:
the rewrite says the opposite of what the original promised to
prioritize) and `62AA2FDC41C6__paragraph_light_controlled` (a dropped
claim merged with a location/mechanism flip inside one garbled
sentence). Both score high embedding similarity and touch no number or
named entity, so neither the fact-check nor the coverage signal had
anything to catch.

**Why it failed:** both screens fundamentally measure lexical/structural
similarity (embeddings) or presence-of-a-counterpart (coverage) — neither
has a mechanism for detecting that a structurally-similar, fluent
sentence states the *opposite* meaning of the original, or that a merged
sentence quietly drops one of two claims it's supposed to carry. This is
precisely the gap DEC-012 flagged as theoretical when it was written
("not observed in this calibration set, but not proven absent either")
— now directly observed, three validation rounds later.

**What changed as a result:** both DEC-012 and DEC-013 updated to state
this plainly rather than continuing to claim a clean record; NLI/
entailment (DEC-012's Alternative B, previously deferred) is now a live
candidate for a future round, since it's specifically suited to
detecting contradiction/reversal that these similarity-based signals
cannot. **Not implemented in this round** — this is a finding to review,
not a fix already made. The standing rule that human review is
mandatory regardless of screen label — already in place — is now backed
by a concrete failure case, not just a theoretical justification.

---

## Part 2: Detector Failures

> Status: not started. There is no trained/calibrated detector yet to
> produce failures from (see [project-status.md](project-status.md)).
> This part remains a placeholder for the required structure (Section
> 15/39) — it will be populated with at least three real,
> confidently-wrong examples once evaluation (Phase 10) has actually run,
> never with invented ones.

### Required structure per failure case (Phase 11)

For each of at least three essays the detector confidently gets wrong:

1. The essay/passage sample
2. Ground truth label
3. The system's prediction and stated confidence
4. The actual feature values that drove the (wrong) prediction
5. An analysis of why the detector likely failed — tied to specific
   feature behavior, not speculation
6. A concrete idea for how the system could improve, ideally phrased as a
   testable follow-up experiment

### Ground rule

These cases will not be hidden or cherry-picked to look better than they
are (Section 15: "Do not hide these examples"). The purpose of this
section is to demonstrate understanding of the system's real failure
modes, which is only possible once the system exists and has been run
against held-out data.
