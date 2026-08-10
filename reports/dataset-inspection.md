# Dataset Inspection Report

> Produced from live-verified, actually-downloaded corpus files. Every
> number below comes from running pandas against the real files in
> `data/raw/` (not committed — gitignored), using
> `scripts/inspect_corpus.py` (tested against fixtures,
> `scripts/tests/test_inspect_corpus.py`) plus direct inspection. Where a
> claim in earlier docs (`dataset-source-comparison.md`, DEC-009) turns
> out to differ from what the real files show, that's called out
> explicitly as a correction, not silently reconciled.
>
> Acquisition date: 2026-08-10. No AI samples have been generated. No
> train/validation/test split has been created. This is inspection only.

---

## PERSUADE 2.0

### Dataset identity

- **Name:** PERSUADE 2.0 (as downloaded — see file-naming caveat below)
- **Kaggle reference:** `nbroad/persaude-corpus-2`
- **Verified license (live, this session):** `CC BY-NC-SA 4.0` — matches
  the GitHub repository's framing from DEC-009's research, **resolving**
  the discrepancy noted there (the Learning Agency Lab's own site had
  described it as CC BY 4.0; Kaggle's authoritative metadata says
  otherwise). See `data/raw/persuade_2.0/ACQUISITION_MANIFEST.json`.
- **Acquisition date:** 2026-08-10, via `scripts/acquire_dataset.py`.
- **Source/provenance:** Community-uploaded Kaggle mirror (owner
  `nbroad`), not an official Learning Agency Lab Kaggle listing — as
  already flagged as an open item in `scripts/dataset_sources.py`. The
  content matches the expected PERSUADE 2.0 essay set (see Text section
  below): 25,996 essays, matching the ~25,000 figure from prior research.

### Files

| File | Format | Size |
|---|---|---|
| `persuade_corpus_1.0.csv` | CSV | 852 MB |
| `persuade_2.0_human_scores_demo_id_github.csv` | CSV | ~30 MB |
| `sources.csv` | CSV | small |

**Important correction:** the largest file is literally named
`persuade_corpus_1.0.csv` — a **different, earlier-format** file than
what our pipeline needs. It's the discourse-element-annotated release
(one row per paragraph-level "discourse element" within an essay, e.g.
Lead/Position/Claim spans — 285,383 rows covering the same 25,996 essays
via `full_text` repeated per row), not a one-row-per-essay file. **The
file our pipeline actually uses is
`persuade_2.0_human_scores_demo_id_github.csv`** (one row per essay, rich
metadata — see below). `persuade_corpus_1.0.csv` is not needed for our
purposes and is the reason the download is 852MB instead of the ~30MB we
actually use.

### Schema (`persuade_2.0_human_scores_demo_id_github.csv`)

| Column | Type | Missing % | Notes |
|---|---|---|---|
| `essay_id_comp` | string | 0.0% | See Duplicates — 4 non-unique values found |
| `full_text` | string | 0.0% | The essay text |
| `holistic_essay_score` | int | 0.0% | 1–6 scale |
| `word_count` | int | 0.0% | **Unreliable — see Text section** |
| `prompt_name` | string | 0.0% | 15 unique values |
| `task` | string | 0.0% | `Independent` (13,121) / `Text dependent` (12,875) — corpus's own terms, not "source-based" as earlier research summaries phrased it |
| `assignment` | string | 0.0% | Full prompt instruction text — one unique value per `prompt_name`, 1:1 |
| `source_text` | string | 50.5% | Present only for `Text dependent` essays, as expected |
| `gender` | string | 0.0% | Sensitive — see Metadata |
| `grade_level` | float | 4.5% | Sensitive-adjacent |
| `ell_status` | string | 4.7% (+92 rows are a literal `' '` blank string, not proper `NaN`) | **Yes/No/blank/NaN** — see Metadata |
| `race_ethnicity` | string | 0.0% | Sensitive — see Metadata |
| `economically_disadvantaged` | string | 20.1% | Sensitive — see Metadata |
| `student_disability_status` | string | 19.9% | Sensitive — see Metadata |

### Text

- **Usable essays:** 25,996 rows; 25,992 unique `essay_id_comp` values
  (4 IDs are non-unique — see Duplicates).
- **Word count — do not trust the corpus's `word_count` column.**
  Comparing it against our own whitespace-split recount
  (`scripts/inspect_corpus.recompute_word_counts`):
  - 31.0% of rows match closely (≤2 words difference — plausible
    tokenizer differences)
  - 63.6% differ by 3–20 words (still minor)
  - **5.4% (1,407 rows) differ by more than 20 words**, and 228 of those
    differ by more than 100
  - **Worst case:** one essay's `word_count` column says 14,818; the
    actual text (18,125 characters) contains 305 words by direct count —
    a **48x discrepancy**, almost certainly a data error in the source
    file, not a real 14,818-word student essay.
  - **Decision this implies:** our pipeline must compute word counts
    (and any other text statistics) directly from `full_text` — which
    Phase 3's `feature_extractor.py` already does independently — never
    from this column. This is a genuine corpus data-quality issue to
    document, not a design flaw on our side.
- **Recomputed word-count distribution (our own count, trustworthy):**
  min 143, median 373, mean 411, max 1,656.
- **Length outliers (>3,000 words by the *provided*, unreliable column):**
  21 essays, almost all `Text dependent` — consistent with the theory
  that some of these are data artifacts rather than genuinely long
  essays (not exhaustively verified for all 21, only the worst case was
  manually checked).

### Prompts

- **15 unique prompts** (`prompt_name`), each with a **corresponding full
  instruction text** in `assignment` — a clean 1:1 mapping (verified: 15
  unique `prompt_name` values, 15 unique `assignment` values, one each).
  This directly supports the prompt-extraction step
  `generation-methodology.md` Section 2 describes.
- Prompt sizes range from 1,168 to 2,167 essays each.
- Example prompt names found: "Car-free cities," "Phones and driving,"
  "Distance learning," "Does the electoral college work?," "Community
  service," and 10 others — full list in the corpus, not reproduced here
  in full to avoid this report going stale if re-inspected.
- `sources.csv` provides source article text/metadata for the
  `Text dependent` prompts, including a `gpt4_summary` column —
  **this column contains AI-generated text** (GPT-4-authored summaries of
  source articles). This must **never** be treated as human-authored
  content if `sources.csv` is used for anything beyond looking up source
  material — a real contamination risk to guard against explicitly in
  any future preprocessing code.

### Structure

- **Paragraph boundaries are preserved** via blank-line convention
  (`\n\n`) in **24,910 / 25,996 essays (95.8%)**. The remaining 1,086
  essays (4.2%) are single blocks with no blank-line breaks — genuinely
  single-paragraph submissions, not a parsing failure (spot-checked).
  This **resolves the open paragraph-boundary question from Phase 5B**:
  paragraph-level mixed-sample transformations are feasible for the
  large majority of essays, using `\n\n` as the boundary marker, with the
  ~4.2% single-block essays excluded from that category (not forced into
  an invented paragraph split).
- Paragraph count distribution (via `\n\n`-splitting): median 5,
  mean 5.4, max 69 (an extreme case, not independently verified further).

### Duplicates

- **Exact duplicate `full_text`:** 0.
- **Near-duplicates** (heuristic: normalized prefix/suffix/length
  signature, `scripts/inspect_corpus.near_duplicate_groups`): 2 groups,
  4 rows total — negligible.
- **Duplicate `essay_id_comp` values:** 4 IDs each appear on 2 different
  rows with **different essay text** (e.g. `1.51E+11` appears for both a
  190-word "A Cowboy Who Rode the Waves" essay and a 711-word "Exploring
  Venus" essay). This is a source-corpus ID-collision bug, not duplicate
  content — confirmed the IDs are genuinely stored as literal strings
  like `"1.51E+11"` in the CSV (not a pandas display/dtype artifact).
  **Implication:** `essay_id_comp` cannot be trusted alone as a unique
  key for the 8 affected rows; our pipeline should generate its own
  unique row identifier rather than relying solely on this column.

### Metadata

1. **Needed for the detector/data pipeline:** `essay_id_comp` (with the
   caveat above), `full_text`, `prompt_name`, `assignment` (prompt text),
   `task`, `holistic_essay_score` (potentially useful as a quality
   control signal, not a detector feature).
2. **Needed only for evaluation/provenance (never fed to the detector):**
   `ell_status` — directly relevant to the Section 16 fairness analysis
   this project is required to do (**new finding: PERSUADE alone has a
   usable, if partial, ELL/non-ELL label** — 22,451 "No," 2,244 "Yes,"
   with 1,209 NaN + 92 blank-string rows needing explicit missing-data
   handling).
3. **Unnecessary sensitive metadata — recommend NOT carrying into the
   working ML dataset at all:** `gender`, `race_ethnicity`,
   `economically_disadvantaged`, `student_disability_status`,
   `grade_level`. None of these map to a fairness question this project
   is actually scoped to investigate (Section 16 is specifically about
   second-language English writers); retaining them would be collecting
   sensitive demographic data with no corresponding analysis to justify
   it. Recommendation: drop these columns entirely during preprocessing,
   keep only `ell_status` (for the one fairness analysis this project
   commits to) alongside the text/prompt columns.

### Limitations

- Kaggle mirror, not an official Learning Agency Lab listing — content
  matches expectations on inspection, but provenance is one step removed
  from the original publisher.
- `persuade_corpus_1.0.csv` (852MB) is bundled but unused — expect this
  disk footprint on re-acquisition; not a bug.
- `word_count` column is unreliable for ~5% of rows, badly wrong for a
  smaller number — always recompute from `full_text`.
- 4 duplicate `essay_id_comp` values (8 rows) — needs its own unique key.
- `ell_status` has a mix of `NaN` and literal blank-string `' '` for
  missing values — must normalize both to a single missing marker during
  preprocessing.
- Domain remains argumentative/persuasive student writing, not
  personal-narrative admissions essays (unchanged conclusion from
  DEC-009, now on a firmer evidentiary footing since the actual prompts
  and essays have been read, not just described secondhand).

---

## ELLIPSE Corpus

### Dataset identity

- **Name:** ELLIPSE Corpus
- **Kaggle reference:** `mpware/ellipse-corpus`
- **Verified license (live, this session):** `CC BY-NC-SA 4.0` — matches
  DEC-009's expectation exactly, no discrepancy.
- **Acquisition date:** 2026-08-10.
- **Source/provenance:** matches expectations from prior research —
  6,482 essays (research had estimated ~6,500 — accurate).

### Files

| File | Format | Size |
|---|---|---|
| `ELLIPSE_Final_github.csv` | CSV | ~15 MB total for the dataset |
| `ELL_Rubrics.docx` | Word document | small — scoring rubric documentation, not essay data; not parsed for this report |

### Schema (`ELLIPSE_Final_github.csv`)

25 columns, **zero missing values in any column** (only 1 `NaN` in `SES`
out of 6,482 rows) — a notably cleaner file than PERSUADE's. Key columns:
`text_id_kaggle`, `full_text`, `gender`, `grade`, `race_ethnicity`,
`num_words`/`num_words2`/`num_words3` (three different word-count
definitions — see Text), `num_sent`, `num_para`, `MTLD`, `TTR`, `task`,
`SES`, `prompt`, and seven proficiency scores: `Overall`, `Cohesion`,
`Syntax`, `Vocabulary`, `Phraseology`, `Grammar`, `Conventions`.

### Text

- **Usable essays:** 6,482, all unique `text_id_kaggle`, 0 exact
  duplicate `full_text`.
- **Word count — three columns provided, they disagree with each other.**
  `num_words2` and `num_words3` match our own whitespace-split recount
  almost exactly (median 398 vs. our recomputed median 398); the plain
  `num_words` column uses a different counting convention (mean absolute
  difference ~50 words vs. our recount). **Use `num_words3` (or recompute
  directly) — not the bare `num_words` column** — if corpus-provided
  counts are used at all; our pipeline recomputes independently anyway.
- **Length range:** min 14 words, median 398, mean 428, max 1,274 (using
  our own recount / `num_words3`) — no equivalent of PERSUADE's wild
  outlier was found here.

### Prompts

- **44 unique prompts**, not the ~29 that prior web research (cited in
  `dataset-source-comparison.md`) estimated. **This is a correction to
  that earlier document, made now that the real file can be inspected
  directly** — updated in `docs/dataset.md`.
- **No full instruction text is provided** — only short prompt titles
  (e.g. "Distance learning," "Cell phones at school"), unlike PERSUADE's
  `assignment` field. This is weaker for the prompt-matching
  full-generation methodology than PERSUADE: generation prompts built
  from ELLIPSE's `prompt` field alone will be less precisely specified
  than PERSUADE's.
- Single task type: 100% `Independent` (no source-based/text-dependent
  essays in this corpus).
- Prompt sizes range widely: 489 essays for "Distance learning" down to
  38 for "Summer projects."

### Structure

- **Paragraph boundaries preserved** in 6,144 / 6,482 essays (94.8%),
  consistent with PERSUADE's finding. Line-ending convention is
  **inconsistent within the file itself** — some rows use `\n\n`, others
  `\r\n\r\n` (confirmed by direct inspection of the first two rows). Our
  existing `text_normalizer.py` (Phase 2) already normalizes `\r\n` → `\n`
  before segmentation, so this is already handled correctly by existing
  code, not a new problem to solve.
- A `num_para` column independently corroborates the paragraph-marker
  finding (median 5 paragraphs, consistent with what blank-line-splitting
  finds).
- Evidence of deliberate PII redaction by the corpus creators: e.g. one
  sample essay addresses "Dear, TEACHER_NAME" — a redaction placeholder,
  not a real name. A positive finding for privacy.

### Duplicates

- Exact duplicates: 0.
- Near-duplicates (same heuristic as PERSUADE): 0 groups.

### Metadata

1. **Needed for the detector/data pipeline:** `text_id_kaggle`,
   `full_text`, `prompt`, `task`.
2. **Needed only for evaluation/provenance:** the seven proficiency
   scores (`Overall` + six analytic sub-scores) — this is the entire
   reason DEC-009 selected this corpus, and it delivers on that: a
   **continuous** proficiency measure, not just a binary ELL flag. This
   enables a stronger fairness test than a simple two-group comparison —
   see Dataset Selection Decision below.
3. **Unnecessary sensitive metadata — recommend NOT carrying into the
   working ML dataset:** `gender`, `race_ethnicity`, `grade`, `SES`. Same
   reasoning as PERSUADE: out of this project's stated fairness scope
   (Section 16 is about second-language writers specifically).
   **Real representativeness caveat if anyone later wanted to use these:**
   `race_ethnicity` is heavily skewed (Hispanic/Latino: 4,635 / 71.5% of
   the corpus; American Indian/Alaskan Native: only 23 essays) — nowhere
   near enough sample size in most categories for a reliable subgroup
   comparison, reinforcing the decision not to use this axis.

### Limitations

- No full prompt/instruction text (only short titles) — weaker
  generation-prompt fidelity than PERSUADE.
- Every essay in this corpus is from an English Language Learner by
  corpus design — there is no non-ELL comparison group *within* ELLIPSE
  itself (see Dataset Selection Decision).
- Same domain mismatch as PERSUADE: independent-prompt student essays,
  not admissions narratives.

---

## Sensitive metadata — cross-corpus summary

Per the instruction not to feed demographic metadata into the detector:
**the recommended working (processed) dataset carries forward only**
text, prompt/task identifiers, and — solely for the Phase 12 fairness
analysis, kept in a separate evaluation-only table never joined into the
detector's feature vector — PERSUADE's `ell_status` and ELLIPSE's
proficiency scores. `gender`, `race_ethnicity`, `economically_disadvantaged`
/`SES`, `student_disability_status`, and `grade`/`grade_level` are
recommended for exclusion from the working dataset entirely, not merely
"unused" — collecting them would carry privacy/sensitivity cost with no
analysis in this project's actual scope to justify keeping them.

## Dataset Selection Decision (evidence-based, post-inspection)

**PERSUADE 2.0 → primary human-writing corpus.** Confirmed suitable:
clean prompt/assignment mapping, large size (25,996 usable essays),
two task types, paragraph structure preserved for generation-pairing
purposes, negligible duplication. Caveats (word-count column
unreliability, 4 ID collisions, blank-vs-NaN inconsistency in
`ell_status`) are data-cleaning items, not disqualifying issues.

**ELLIPSE → fairness/robustness evaluation corpus — refined role.**
DEC-009 originally framed this as enabling an ELL-vs-non-ELL comparison.
Inspection reveals ELLIPSE is **100% ELL writers** — it cannot supply the
non-ELL side of that comparison by itself. The refined, evidence-based
plan:
- **Primary fairness test:** use ELLIPSE's *continuous* `Overall`
  proficiency score to test whether the detector's false-positive rate
  (or evidence strength) correlates with proficiency **within** the ELL
  population — arguably a more direct test of "does this penalize weaker
  English proficiency" than a coarse binary split.
- **Secondary, coarser test:** PERSUADE's own `ell_status` field (2,244
  "Yes" / 22,451 "No", once blank/NaN rows are handled) supplies an
  ELL-vs-non-ELL comparison *within one corpus*, avoiding a cross-corpus
  confound (PERSUADE-ELL vs. ELLIPSE-ELL essays differ by more than ELL
  status alone — different prompts, different task mix).
- This is a genuine refinement of the Phase 12 plan, not a reversal —
  recorded as an update to DEC-009, not a new decision.

**Both remain a domain mismatch with real admissions essays** — stated
again here, on firmer footing than the pre-inspection research alone
provided, and not minimized.

## Preprocessing scope for this report

No processed/merged dataset, no train/validation/test split, and no
deduplication that modifies the corpus has been performed. This report
describes what exists in the raw acquired files only.
