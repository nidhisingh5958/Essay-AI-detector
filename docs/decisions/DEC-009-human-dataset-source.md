# DEC-009 — Human Dataset Source

## Status
Provisional

## Date
2026-08-10

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
general reference distributions (Phase 5/6), and reserve the **ELLIPSE
Corpus** specifically for the Phase 12 fairness analysis, where its
genuine ELL-proficiency labels allow an honest subgroup comparison instead
of inferring language background from text (which Section 16 forbids).
Both remain **Provisional** pending a mandatory license-verification step
before any file is downloaded or committed (see Evidence and Revisit
When).

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

1. **Before any download occurs** (first step of the Phase 5 acquisition
   script, not a separate manual step to skip under time pressure):
   programmatically read the license field from the actual Kaggle dataset
   metadata for both corpora and assert it matches what's documented
   here. If it doesn't, stop and update this record before proceeding —
   do not silently proceed on a mismatched license.
2. If Phase 12's fairness analysis finds ELLIPSE's ELL-proficiency labels
   insufficient (e.g. too few essays in some proficiency band to compare
   meaningfully), reconsider TOEFL11 despite its LDC licensing overhead.
3. If ICLE's promised September 2026 free-access rollout turns out to
   include bulk export, re-evaluate it as an additional or replacement
   source.
4. If the domain mismatch (Consequences, above) is shown by evaluation to
   produce misleading results specifically *because* of register
   differences (not just weaker overall accuracy), this decision should
   be revisited rather than patched around with post-hoc calibration.

## Implementation

Not yet — this decision precedes the acquisition script
(`scripts/`, to be added next). No files have been downloaded or
committed.

## Tests / Experiments

None yet. The license-verification step above will be the first
automated check in the (not-yet-written) acquisition script, and should
have its own test asserting the script refuses to proceed on a license
mismatch.
