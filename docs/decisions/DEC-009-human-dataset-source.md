# DEC-009 — Human Dataset Source

## Status
Accepted (updated 2026-08-10 after live verification + file inspection —
see "Live Verification & Inspection Update" below; originally recorded as
Provisional based on web research only)

## Date
2026-08-10 (original); updated same day after acquisition

## Context

Phase 5 (dataset) cannot proceed responsibly without first establishing
where human-written text comes from, with real provenance and licensing —
not just picking whatever is largest or easiest to scrape. A full
comparison of candidate sources is in
[dataset-source-comparison.md](../dataset-source-comparison.md), built
from actual web research (cited there) rather than assumption, since
fabricating licensing/provenance claims is explicitly disallowed (Section
12 of the project brief) and would be far worse than admitting a source
is imperfect.

## Problem

Which human-writing source(s) should this project actually acquire and
build reference distributions from?

## Alternatives Considered

Full detail in [dataset-source-comparison.md](../dataset-source-comparison.md).
Summary:

### PERSUADE 2.0 (Learning Agency Lab)
Advantages: ~25,000 essays, real students (grades 6–12), strong
provenance (research-program-collected, not scraped), rich demographic
metadata, 15 prompts across two task types for topic diversity,
plain-text and clean for sentence-level analysis, CC-licensed.
Disadvantages: domain mismatch — argumentative/persuasive essays, not
personal-narrative admissions writing; a license-framing discrepancy
between two sources (CC BY-NC-SA 4.0 vs. CC BY 4.0) that must be resolved
against Kaggle's authoritative metadata before download.

### ELLIPSE Corpus (Vanderbilt / Learning Agency Lab)
Advantages: ~6,500 essays, strong provenance (standardized-testing-
collected), and — uniquely among every candidate found — genuine,
appropriately-collected English-language-proficiency labels, which
Section 16's fairness analysis needs and which the project must not
substitute by inferring language background from the writing itself.
Disadvantages: smaller than PERSUADE; same domain mismatch (independent-
prompt essays, not admissions narratives); same license family
(CC BY-NC-SA 4.0, consistent across sources this time).

### ICLE (International Corpus of Learner English)
Advantages: strong academic provenance, decades-established corpus.
Disadvantages: access is web-interface-only under the license terms
found (bulk text download explicitly disabled in the trial; free access
promised from 2026-09-15 but not confirmed to include bulk export) —
incompatible with a reproducible, scriptable acquisition pipeline.
Rejected for now, not permanently.

### TOEFL11 / ETS Corpus of Non-Native Written English
Advantages: excellent provenance, real L1-background labels across 11
languages with score levels — exactly the kind of appropriately-labeled
data a deeper fairness analysis could use.
Disadvantages: distributed via LDC under a paid membership/license
agreement — real cost and process overhead not yet initiated, and not
justified when PERSUADE + ELLIPSE already unblock Phases 5–6 for free.
Deferred, not rejected outright — worth reconsidering if ELLIPSE's
labels prove insufficient for the fairness analysis in Phase 12.

### Official "Essays That Worked" college-published admissions essays
Advantages: the best possible domain match — these are real admissions
essays.
Disadvantages: licensing is per-essay institutional permission granted to
one specific publisher, not a corpus license; scraping would exceed the
consent scope the contributing students gave and likely violate each
site's Terms of Use, and these are personal, identifying narratives from
minors/recent minors. Rejected — this is the textbook case of prioritizing
domain fit over provenance/licensing, which Section 12 and this task's
instructions explicitly warn against.

### Reddit / online essay-feedback forums
Advantages: real, voluntarily-shared draft admissions essays.
Disadvantages: privacy/consent risk to a largely-minor population sharing
personal narratives for peer feedback, not for ML dataset construction;
ambiguous redistribution rights. Rejected.

### Generic scraped Kaggle "college essay" dumps
Disadvantages: provenance could not be established for any specific one
surfaced in this research pass. Rejected as a category — exactly the
"available and large, but unverified" case this evaluation exists to
screen out.

## Decision

Use **PERSUADE 2.0** as the primary human-writing corpus for building
general reference distributions (Phase 5/6), and use the **ELLIPSE
Corpus** for the Phase 12 fairness analysis, where its genuine
proficiency labels allow an honest subgroup comparison instead of
inferring language background from text (which Section 16 forbids). Both
were **Provisional** pending a mandatory license-verification step before
any file was downloaded — that step has now run for real (see "Live
Verification & Inspection Update" below), and both passed.

## Why

Between all candidates researched, PERSUADE and ELLIPSE are the only ones
with simultaneously: (1) an immediately usable, non-paywalled, non-
interface-only license, (2) strong, non-scraped provenance, and (3)
sufficient scale/metadata for sentence-level analysis and reference-
distribution construction. Every source with better domain relevance
(the "Essays That Worked" examples, Reddit posts) failed on licensing or
privacy grounds badly enough to be disqualified outright, per this task's
explicit instruction to prioritize provenance/licensing over raw domain
fit or size.

## Evidence

Web research only at this stage (cited in
[dataset-source-comparison.md](../dataset-source-comparison.md)) — no
files have been downloaded, inspected, or committed. This decision is
therefore explicitly **Provisional**, not Accepted: the license-framing
discrepancy found for PERSUADE (CC BY-NC-SA 4.0 on GitHub vs. CC BY 4.0
described on the Learning Agency Lab's own site) has not been resolved
against the authoritative source, which per Kaggle's own dataset
conventions is the license field on the actual Kaggle dataset page at
download time.

## Live Verification & Inspection Update (2026-08-10)

The Evidence section above describes this decision's state when it was
first written (web research only). That research is preserved as-is,
not rewritten, per this project's documentation discipline. This section
records what changed once real credentials became available and
acquisition actually ran.

**License verification (live, not research-based):**
- PERSUADE 2.0 (`nbroad/persaude-corpus-2`): live Kaggle metadata reports
  `CC BY-NC-SA 4.0`. **This resolves the discrepancy** the original
  research found — the GitHub repository's framing was correct; the
  Learning Agency Lab site's "CC BY 4.0" framing was not the operative
  license on the platform this project actually acquires from.
- ELLIPSE Corpus (`mpware/ellipse-corpus`): live Kaggle metadata reports
  `CC BY-NC-SA 4.0`, exactly as expected — no discrepancy.
- One real bug was found and fixed during this process, not a safety-
  logic weakening: `scripts/acquire_dataset.py` originally read
  `dataset.licenseName` (a name assumed from web research on the `kaggle`
  package's API), but the actual installed `kaggle` package exposes
  `dataset.license_name` (snake_case) — confirmed by inspecting the real
  API response object's attributes. Fixed, tests updated to match, full
  suite re-run and passing. The refuse-on-mismatch/refuse-on-not-found
  behavior itself was not changed.

**Both datasets were downloaded and inspected.** Full findings:
[reports/dataset-inspection.md](../../reports/dataset-inspection.md).
Highlights that refine (not reverse) this decision:

- PERSUADE 2.0's actual essay-level file is
  `persuade_2.0_human_scores_demo_id_github.csv` (25,996 essays, 15
  prompts each with full instruction text, paragraph structure preserved
  in 95.8% of essays) — confirms suitability as primary corpus. Real,
  documented data-quality issues found (not disqualifying): the
  corpus-provided `word_count` column is unreliable for ~5% of rows
  (worst case off by 48x), and 4 `essay_id_comp` values collide across
  different essays. Our pipeline already recomputes word counts
  independently (Phase 3), so this doesn't block anything — it's
  recorded so nobody later trusts that column.
- **New finding: PERSUADE itself carries an `ell_status` field**
  (2,244 "Yes" / 22,451 "No" / ~5% missing) — not previously confirmed in
  the research-only pass. This supplies a same-corpus ELL-vs-non-ELL
  comparison, which matters because of the next finding.
- **Refinement to ELLIPSE's role:** ELLIPSE is **100% English Language
  Learners by corpus design** — it cannot, by itself, supply a non-ELL
  comparison group. The original phrasing above ("honest subgroup
  comparison") remains true but needs this precision: the comparison
  will use (a) ELLIPSE's *continuous* proficiency scores to test for a
  within-ELL-population correlation between proficiency and detector
  behavior, and (b) PERSUADE's own `ell_status` field for a same-corpus
  coarse ELL-vs-non-ELL comparison — rather than comparing PERSUADE
  (assumed non-ELL) against ELLIPSE (ELL) directly, which would confound
  ELL status with the fact that they're simply different corpora with
  different prompts and task mixes.
- ELLIPSE has 44 unique prompts, not the ~29 the original web research
  estimated — corrected in `docs/dataset.md` and
  `docs/dataset-source-comparison.md`.
- Both corpora: negligible exact/near-duplication (0 exact dupes in
  either; 4 near-dupe rows in PERSUADE, 0 in ELLIPSE).
- Sensitive metadata inventory completed for both corpora (gender, race/
  ethnicity, economic status, disability status, grade) — recommendation
  is to exclude all of it from the working ML dataset, keeping only
  `ell_status` (PERSUADE) and the proficiency scores (ELLIPSE) in a
  separate evaluation-only table for Phase 12, never joined into
  detector features. Full reasoning in the inspection report.

**Status change justification:** DEC-009 was marked Provisional for two
concrete, named reasons: (1) the PERSUADE license discrepancy was
unresolved against live metadata, and (2) no file had been downloaded or
inspected. Both are now resolved with real evidence, not assumptions —
hence **Accepted**. The domain-mismatch trade-off (below) and the
refined ELLIPSE fairness methodology are carried forward as documented,
accepted characteristics of this decision, not open blockers.

## Trade-offs

Both chosen corpora are a domain mismatch with real admissions essays
(argumentative/proficiency-assessment writing vs. personal narrative) —
accepted deliberately, in exchange for provenance and licensing clarity
that no admissions-essay-specific source offered. This mismatch must be
stated plainly in `docs/dataset.md` and `docs/evaluation.md` once real
numbers exist, not minimized.

## Consequences

Positive:
- Unblocks Phase 5 with two free, well-documented, appropriately-licensed
  corpora.
- ELLIPSE specifically enables an honest Section 16 fairness analysis
  that would otherwise have to be skipped for lack of appropriately-
  labeled data.

Negative:
- Reference distributions built from PERSUADE/ELLIPSE describe
  argumentative/proficiency-assessment student writing, not admissions-
  essay writing specifically — any classification this system eventually
  produces inherits that domain gap, and this must be surfaced to anyone
  reading the results, not buried in a footnote.
- The CC BY-NC-SA 4.0 NonCommercial clause (if it is the authoritative
  license for both corpora) means this project and anything derived from
  these reference distributions must remain non-commercial.

## Revisit When

1. ~~Before any download occurs, programmatically verify the license
   field~~ — **done, 2026-08-10, both passed.** (Kept struck through
   rather than deleted, so the historical criterion and its resolution
   are both visible.)
2. If Phase 12's fairness analysis finds ELLIPSE's proficiency-score
   gradient and/or PERSUADE's `ell_status` field insufficient (e.g. too
   few essays in some proficiency band to compare meaningfully),
   reconsider TOEFL11 despite its LDC licensing overhead.
3. If ICLE's promised September 2026 free-access rollout turns out to
   include bulk export, re-evaluate it as an additional or replacement
   source.
4. If the domain mismatch (Consequences, above) is shown by evaluation to
   produce misleading results specifically *because* of register
   differences (not just weaker overall accuracy), this decision should
   be revisited rather than patched around with post-hoc calibration.
5. If preprocessing later finds the `essay_id_comp` ID collisions (4
   values, PERSUADE) or the `word_count` column unreliability cause any
   downstream problem beyond what's already documented, update
   `reports/dataset-inspection.md` rather than silently working around it
   in code.

## Implementation

`scripts/acquire_dataset.py`, `scripts/dataset_sources.py` (license check
fixed to use `license_name`, matching the real Kaggle API — see Live
Verification Update). Acquired files: `data/raw/persuade_2.0/`,
`data/raw/ellipse_corpus/` (gitignored, not committed — see
`.gitignore` and `docs/dataset.md`).

## Tests / Experiments

`scripts/tests/test_acquire_dataset.py` (5 tests, license-gate logic,
fake API — still passing after the attribute-name fix),
`scripts/tests/test_inspect_corpus.py` (9 tests, inspection utilities
against fixtures). Live verification itself (not a unit test, a real
one-time acquisition run) documented in
[reports/dataset-inspection.md](../../reports/dataset-inspection.md).
