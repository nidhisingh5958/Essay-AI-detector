# Product Audit & Implementation Plan — Final Research-to-Product Handoff

**Status: AUDIT / SYNTHESIS / PLAN ONLY, 2026-08-15.** No detector code
modified, no retraining, no data regeneration, no dataset/test-set
modification, no frontend/API implementation in this document's
production. This synthesizes six completed experiments (EXP-003A,
EXP-003B, EXP-003B-R1, EXP-003C, GEN-001, FAIR-001) plus the existing
codebase into a product definition and phased implementation plan for
the next, separately-authorized phase.

Source experiments/reports (not rewritten, only cited):
[EXP-003A](../reports/EXP-003A.md), [EXP-003B](../reports/EXP-003B.md),
[EXP-003B-R1](../reports/EXP-003B-R1.md), [EXP-003C](../reports/EXP-003C.md),
[GEN-001](../reports/GEN-001.md), [FAIR-001](../reports/FAIR-001.md).

---

## 1. Final evidence summary

| Question | Evidence | Verdict |
|---|---|---|
| Can whole-essay AI generation (`full_ai`) be detected? | EXP-003A: near-perfect separation on Qwen2.5-1.5B-Instruct (test 45/46–46/46 depending on threshold). GEN-001: the same frozen detector transfers essentially perfectly to Phi-3.5-mini-instruct (97.8%/100%, identical to Qwen's own result; zero score-distribution overlap between human and either generator's `full_ai`). | **Yes, with real cross-generator evidence** — tested against 2 architecturally distinct generators, not 1. |
| What drives that detection? | EXP-003A: stylometric-only ties combined exactly. EXP-003C: stylometric-only ties combined exactly on validation. GEN-001: stylometric-only transfers as well as combined; LM-only is the only group that degrades under generator shift. | **Stylometric features (lexical diversity, repetition, sentence rhythm, word length, punctuation, dependency depth) — not the LM instrument.** |
| Can lightly AI-assisted writing (`ai_assisted`) be detected at the essay level? | EXP-003B: essay-level near chance (frozen-threshold test result at/below majority baseline). EXP-003C: **complete collapse** — 0/16 correct, precision/recall/F1 all exactly 0.0, 15/16 misclassified as `human`. | **No — essay-level `ai_assisted` classification is not usable.** |
| Is there real signal for *where* in an essay AI touched something? | EXP-003B: 86.7% sentence-level recall at 17.6% precision; 60% top-1-per-essay accuracy (test) vs. ~8% chance. EXP-003B-R1: signal survives removing length/count features (46.7% non-length top-1 vs. 40% length-only, both far above chance) — not just a length artifact. | **Yes — real, above-chance, but low-precision signal.** Usable as a candidate-flagging tool, not as proof. |
| Does the LM (perplexity/predictability) instrument add value? | EXP-003A: zero incremental value. EXP-003B-R1: genuine LM-predictability features are the *weakest* of 5 groups tested (13.3%). EXP-003C: LM-only strictly weaker than stylometric/combined, which are identical to each other. GEN-001: LM-only is the *only* group that degrades under generator transfer (100%→56.5% recall). | **No demonstrated incremental value, across four independent experimental designs.** DEC-004 remains open, not Rejected, but the pattern is now consistent. |
| Does the detector treat English-proficiency subgroups differently? | FAIR-001: human FP rate 0.0% (`ell_status=Yes`, n=10) vs. 0.76% (`No`, n=132); AI FN rate 0.0% vs. 0.0%; overlapping score distributions. | **No material disparity detected — but the n=10 sample can only rule out a large disparity (~>25–28 points), not a smaller one.** Not a fairness certification. |

---

## 2. What the detector can honestly claim

- It statistically distinguishes **whole-essay human writing from whole-essay AI generation**, on this benchmark, with high accuracy, using measurable stylometric features (vocabulary diversity, repetition rate, sentence-length rhythm, average word length, punctuation density, syntactic dependency depth).
- This separation has been shown to hold **across two architecturally distinct AI writing models** (Qwen2.5-1.5B-Instruct and Phi-3.5-mini-instruct) — real, if bounded, evidence against "this only works because it memorized one model's fingerprint."
- It can surface **sentence-level candidates** worth a closer look inside an essay that shows AI-assisted characteristics, with real (above-chance) but imprecise signal.
- Within the evaluated data, it does **not** show a detected difference in error rates for essays written by students in the available English-proficiency subgroups — an absence-of-evidence finding, explicitly bounded by sample size.
- Every number the system would show a user is traceable to a computed, inspectable feature — never an opaque model verdict (DEC-004, DEC-017).

## 3. What it cannot claim

- **Cannot** claim to reliably detect **AI-assisted (lightly edited) writing** at the essay level — EXP-003B/EXP-003C show this fails completely as a classifier.
- **Cannot** claim to identify **a specific sentence as AI-written** with certainty — 17.6% precision means roughly 5 in 6 flagged sentences (at the recall-maximizing threshold) are not the AI-touched one.
- **Cannot** claim **universal AI detection** — tested against exactly two generation models, one dataset (PERSUADE-derived), one generation methodology per category.
- **Cannot** claim the system is **"fair"** — only that no disparity was detected in a small, underpowered sample on one proficiency variable.
- **Cannot** claim the **perplexity/predictability (LM) signal** is a meaningful part of why the system works — evidence says it isn't, and under generator shift it actively degrades.
- **Cannot** claim any figure resembling **"100% accurate,"** "detects all AI writing," "proves AI wrote this," or "identifies AI sentences with certainty."

## 4. Final product claim (proposed)

> **"This tool analyzes an essay's measurable writing patterns — vocabulary diversity, sentence rhythm, repetition, and related statistical features — and reports whether those patterns are more consistent with the fully AI-generated essays or the human-written essays in its reference data, along with which passages most influenced that result. It does not detect editing assistance reliably, does not identify individual AI-written sentences with certainty, and its conclusions are scoped to the writing styles it has been tested against."**

**Justification, feature by feature of the claim**:
- "measurable writing patterns... statistical features" — grounded in DEC-004/DEC-017: every claim traces to a computed feature, never an LLM verdict.
- "more consistent with... in its reference data" — deliberately relative/comparative language, not an absolute "is/is not AI" claim; matches what a logistic-regression probability actually represents.
- "along with which passages most influenced that result" — grounded in the real (if imprecise) sentence-localization signal (EXP-003B/B-R1), framed as influence/evidence, not proof.
- "does not detect editing assistance reliably" — required by EXP-003B/EXP-003C's collapse; omitting this would be dishonest by omission.
- "does not identify individual AI-written sentences with certainty" — required by the 17.6% precision figure.
- "scoped to the writing styles it has been tested against" — required by GEN-001's own scope discipline (2 generators, not "all AI") and by FAIR-001's small-sample caveat.

This wording is a proposal for review, not a final production string — see §10 for exact UI copy.

## 5. Recommended production classification strategy

### Essay level: **three-state output**, not a binary or three-class label

| State | Meaning | Derivation |
|---|---|---|
| **Strong machine-generated signal** | Score is far on the `full_ai`-consistent side of the frozen model's validation-set distribution | EXP-003A's frozen combined model's `P(machine)`, banded |
| **No strong machine-generated signal** | Score is far on the `human`-consistent side | Same score, banded |
| **Inconclusive** | Score falls in the band around the frozen threshold where the training/validation data itself showed the least separation | Same score, banded |

**Why not a binary human/machine label**: EXP-003A's own accuracy, while very high, is not 100% (45–46/46 depending on threshold) — presenting a hard binary at the exact frozen threshold overstates certainty right at the boundary, which is precisely where the model is least reliable. A three-state band is the same underlying score, presented honestly.

**Why not a three-class (human/full_ai/ai_assisted) essay-level output**: EXP-003C's complete `ai_assisted` collapse (0/16, all metrics 0.0) makes exposing `ai_assisted` as a peer essay-level class actively misleading — it would look like a calibrated third option when it is, in measured fact, indistinguishable from noise at this task. **`ai_assisted` must not appear as an essay-level class in the product.**

**Band-edge calibration**: this audit does **not** compute the exact score cutoffs (that is a bounded, no-retraining analysis task — reslicing the already-computed EXP-003A validation scores — deferred to Phase D, §16). Recommended construction method, stated now for review: pick band edges from the **validation-set score distribution's overlap region** (e.g., the score range where validation human and `full_ai` score histograms actually overlap becomes "Inconclusive"; everything cleanly outside that range on either side becomes "Strong signal" / "No strong signal"). This reuses only already-computed validation scores — no new fitting.

### Sentence level: **"Potentially AI-assisted passage," ranked, not thresholded**

EXP-003B-R1 found the full 29-feature localization model (60% top-1-per-essay accuracy, test) outperforms every feature-group ablation, including the non-length-only group (46.7%) — length/count features contribute real signal to *localization* specifically, unlike essay-level classification. The localization model's own thresholded precision/recall (86.7%/17.6%) is far too weak to support a binary "this sentence is AI" claim per sentence.

**Recommendation**: score every sentence in an essay with the frozen localization model, then surface the **top-K highest-scoring sentences** (K=1–3, tunable in UI copy only, not in the model) as "passages that show measurable patterns associated with AI-assisted writing in the reference data" — a ranking presentation, not a per-sentence binary classification. This directly uses the *metric that actually showed real signal* (top-1 accuracy), not the degenerate raw-threshold metric.

## 6. Recommended frozen detector configuration

**No retraining. Every model below already exists as a completed, evidence-backed fit; this section only selects among them.**

### Primary essay-level classifier

| Field | Value |
|---|---|
| Source experiment | EXP-003A |
| Model | `LogisticRegression` (via `LogisticRegressionCV`, L2, `C=0.005994842503189409`), fit on EXP-003A's 208-row train split, `random_state=42` |
| Feature group | Combined, 29 features (23 stylometric + 6 LM-derived) |
| Preprocessing | `StandardScaler` fit on the same train split |
| Threshold | 0.47 (validation-swept, DEC-015-compliant) |
| Limitations | Binary human-vs-`full_ai` only; does not generalize to `ai_assisted` (not its task); tested against 2 generators, not a universal detector; LM feature group's 6 features are carried along but have never demonstrated incremental value over the 23 stylometric features alone (see note below) |

**A disclosed, not-yet-resolved gap**: EXP-003A/EXP-003C/GEN-001 all found the 23-feature stylometric-only model performs identically to this 29-feature combined model everywhere both were measured. The stylometric-only model was **never taken through DEC-015's formal validation threshold-sweep** (it was only ever evaluated at the default 0.5 reference point as a baseline comparison) — so it does not yet have its own frozen, fully-validated operational threshold. The combined model above is recommended as production PRIMARY specifically because it is the *only* configuration with a complete, already-finished threshold-selection procedure behind it — not because the LM features have been shown to help. **A follow-up, analysis-only task** (sweep a validation threshold for the already-fit stylometric-only baseline — reusing already-computed scores, no new model fitting) **could enable dropping the LM dependency for the primary score entirely; not done in this audit, flagged for a future, separately-authorized pass.**

### Sentence-level localization model

| Field | Value |
|---|---|
| Source experiment | EXP-003B (top1_localization block) / confirmed by EXP-003B-R1 |
| Model | `LogisticRegression` (via `LogisticRegressionCV`), fit on EXP-003B's sentence-level train split |
| Feature group | Combined, 29 features (all-29 group outperformed every ablation for the top-1 metric specifically — length/count features matter here, unlike essay-level) |
| Decision rule | **Ranking** (top-K sentence scores per essay), never the raw 0.34 threshold (shown degenerate: near-universal positive prediction) |
| Limitations | 60% top-1 test accuracy means roughly 2 in 5 essays' actual highest-scored sentence will not be the true AI-touched one; only validated against `ai_assisted` (single-sentence surgical-splice) samples, not other edit patterns |

### Not selected for production

- **EXP-003B/EXP-003C's essay-level `ai_assisted` classifier** — near-chance/complete collapse, excluded from the essay-level product entirely (§5).
- **LM-only feature group as a standalone score** — never demonstrated value; may still be **displayed as supplementary evidence** (raw perplexity/predictability numbers) in an evidence panel, explicitly labeled as measured-but-unproven, per the "keep it only if documented as unproven, do not force it into the narrative" instruction — but must never drive the primary classification alone.
- **EXP-003C's three-class multinomial model** — not used for essay-level product output (§5); its coefficient/failure analysis remains valuable research context, not a production component.

## 7. Evidence mapping (DEC-017 compliance check)

DEC-017's constraint: `essay → features → model → feature contribution → deterministic template → evidence statement`. Never `essay → LLM → "reason"`.

**Verified traceable to a measured feature, for every UI explanation category planned**:

| UI explanation | Feature(s) it must trace to | Status |
|---|---|---|
| "This essay's vocabulary is unusually repetitive/diverse for typical human writing" | `stylo_type_token_ratio`, `stylo_moving_average_ttr`, `stylo_repeated_bigram_ratio`, `stylo_repeated_trigram_ratio` | Computed today, `feature_extractor.py` |
| "This essay's sentences are unusually uniform/varied in length" | `stylo_sentence_length_cv`, `stylo_sentence_length_std` | Computed today |
| "This essay uses longer words / more punctuation than typical" | `stylo_mean_avg_word_length`, `stylo_mean_punctuation_count` | Computed today |
| "This passage's predictability (per the LM instrument) is unusually low/high" | `lm_mean_perplexity`, `lm_mean_predictability_delta` | Computed today, `language_model.py` — **display only, not decisive**, per §6 |
| "This passage was flagged as a candidate AI-touched passage" | Sentence-localization model's score, ranked | Requires the sentence-level model artifact (missing — §8) |

**No planned UI text requires a generative model to produce a "reason."** The template layer (feature value → normalized measurement → fixed evidence sentence) does not exist as code yet (`evidence_mapper.py` is not present, §8) — this is real, necessary Phase D work, not already done.

## 8. Product architecture audit

```
Frontend (Next.js)          EXISTS (scaffold only) — 1 page, 1 real component, 4 empty placeholder dirs
      |
      v
API (/api/analyze)          DOES NOT EXIST — only GET /api/health exists
      |
      v
Normalization                EXISTS — backend/app/services/text_normalizer.py (tested, 5 tests)
      |
      v
Sentence segmentation        EXISTS — backend/app/services/sentence_segmenter.py (tested, 11 tests)
      |
      v
Feature extraction           EXISTS — backend/app/services/feature_extractor.py (tested, 12 tests)
                              + language_model.py (tested, 9 tests)
      |
      v
Frozen detector              MISSING — no serialized model artifact anywhere; only exists as
                              "refit deterministically from research feature files" in scripts/
      |
      v
Sentence localization        MISSING — same gap, sentence-level model not serialized
      |
      v
Deterministic evidence        MISSING — no evidence_mapper.py or equivalent exists
mapping (DEC-017)
      |
      v
Structured response          MISSING — backend/app/models/ is an empty placeholder;
                              no Pydantic response schema exists
```

### Existing, directly reusable

- `backend/app/services/text_normalizer.py`, `sentence_segmenter.py`, `feature_extractor.py`, `language_model.py` — the exact 29-feature pipeline every EXP-003 experiment used, already tested (37 of the 43 backend tests), already the canonical implementation `scripts/*.py` imports rather than duplicates. **No duplication debt found between research and service code.**
- `backend/app/services/validation.py` — essay length validation, already matches the frontend's 20,000-char limit.
- `backend/app/config.py` — settings scaffold, ready to extend with model-artifact paths/version.

### Missing modules (real implementation gaps, not yet started)

1. **Model persistence.** No `.joblib`/`.pkl`/serialized model exists anywhere. Every research script *refits* the scaler+logistic-regression deterministically from `experiments/EXP-003A/features.jsonl` at run time — acceptable for research reproducibility, **not acceptable for a production service** (would require shipping training-data-derived feature files into production and refitting at every startup). Needs: one `joblib.dump` of the frozen scaler + combined-model coefficients (from the already-completed EXP-003A fit, and separately EXP-003B's sentence-level fit), versioned, stored as a build artifact (pattern similar to the existing `.gitignore`'s `*.pt`/`*.bin`/`*.safetensors` rule — needs a `*.joblib` equivalent).
2. **`/api/analyze` route** — does not exist (`backend/app/api/__init__.py` is 0 bytes).
3. **Request/response Pydantic schemas** — `backend/app/models/` is an empty placeholder.
4. **A scorer/detector-loading module** (e.g. `backend/app/services/detector.py`) — load the persisted model once at process start (not per-request), expose a `score_essay(features) -> float` function.
5. **`evidence_mapper.py`** (DEC-017's deterministic template layer) — does not exist at all.
6. **Sentence-localization scoring path** — same missing-artifact problem as #1, specific to the EXP-003B sentence-level model.

### Research-only code that must NOT enter production

`scripts/*.py` in its entirety (generation scripts, QC/screening pipeline, experiment-runner scripts like `run_exp003a.py`/`run_gen001_*.py`/`run_fair001_*.py`) — these are dataset-construction and experiment tooling. Production code should call `backend/app/services/*` functions directly (already the pattern), never import from `scripts/`. `qwen_generate.py`/`phi_generate.py` and the whole generation pipeline have no role in the product (the product analyzes essays, it does not generate them).

### Model/preprocessing/configuration artifacts required

- Serialized `StandardScaler` + `LogisticRegression` for the essay-level primary detector (from EXP-003A's frozen fit).
- Serialized `StandardScaler` + `LogisticRegression` for the sentence-localization model (from EXP-003B's frozen fit).
- A small config file (JSON/YAML) recording: feature-group field order (must exactly match `ALL_FIELDS` from `run_exp003a.py`), frozen threshold (0.47) and band edges (§5, to be computed), model version/experiment-ID provenance (so a served prediction can always be traced back to "EXP-003A, `chosen_C=0.005994842503189409`, frozen 2026-08-15").
- `distilgpt2` weights (already downloaded via `transformers`/HF cache locally; needs to be part of the deploy environment's model cache, not committed to git — consistent with existing `.gitignore` LM-weight exclusions).

## 9. Frontend requirements

Per the hackathon brief's required user experience (accept → analyze → actionable result → flagged passages → explanation → no meaningless bare percentage → communicate limitations), and **not overbuilding**:

**Minimum screens/components** (building on what already exists):

1. **Essay input** — `EssayInput.tsx` already exists; needs its "Analyze" button wired to `POST /api/analyze` (currently permanently disabled) and a loading state.
2. **Results summary** (`ResultsSummary/` — currently empty) — shows the three-state essay-level result (§5) as text + a simple visual (e.g. a banded meter, not a bare percentage), plus the product claim's honest framing (§4/§10).
3. **Evidence panel** (`EvidencePanel/` — currently empty) — lists the 2–4 features that most influenced the result, each mapped through the deterministic template (§7) — e.g. "Vocabulary diversity: unusually high relative to typical student writing."
4. **Essay viewer with passage highlighting** (`EssayViewer/` — currently empty) — renders the submitted essay with the top-K ranked candidate passages (§5) highlighted, each with a hover/click evidence tooltip.
5. **Limitations/uncertainty footer** — always visible, not buried: states the system's scope (which categories it can/cannot classify, per §3), consistent with the "must communicate limitations" requirement.

**Explicitly not building**: a feature-breakdown dashboard beyond the evidence panel (the empty `FeatureBreakdown/` directory should likely be folded into the evidence panel rather than built as a separate dense-dashboard screen — a hackathon-scale product doesn't need two feature-display surfaces), no user accounts, no essay history/storage UI, no batch upload — none of these are required by the brief or supported by anything tested.

## 10. Backend requirements (concrete, from §8)

1. `POST /api/analyze` — accepts essay text (reusing existing `validation.py` length checks), returns a structured response.
2. Response schema (new, `backend/app/models/`): essay-level three-state result + raw score, top-K flagged sentence indices/text + scores, evidence list (feature name, human-readable label, normalized value, direction), applicable limitations/scope text, and a version/provenance stamp (`detector_version`, `experiment_id`).
3. `detector.py` — loads persisted model artifacts once at startup (not per-request); exposes scoring functions for both the essay-level and sentence-level models.
4. `evidence_mapper.py` — deterministic feature-value → evidence-statement template layer (DEC-017).
5. Error handling for every failure state in §11.

## 11. Failure-state behavior (defined now, not implemented)

| Case | Behavior |
|---|---|
| Empty input | Reject at validation layer (`validation.py` already does this) — HTTP 422, no analysis attempted. |
| Very short input (below `min_essay_chars`) | Same — rejected before reaching the detector; the detector was never validated on very short text and should not silently produce a score for it. |
| Very long input (above `max_essay_chars`, 20,000) | Rejected before reaching the detector (existing frontend/backend limit already aligned). |
| Insufficient scorable LM tokens (e.g. all-stopword or degenerate text) | `language_model.py` already returns `None` for unscorable sentences (tested); the essay-level feature aggregation already mean-pools over non-`None` values only — if **zero** sentences are scorable, the response must say so explicitly ("LM-derived evidence unavailable for this essay") rather than silently omitting it or fabricating a value. |
| Sentence segmentation failure | Should not occur for valid text given spaCy's robustness (11 existing tests cover edge cases); if it somehow throws, return a clear 500 with "analysis failed" — never a fabricated result. |
| Feature extraction failure | Same — fail loudly, never silently substitute a default/mean value into a real user's result. |
| Model inference failure (e.g. artifact not loaded) | Startup should fail fast if the model artifact is missing/corrupt (never serve requests with a partially-loaded detector); a runtime failure mid-request returns 500, not a fabricated score. |
| No strong signal | Presented as its own honest state (§5), not hidden or forced into "inconclusive." |
| Ambiguous score (near the threshold) | Falls into "Inconclusive" band (§5) by design — this is the intended behavior, not a failure. |
| Zero passages flagged above the candidate threshold | Explicitly state "no passages stood out as unusual" rather than forcing a top-K display when nothing scored notably high. |
| Multiple flagged passages | Show all above whatever candidate cutoff is chosen (§5's top-K), each with its own evidence — never collapse multiple distinct passages into one vague statement. |

**Standing rule across every case**: never fabricate a value when evidence is missing or a component fails — this is the same discipline already used throughout the research phase (missing LM scores excluded, not imputed; QC failures reported, not hidden).

## 12. Performance requirements (documented from existing measurements, not optimized)

| Item | From existing measurement | Note |
|---|---|---|
| distilgpt2 load time | Not separately benchmarked for the small LM; `language_model.py` uses `lru_cache` to load once, not per-request — consistent with a production "load at startup" pattern already in place for the LM. | Reuse existing pattern. |
| Phi-3.5-mini-instruct / Qwen2.5-1.5B-Instruct load/inference time | **Not applicable to production** — these are research-only generation models (§8), never loaded by the served application. | N/A for product. |
| Feature extraction time | Not separately benchmarked; spaCy `en_core_web_sm` + `distilgpt2` forward pass per essay — same cost profile as every EXP-003 feature-extraction run, which processed hundreds of essays in well under an hour total on this machine. | Per-essay cost is small; expect low-single-digit seconds per request on CPU. |
| Maximum supported essay length | 20,000 characters (existing `max_essay_chars`, already enforced both frontend and backend). | Already decided, no new work needed. |
| Memory requirements | distilgpt2 (small, already loaded successfully throughout this project on a 16GB machine) + spaCy `en_core_web_sm` (small) + a logistic-regression artifact (tiny) — **far lighter** than GEN-001's Phi-3.5-mini-instruct (3.8B params), which is not part of the production path at all. | No 16GB-memory-pressure risk expected for the production model set — that problem was specific to research-only generation models. |
| Should the model remain loaded | Yes — `lru_cache`-style singleton loading (already the pattern for the LM) should extend to the new detector/localization model artifacts. | Direct extension of existing code pattern. |
| CPU-only operation practicality | Fully practical — every EXP-003 experiment's actual classifier (logistic regression) is CPU-trivial; the only GPU-relevant cost in this whole project was Phi-3.5-mini-instruct generation (GEN-001, research-only, not shipped). | No GPU dependency for the product. |
| Is MPS optional | Yes, and irrelevant to production — MPS was only used to make research-only Phi-3.5-mini-instruct generation practical (GEN-001); the shipped detector never needs it. | N/A for product. |

## 13. Security / repository audit findings

- **No secrets or credentials found** anywhere in the repository (API keys, tokens, passwords) — verified by targeted search across all tracked file types.
- **No `.env` file tracked in git** — none exists in the repo at all currently; `.gitignore` correctly excludes `.kaggle/`, `kaggle.json`, `**/kaggle.json`.
- **No raw or generated dataset files tracked** — `data/` contains only `.gitkeep` in git; PERSUADE/ELLIPSE corpora and all `data/generated/*` outputs (including GEN-001's) are correctly excluded.
- **No model weights tracked** — `.gitignore` excludes `*.pt`/`*.bin`/`*.safetensors`; confirmed none are tracked.
- **Two stray debug-log files ARE tracked and should be removed before freeze**: `experiments/EXP-003A/extract_features.log` and `experiments/EXP-003B/extract_features.log` — stdout captures containing this machine's local absolute path (`/Volumes/DevSSD/Developer/apply_tasks/AI-detector/...`). Not a credential leak, but not intentional documentation either — a `.gitignore` gap (`experiments/**/results/` doesn't cover top-level `.log` files). **Recommendation: add `experiments/**/*.log` to `.gitignore` and `git rm --cached` these two files** (an implementation-phase action, not done in this audit turn).
- **No absolute-path leakage in any source code** (`.py`/`.ts`/`.tsx`) — only in the two log files above.
- **Frontend has no `.env`**, no client-side secret risk currently (no API calls exist yet to misconfigure).
- **Uncommitted work exists** from the just-completed GEN-001/FAIR-001 phase (new scripts, reports, experiment outputs, doc updates) — legitimate research output, not stray artifacts, but should be committed (or explicitly deferred) as part of any freeze checklist; not resolved by this audit itself, since commits were not requested.

**Research-only vs. production-required, explicit split**:

| Research-only (never ships) | Production-required (ships) |
|---|---|
| `scripts/*.py` (all generation, QC, experiment-runner, GEN-001/FAIR-001 scoring scripts) | `backend/app/services/*.py` (all four existing modules) |
| `data/generated/*`, `data/raw/*` | Persisted model artifacts (§8, to be created) |
| `experiments/*` | `backend/app/main.py`, new `api/`, `models/` modules (to be created) |
| Qwen/Phi generation model weights | `distilgpt2` weights (already the production LM) |
| `reports/*.md`, `docs/decisions/*` | spaCy `en_core_web_sm` |

## 14. Documentation audit

**Genuine contradictions found and resolved in this pass** (not rewriting historical experiment reports — updating meta-documents that were explicit placeholders pending exactly this evidence):

- `docs/evaluation.md` stated "Status: not started. No model, scoring system, or dataset exists yet" — **false** as of six completed experiments. Updated to point at the actual results (§1 of this document) rather than rewritten with invented content.
- `docs/failure-analysis.md` Part 2 ("Detector Failures") stated "Status: not started... no trained/calibrated detector yet" and required "at least three real, confidently-wrong examples" once available — **now available and not yet recorded.** Populated with three real cases already documented in existing experiment reports (not invented): (1) family `302DC21A6DEE`, misclassified across four independent experiments (EXP-003A, EXP-003B, EXP-003C, GEN-001) — a genuine, reproducible detector quirk; (2) EXP-003C's complete `ai_assisted` collapse as a systemic failure mode, not a single essay; (3) GEN-001's LM-only degradation under generator shift as a feature-level failure mode. See the updated file for the full required structure (sample/ground truth/prediction/feature values/analysis/follow-up idea) per each.
- No other genuine contradictions found between `project-status.md`, `decision-summary.md`, `fairness.md`, `final-decision-guide.md`, and the six experiment reports — these were kept current at the end of each experiment's own turn.

**Not changed**: any historical experiment report (`reports/EXP-*.md`, `reports/GEN-001.md`, `reports/FAIR-001.md`) — read-only source of truth, per explicit instruction.

## 15. Decision-record status summary (DEC-001 through DEC-019)

| ID | Decision | Status | Affects production? |
|---|---|---|---|
| DEC-001 | FastAPI backend | Accepted | Yes — the framework the new `/api/analyze` route is built in. |
| DEC-002 | Next.js frontend | Accepted | Yes — the framework the new UI components are built in. |
| DEC-003 | Monorepo layout | Accepted | Yes — production code and research code share a repo; §13's research/production split matters more as a result. |
| DEC-004 | LM as instrument, never classifier | Accepted (evidence-updated 4x: EXP-003A, EXP-003B, EXP-003C, GEN-001 — LM group never showed value, status still open re: whether to *drop* the feature group) | **Yes, directly** — governs §6's decision to keep the LM group in the frozen combined model but never let it drive the primary decision alone, and to display (not decide with) its output. |
| DEC-005 | spaCy sentence segmentation | Accepted | Yes — `sentence_segmenter.py` ships as-is. |
| DEC-006 | Phase 3 feature scope | Provisional | Yes — the feature set is what `feature_extractor.py` computes today; no change proposed. |
| DEC-007 | distilgpt2 local LM | Accepted | Yes — ships as the production LM; no larger/different model proposed. |
| DEC-008 | Whole-essay single-pass LM scoring | Accepted | Yes — `language_model.py`'s scoring approach ships as-is. |
| DEC-009 | PERSUADE + ELLIPSE data sources | Accepted (live-verified) | Indirectly — governs the *evidence base* (training data), not the shipped code; ELLIPSE also now used by FAIR-001. |
| DEC-010 | Qwen2.5-1.5B-Instruct generation model | Provisional (pilot-tested) | **No** — research-only, generation model never ships. |
| DEC-011 | Mixed-sample generation mechanism | Provisional (strategic decision made) | **No** — research-only, governs dataset construction, not the product. |
| DEC-012 | Semantic-risk screening signal | Accepted (triage only) | **No** — dataset-construction QC tool, not part of the served application. |
| DEC-013 | Claim-survival screening signal | Accepted (screening only) | **No** — same as DEC-012. |
| DEC-014 | EXP-003 feature set & baselines | Provisional (validated) | **Yes, directly** — defines the exact 29-field feature vector §6's frozen models require. |
| DEC-015 | Model selection & threshold strategy | Provisional (validated, degenerate-threshold risk documented) | **Yes, directly** — governs why the combined model (not stylometric-only) is recommended (§6), and why sentence-localization uses ranking, not the raw threshold (§5). |
| DEC-016 | Sentence-localization evaluation design | Provisional (design validated) | **Yes** — governs how sentence-level "ground truth" and evaluation are understood; informs the top-K ranking design (§5). |
| DEC-017 | Evidence/explanation mapping | Provisional (first worked examples applied) | **Yes, directly** — the entire §7 evidence-mapping design is built to satisfy this decision; `evidence_mapper.py` (missing, §8) is this decision's actual implementation. |
| DEC-018 | FAIR-001 fairness methodology | Provisional (executed, Category A) | **Yes** — governs §10's limitations/fairness-note requirement (§10 UI copy) and the standing "no fairness certification" framing. |
| DEC-019 | GEN-001 generator selection | Provisional (executed, mixed transfer) | **Yes** — the cross-generator evidence behind §4's product claim and §2's "tested against two generators" scoping language. |

**No status changed merely because the project is entering production** — every status above is exactly what each decision record already stated after its own experiment/evidence, unchanged by this audit.

## 16. Phased implementation plan

**Execution status (2026-08-15): Phase I complete. Phases A and B —
including C's scope (both artifacts built in one pass) — complete, see
[production-detector.md](production-detector.md) for the full record.
Phases D onward not started, require separate authorization.**

| Phase | Purpose | Files/modules | Depends on | Tests required | Acceptance criteria |
|---|---|---|---|---|---|
| **A — Production backend extraction** | Confirm `backend/app/services/*` is fully sufficient and add nothing research-specific to it | Audit only, likely no code change | None | None new | ✅ Confirmed: no changes needed (§8 finding: no duplication debt) |
| **B — Frozen model integration** | Persist EXP-003A's and EXP-003B's already-fit models as loadable artifacts | New: `backend/app/services/detector.py`, `feature_spec.py`, `essay_feature_vector.py`; new `.joblib` artifacts; `.gitignore` update | Phase A | Unit tests: loaded model reproduces the exact `chosen_C`/coefficients already recorded in `results.json` (a reproduction check, same discipline as GEN-001/FAIR-001's) | ✅ **Done** — refit `chosen_C` and all 46 frozen test scores reproduce EXP-003A's recorded values exactly (tolerance `5e-5`) |
| **C — Sentence localization** | Same persistence for the sentence-level ranking model | New: `sentence_feature_vectors.py`; extends `detector.py` | Phase B | Unit test: reproduces EXP-003B's recorded top-1 test accuracy exactly on its own test set | ✅ **Done** (built alongside B) — top-1 test accuracy reproduces exactly (9/15, 60.0%) |
| **D — Deterministic evidence mapping** | Implement DEC-017's template layer + compute the three-state band edges (§5) from existing validation scores | New: `backend/app/services/evidence_mapper.py`; a small calibration script (analysis-only, reuses existing validation scores, no new fitting) | Phase B | Unit tests per template rule (feature value → correct evidence sentence); a correctness test that no template ever emits causal language ("because," "proves") | Every evidence statement traces to a real feature value (§7 table), verified in tests |
| **E — API** | `POST /api/analyze` | New: `backend/app/api/analyze.py` (or similar), `backend/app/models/` schemas | Phases B–D | Integration tests (extends the one existing API-level test pattern from `test_health.py`); failure-state tests per §11's table | Valid essay → structured response with essay-level state, flagged passages, evidence, limitations text; each §11 failure case handled without fabrication |
| **F — Frontend** | Wire `EssayInput`, build `ResultsSummary`/`EvidencePanel`/`EssayViewer` | `frontend/components/*` (fill the 4 currently-empty directories), `frontend/lib/` (API client, currently empty) | Phase E | Component tests if a frontend test framework is added (none currently exists — flagged as a gap, not assumed) | End-to-end: paste essay → see three-state result, flagged passages highlighted, evidence shown, limitations visible |
| **G — End-to-end tests** | Full pipeline integration coverage | `backend/tests/test_analyze_e2e.py` or similar | Phases E–F | New — currently zero end-to-end coverage exists (§8 finding) | A known human essay and a known `full_ai` essay from PRIMARY-DATASET-v1 each produce the expected essay-level state through the real API |
| **H — Performance** | Verify §12's documented expectations hold under the real integrated pipeline | No new modules, benchmarking scripts only | Phase G | Timing assertions (loose bounds, not micro-optimized) | Single-essay analysis completes in a few seconds on CPU, matching §12's expectations |
| **I — Security/repository cleanup** | Remove the two tracked debug logs (§13), extend `.gitignore`, commit outstanding GEN-001/FAIR-001 research artifacts | `.gitignore`, `git rm --cached` the two log files | None (can run anytime) | None | `git ls-files` shows no `.log` files with local paths; repo status clean |
| **J — Final documentation/demo** | Update `project-status.md`/`README` to reflect a working product; prepare demo script | Docs only | Phases E–H | None | A reviewer can read one document and understand what the product does, what it doesn't, and why |

**Recommended order**: B → C → D → E → F → G → H, with A confirmed trivially first and I/J running in parallel wherever convenient (I has no dependencies; J should be last so it describes the finished state).

## 17. Remaining risks

- **Band-edge calibration (§5) is not yet computed** — a small, low-risk, no-retraining analysis task, but the three-state UI cannot ship without it.
- **Stylometric-only-vs-combined threshold gap (§6)** — a real, disclosed methodological loose end; low risk to ship with combined-as-is, but worth closing for a cleaner story.
- **Zero end-to-end/API-level test coverage today** — the entire proposed pipeline (Phases B–G) is new code; the existing 43 tests validate the service *functions* in isolation, not the integrated request flow.
- **No frontend test framework exists** — Phase F's UI correctness currently has no automated safety net beyond manual verification.
- **17.6% sentence-localization precision** means the UI must work hard (copy, framing, visual design) to avoid implying more certainty than the number supports — a communication risk, not a modeling one.
- **FAIR-001's n=10 sample** means the fairness note (§10) must be re-stated prominently and cannot be softened over time without new, larger evaluation data.
- **Two tracked debug-log files** (§13) are a minor but real cleanliness gap before any "frozen" public release.

## 18. Recommended order of implementation

1. **Phase I** (repository cleanup) — no dependencies, do it first, cheap.
2. **Phase B** (persist the essay-level model) — unblocks everything else; includes the stylometric-vs-combined threshold-gap decision as a explicit go/no-go checkpoint (ship combined-as-is now, or spend the extra analysis cycle first — a call for the next authorization, not this audit).
3. **Phase D**'s calibration sub-task (band edges) can run in parallel with Phase B once B's artifact exists, since it only needs the already-computed validation scores.
4. **Phase C** (sentence localization) — same pattern as B, can run in parallel with B/D once the approach is proven once.
5. **Phase D** (evidence mapper, full) — needs B/C's outputs defined.
6. **Phase E** (API) — needs B/C/D.
7. **Phase F** (frontend) — needs E; can start component scaffolding (non-data-dependent parts) earlier if desired.
8. **Phase G** (end-to-end tests) — needs E/F.
9. **Phase H** (performance check) — needs G.
10. **Phase J** (final docs/demo) — last.

---

**This document is a synthesis and plan only. No phase above has been started. Explicit authorization is required before Phase A (or any phase) begins.**
