# Dataset Source Comparison

> Status: research complete, no data downloaded yet. This document
> compares candidate **human-writing** sources only — it does not cover
> machine-sample generation (Phase 5, later) or the mixed/AI-polished
> sample construction methodology. Nothing here has been downloaded,
> scraped, or committed; see
> [decisions/DEC-009-human-dataset-source.md](decisions/DEC-009-human-dataset-source.md)
> for the resulting decision and its Provisional status.

## Method

Candidates were found via web research (see Sources at the bottom of each
section) rather than assumed from memory, because licensing/provenance
claims are exactly the kind of thing this project must not fabricate
(Section 12 of the project brief). Where two sources for the same corpus
gave conflicting license framing, that conflict is stated explicitly
rather than silently picking the more convenient one.

Candidates were evaluated against, for each source: provenance, licensing,
domain relevance, approximate size, essay length, topic diversity,
authorship confidence, metadata availability, privacy concerns,
redistribution restrictions, suitability for sentence-level analysis, and
known limitations — per the evaluation criteria requested for this phase.

## At a glance

| Source | Domain relevance | License | Approx. size | Verdict |
|---|---|---|---|---|
| PERSUADE 2.0 | Moderate (argumentative student essays, not personal narrative) | CC BY-NC-SA 4.0 (see note below) | ~25,000 essays | **Leading candidate** |
| ELLIPSE Corpus | Moderate (independent-prompt student essays) | CC BY-NC-SA 4.0 | ~6,500 essays | **Leading candidate — fairness use** |
| ICLE (Int'l Corpus of Learner English) | Low-moderate (academic learner essays) | Restricted, interface-only access | Unclear (not bulk-inspectable) | Rejected (access model) |
| TOEFL11 / ETS Corpus of Non-Native Written English | Low-moderate (TOEFL independent-task essays) | LDC paid license agreement | 12,100 essays | Rejected (cost/paperwork, for now) |
| Official "Essays That Worked" college-published examples | **High** (genuine admissions essays) | Per-essay institutional permission, not a corpus license | Small, scattered across many sites | Rejected (licensing/ethics) |
| Reddit / online essay-feedback forums | High (genuine admissions essays) | Ambiguous; poster retains copyright | Unbounded but uncatalogued | Rejected (privacy/consent) |
| Generic scraped Kaggle "college essay" dumps | Unknown | Unknown/unverifiable | Unknown | Rejected (provenance) |

## PERSUADE 2.0 Corpus

- **Source:** The Learning Agency Lab, developed with Georgia State
  University as part of the "Feedback Prize" initiative.
- **Provenance:** Argumentative/persuasive essays written by real 6th–12th
  grade students in the US, collected for educational-assessment research
  (not scraped from the open web).
- **Licensing:** Stated as **CC BY-NC-SA 4.0** (Attribution-NonCommercial-
  ShareAlike) on the corpus's GitHub repository. Note: The Learning Agency
  Lab's own site describes "Persuade dataset © 2024" as licensed under
  **CC BY 4.0** (no NonCommercial/ShareAlike clause) in at least one place
  we found. **This discrepancy was not resolved by this research pass** —
  **resolved 2026-08-10 by live Kaggle API verification: CC BY-NC-SA
  4.0**, matching the GitHub framing, not the Learning Agency Lab site's.
  See DEC-009's "Live Verification & Inspection Update."
- **Domain relevance:** Moderate. These are argumentative/persuasive
  essays responding to assigned prompts ("Should schools require
  uniforms?"), not personal-narrative admissions essays. Register,
  purpose, and typical rhetorical structure differ from what an
  admissions reader evaluates.
- **Approximate size:** Over 25,000 essays.
- **Essay length:** Typical of in-class timed writing (a few hundred to
  ~1,000 words); not independently re-verified against the raw files in
  this research pass.
- **Topic diversity:** 15 prompts across two task types (independent
  writing, source-based writing) — meaningful diversity within the
  argumentative-essay genre, but all within that one genre.
- **Authorship confidence:** High — collected directly from students as
  part of a research program, not aggregated from anonymous web content.
- **Availability of metadata:** Strong — includes grade level, race/
  ethnicity, economic background, disability status (IEP/504 plan, no
  further detail), and human-annotated argumentative/discourse-element
  labels.
- **Privacy concerns:** Lower than scraped personal-narrative sources —
  essays are argumentative rather than autobiographical, reducing (but
  not eliminating) the amount of personal/identifying detail in the text
  itself. Demographic metadata is presumably anonymized/aggregated by the
  original research program; this has not been independently verified.
- **Redistribution restrictions:** NonCommercial and ShareAlike clauses
  (if the GitHub license framing is authoritative) mean any derivative
  dataset we build from it must also be non-commercial and
  similarly-licensed. This project is non-commercial, so that's
  compatible, but it constrains any future commercial use of this
  project or its derived reference distributions.
- **Suitability for sentence-level analysis:** Good — plain text essays
  with normal sentence/paragraph structure, no special markup to strip.
- **Known limitations:** Domain mismatch (persuasive vs. narrative);
  license framing discrepancy noted above must be resolved before
  download; grades 6–12 population skews younger than typical college
  applicants (rising seniors), so some stylistic maturity differences
  from real admissions essays should be expected and documented, not
  papered over.

Sources: [GitHub — scrosseye/persuade_corpus_2.0](https://github.com/scrosseye/persuade_corpus_2.0), [Kaggle — persuade corpus 2.0](https://www.kaggle.com/datasets/nbroad/persaude-corpus-2), [The Learning Agency Lab — PERSUADE Dataset](https://the-learning-agency-lab.com/learning-exchange/persuade-dataset/), [ScienceDirect — PERSUADE 2.0 paper](https://www.sciencedirect.com/science/article/pii/S1075293524000588)

## ELLIPSE Corpus

- **Source:** Vanderbilt University researchers (Crossley et al.) /
  The Learning Agency Lab, released for the "Feedback Prize — English
  Language Learning" Kaggle competition.
- **Provenance:** Essays written by English Language Learners (ELLs)
  during state-wide standardized annual testing in the US — collected for
  language-proficiency-assessment research, not scraped.
- **Licensing:** **CC BY-NC-SA 4.0**, consistently stated across the
  GitHub repository and research literature found — no discrepancy
  observed here (unlike PERSUADE above).
- **Domain relevance:** Moderate. Independent-prompt essays not requiring
  background knowledge — closer in spirit to a "write about your
  experience/opinion" prompt than PERSUADE's argumentative structure, but
  still not admissions-essay narrative writing specifically.
- **Approximate size:** ~6,500 essays in the curated/reliable release
  (drawn from a larger ~9,000-essay raw pool, with some excluded for
  scoring-reliability reasons).
- **Essay length:** Not independently re-verified in this research pass.
- **Topic diversity:** ~29 independent prompts per secondary sources found
  during this research pass. **Correction (2026-08-10, after actual
  acquisition and file inspection): the real file contains 44 unique
  prompts** — see
  [reports/dataset-inspection.md](../reports/dataset-inspection.md).
  Left here uncorrected-in-place deliberately, alongside this note, so
  the research-vs-inspection discrepancy itself stays visible.
- **Authorship confidence:** High — collected during actual standardized
  testing administration, not self-reported or scraped.
- **Availability of metadata:** Strong, and uniquely valuable for this
  project: **genuine English-proficiency labels** (an overall proficiency
  score plus six analytic sub-scores: cohesion, syntax, vocabulary,
  phraseology, grammar, conventions), rated by two trained human raters —
  plus economic status, gender, grade level (8–12), and race/ethnicity.
- **Privacy concerns:** Similar profile to PERSUADE — collected through a
  formal research/testing pipeline rather than scraped; independent
  verification of anonymization was not performed in this research pass.
- **Redistribution restrictions:** Same NonCommercial/ShareAlike
  constraints as PERSUADE.
- **Suitability for sentence-level analysis:** Good, same profile as
  PERSUADE (plain text, standard structure).
- **Known limitations:** Domain mismatch (independent-prompt/proficiency-
  assessment essays vs. admissions narrative writing); smaller than
  PERSUADE; grades 8–12 (closer to college-applicant age than PERSUADE's
  6–12 floor, but still not college-applicant-specific).

**Why this matters beyond "another student-essay corpus":** Section 16 of
the project brief requires investigating fairness for second-language
English writers, and explicitly forbids inferring language background
from the writing itself. ELLIPSE is, as far as this research found, the
only candidate here with **genuine, appropriately-collected** ELL
proficiency labels — meaning it can support that required fairness
analysis honestly, rather than the analysis being blocked entirely for
lack of appropriately-labeled data (which is the default, and the honest
fallback stated in `docs/fairness.md` if this hadn't been found).

Sources: [ResearchGate — ELLIPSE Corpus](https://www.researchgate.net/publication/378094468_The_English_Language_Learner_Insight_Proficiency_and_Skills_Evaluation_ELLIPSE_Corpus), [Kaggle — ELLIPSE Corpus](https://www.kaggle.com/datasets/mpware/ellipse-corpus), [GitHub — scrosseye/ELLIPSE-Corpus](https://github.com/scrosseye/ELLIPSE-Corpus), [LEAR Lab — Datasets](https://learlab.org/data/)

## International Corpus of Learner English (ICLE)

- **Source:** Centre for English Corpus Linguistics, UCLouvain.
- **Provenance:** Academic essays by advanced learners of English across
  many L1 backgrounds, collected by an academic consortium over decades —
  high scholarly provenance.
- **Licensing / access:** Historically restricted to a paid, non-profit-
  educational license granting **web-interface access**, not bulk file
  download — the trial version explicitly has "text download
  functionality deactivated." Free access to all users is stated to begin
  September 15, 2026, but even then the description found is of interface
  access, not confirmed bulk export.
- **Domain relevance:** Low-moderate — academic essays, not personal
  narrative.
- **Approximate size:** Not independently determined in this pass (access
  model prevented direct inspection).
- **Suitability for sentence-level analysis:** Poor fit for this
  project's needs as currently accessible — a reproducible local
  acquisition/preprocessing pipeline (Section 12's requirement) needs
  bulk, scriptable access, not an interactive web interface.
- **Known limitations / why rejected (for now):** Access model
  incompatible with a reproducible, scriptable pipeline. Worth
  re-examining after September 2026 if free access turns out to include
  bulk export — noted as a future revisit, not a permanent rejection.

Sources: [UCLouvain — ICLE](https://corpora.uclouvain.be/cecl/icle/home), [UCLouvain — ICLE trial](https://corpora.uclouvain.be/cecl/icle/trial/)

## TOEFL11 / ETS Corpus of Non-Native Written English

- **Source:** Educational Testing Service (ETS), distributed via the
  Linguistic Data Consortium (LDC2014T06).
- **Provenance:** 12,100 real TOEFL independent-task essays (2006–2007),
  1,100 per each of 11 native-language backgrounds, with score-level
  (low/medium/high) labels — very strong provenance and exactly the kind
  of appropriately-labeled L1-background data that would strengthen a
  fairness analysis.
- **Licensing / access:** Distributed through LDC, which requires an LDC
  user/membership license agreement (and historically a fee) rather than
  a simple open download — a real acquisition cost in time/paperwork/money
  that has not been initiated.
- **Domain relevance:** Low-moderate — TOEFL independent-writing-task
  essays (opinion essays on assigned prompts), not admissions narratives.
- **Known limitations / why rejected (for now):** The access process
  (LDC license agreement) is real friction that this research pass
  explicitly should not route around ("do not download or commit a
  dataset whose licensing/provenance has not been established" — here
  it's established, just gated behind a process we haven't started).
  Given PERSUADE + ELLIPSE already unblock Phases 5–6 under an
  immediately-available license, TOEFL11 is deferred rather than pursued
  now. Worth revisiting specifically if EXP-006 (fairness) later needs
  L1-background labels beyond what ELLIPSE's ELL-proficiency labels
  provide.

Sources: [LDC catalog — LDC2014T06](https://catalog.ldc.upenn.edu/LDC2014T06), [ERIC — TOEFL11: A Corpus of Non-Native English](https://files.eric.ed.gov/fulltext/EJ1109982.pdf)

## Official college-published "Essays That Worked" examples

- **Source:** Individual university admissions offices (e.g. Johns
  Hopkins, Hamilton College) and third-party sites (e.g.
  essaysthatworked.com, College Essay Guy) that publish real accepted
  applicants' essays.
- **Provenance:** These are, as far as domain match goes, **the single
  best match** available — genuine college admissions essays, exactly the
  target text type.
- **Licensing:** This is where it falls apart for our purposes. Hamilton
  College's page states essays are "reprinted with the permission of
  students" — i.e. permission was granted to that specific publisher for
  that specific use (recruiting/inspiring future applicants), not a
  license for a third party to bulk-collect and redistribute the text as
  an ML dataset. Each site has its own Terms and Conditions governing use
  of the *site*, not a corpus license for the essay text.
- **Redistribution restrictions:** Scraping these pages and using the
  essays as training/reference data would exceed the scope of consent the
  original students gave, and likely violate each site's Terms of Use.
- **Privacy concerns:** These are personal, identifying narratives
  (often including the student's name, hometown, and other admissions-
  specific context) written by minors or very recent minors at the time
  of writing.
- **Known limitations / why rejected:** Best domain match, worst
  licensing/consent fit. This is exactly the case the brief's Section 12
  guidance ("prefer datasets with clear provenance and licensing") is
  warning against overriding for domain-fit alone. Rejected.

Sources: [Hamilton College — Essays that Worked](https://www.hamilton.edu/admission/apply/college-essays-that-worked), [Johns Hopkins — Essays That Worked](https://apply.jhu.edu/college-planning-guide/essays-that-worked/), [Essays That Worked](https://essaysthatworked.com/)

## Reddit / online essay-feedback forums (e.g. r/ApplyingToCollege)

- **Provenance / domain relevance:** High — real applicants voluntarily
  post real drafts of their actual admissions essays for peer feedback.
- **Privacy concerns:** Significant. Posters are typically minors or very
  recent minors, sharing personal, sometimes sensitive life narratives,
  under an expectation of getting essay feedback from strangers — not an
  expectation of becoming part of an ML training/reference dataset.
- **Redistribution restrictions:** Reddit's terms grant Reddit a license
  to the content; the poster retains copyright. Using the essays outside
  the platform for dataset construction is a separate question from
  whether the post itself is "public," and raises consent concerns this
  project should not resolve by simply asserting API/ToS compliance is
  sufscient.
- **Known limitations / why rejected:** Privacy/consent risk to a
  vulnerable population (largely minors) outweighs the domain-relevance
  advantage. Rejected.

## Generic scraped Kaggle "college essay" / "student essays" dumps

- **Provenance:** Frequently unclear — many such datasets are re-uploads
  of scraped web content without a documented chain back to an original,
  consenting source.
- **Known limitations / why rejected:** This is precisely the "do not
  select a source merely because it is available/large, without
  established provenance/licensing" case this research phase exists to
  guard against. A specific such dataset could in principle be evaluated
  if a concrete provenance chain were found for it, but none of the ones
  surfaced in this research pass (e.g. generic "essays.csv"-style
  uploads) documented one. Not pursued further.

## Related resource noted for later (not a human-writing source itself)

The Kaggle competition **"LLM - Detect AI Generated Text"** pairs
PERSUADE-derived human essays with essays generated by multiple LLMs
(including fine-tuned models and general-purpose ones) for the same
prompts. This is not a separate *human* source (its human essays are
PERSUADE's), but it's a relevant prior-art reference for Phase 5's
machine-sample-generation and mixed-sample-construction methodology, and
will be considered then — noted here so it isn't rediscovered from
scratch later.

Sources: [Kaggle — LLM - Detect AI Generated Text](https://www.kaggle.com/competitions/llm-detect-ai-generated-text)
