"""
EXP-003B-R1 -- diagnostic: does sentence-level localization signal
survive controlling for length/count features? Uses the EXISTING
EXP-003B sentence-level dataset unchanged (no new generation, no
relabeling, no split changes) -- see
experiments/EXP-003B/features_sentence.jsonl.

Feature-group definitions (exact columns, decided BEFORE running,
documented here and in reports/EXP-003B-R1.md):

LENGTH_COUNT (11): every feature whose definition is a raw or
trivially-normalized COUNT of words/chars/sentences/tokens/punctuation.
Includes `lm_mean_token_count` despite its "lm_" prefix -- per explicit
instruction, a feature is only "LM evidence" if it reflects actual
predictability information, not because its column name starts with
lm_. Token count is a count, not a predictability measure.

  stylo_sentence_count, stylo_sentence_length_mean,
  stylo_sentence_length_std, stylo_sentence_length_cv,
  stylo_short_sentence_ratio, stylo_medium_sentence_ratio,
  stylo_long_sentence_ratio, stylo_mean_word_count,
  stylo_mean_char_count, stylo_mean_punctuation_count,
  lm_mean_token_count

STYLO_NON_LENGTH (13): stylometric features NOT defined as a raw count
-- vocabulary diversity, repetition ratios (already length-normalized),
word-length-in-characters (a lexical/vocabulary signal, not a sentence-
length/count signal), POS ratios, and dependency depth (a syntactic-
structure measure; disclosed judgment call -- dependency depth is known
to correlate with sentence length in general linguistics, but its
definition is not itself a length or count).

  stylo_type_token_ratio, stylo_moving_average_ttr,
  stylo_rare_word_ratio, stylo_repeated_bigram_ratio,
  stylo_repeated_trigram_ratio, stylo_repeated_sentence_opening_ratio,
  stylo_mean_avg_word_length, stylo_mean_noun_ratio,
  stylo_mean_verb_ratio, stylo_mean_adj_ratio, stylo_mean_adv_ratio,
  stylo_mean_pronoun_ratio, stylo_mean_dependency_depth

LM_PREDICTABILITY_NON_COUNT (5): genuine LM predictability signals,
excluding the count feature.

  lm_mean_mean_log_prob, lm_mean_median_log_prob,
  lm_mean_log_prob_variance, lm_mean_perplexity,
  lm_mean_predictability_delta

Six requested groups, mapped onto the three disjoint sets above:

  A. ALL_29                = LENGTH_COUNT + STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT  (29)
  B. LENGTH_COUNT_ONLY      = LENGTH_COUNT                                                   (11)
  C. NON_LENGTH_COMBINED    = STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT                 (18)
  D. LM_ONLY                = LM_PREDICTABILITY_NON_COUNT + lm_mean_token_count              (6, matches EXP-003B's original "LM-only" definition)
  E. STYLO_NON_LENGTH_ONLY  = STYLO_NON_LENGTH                                                (13)
  F. COMBINED_NON_LENGTH    = STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT                 (18)

**By construction, C and F are the identical 18-feature set** once
`lm_mean_token_count` is classified as a length/count feature (as
instructed) -- "length/count removed from ALL_29" and "non-length
stylometric combined with genuine LM predictability" describe the same
set. This is disclosed explicitly, not hidden: one model fit serves
both labels, not a silent shortcut around the requested 6-group design.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import fit_logreg_cv, metrics_at_threshold, select_threshold_on_validation  # noqa: E402
from run_exp003b import to_xy  # noqa: E402

SENTENCE_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003B-R1" / "results.json"

LENGTH_COUNT = [
    "stylo_sentence_count", "stylo_sentence_length_mean", "stylo_sentence_length_std",
    "stylo_sentence_length_cv", "stylo_short_sentence_ratio", "stylo_medium_sentence_ratio",
    "stylo_long_sentence_ratio", "stylo_mean_word_count", "stylo_mean_char_count",
    "stylo_mean_punctuation_count", "lm_mean_token_count",
]
STYLO_NON_LENGTH = [
    "stylo_type_token_ratio", "stylo_moving_average_ttr", "stylo_rare_word_ratio",
    "stylo_repeated_bigram_ratio", "stylo_repeated_trigram_ratio",
    "stylo_repeated_sentence_opening_ratio", "stylo_mean_avg_word_length",
    "stylo_mean_noun_ratio", "stylo_mean_verb_ratio", "stylo_mean_adj_ratio",
    "stylo_mean_adv_ratio", "stylo_mean_pronoun_ratio", "stylo_mean_dependency_depth",
]
LM_PREDICTABILITY_NON_COUNT = [
    "lm_mean_mean_log_prob", "lm_mean_median_log_prob", "lm_mean_log_prob_variance",
    "lm_mean_perplexity", "lm_mean_predictability_delta",
]
assert len(LENGTH_COUNT) == 11 and len(STYLO_NON_LENGTH) == 13 and len(LM_PREDICTABILITY_NON_COUNT) == 5

GROUPS = {
    "A_all_29": LENGTH_COUNT + STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT,
    "B_length_count_only": LENGTH_COUNT,
    "C_non_length_combined": STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT,
    "D_lm_only": LM_PREDICTABILITY_NON_COUNT + ["lm_mean_token_count"],
    "E_stylo_non_length_only": STYLO_NON_LENGTH,
    "F_combined_non_length": STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT,  # identical to C, see module docstring
}
for name, fields in GROUPS.items():
    assert len(fields) == len(set(fields)), f"duplicate columns in group {name}"

RANDOM_SEED = 42


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_group(records: list[dict], fields: list[str], group_name: str) -> dict:
    from sklearn.preprocessing import StandardScaler

    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    test = [r for r in records if r["split"] == "test"]

    X_train, y_train = to_xy(train, fields, "ai_assisted")
    X_val, y_val = to_xy(val, fields, "ai_assisted")
    X_test, y_test = to_xy(test, fields, "ai_assisted")

    scaler = StandardScaler().fit(X_train)
    Xs_train, Xs_val, Xs_test = scaler.transform(X_train), scaler.transform(X_val), scaler.transform(X_test)

    model = fit_logreg_cv(Xs_train, y_train)
    scores_val = model.predict_proba(Xs_val)[:, 1]

    threshold_info = select_threshold_on_validation(y_val, scores_val)
    chosen_threshold = threshold_info["chosen_threshold"]

    scores_test = model.predict_proba(Xs_test)[:, 1]
    test_metrics = metrics_at_threshold(y_test, scores_test, chosen_threshold)

    # top1_localization_accuracy (imported from run_exp003b) hardcodes the
    # full 29-feature ALL_FIELDS internally, so it isn't reusable for a
    # per-group model trained on a feature subset -- _top1_for_group below
    # is the group-aware equivalent.
    top1 = _top1_for_group(records, model, scaler, fields)

    return {
        "group_name": group_name,
        "n_features": len(fields),
        "features": fields,
        "chosen_C": float(model.C_[0]),
        "threshold_selection": threshold_info,
        "test_metrics_at_frozen_threshold": test_metrics,
        "top1_localization": top1,
    }


def _top1_for_group(records, model, scaler, fields):
    import numpy as np

    def top1(split_name):
        by_essay: dict[str, list[dict]] = {}
        for r in records:
            if r["split"] == split_name:
                by_essay.setdefault(r["essay_sample_id"], []).append(r)
        n_pos, n_correct = 0, 0
        for essay_id, rows in by_essay.items():
            if not any(r["label"] == "ai_assisted" for r in rows):
                continue
            n_pos += 1
            X = np.array([[r[f] for f in fields] for r in rows], dtype=float)
            Xs = scaler.transform(X)
            scores = model.predict_proba(Xs)[:, 1]
            top_idx = int(np.argmax(scores))
            if rows[top_idx]["label"] == "ai_assisted":
                n_correct += 1
        return {"n_essays_with_a_locatable_positive_sentence": n_pos, "n_top1_correct": n_correct,
                "top1_accuracy": n_correct / n_pos if n_pos else None}

    return {"validation": top1("validation"), "test": top1("test")}


def main() -> None:
    records = load_jsonl(SENTENCE_FEATURES_PATH)
    print(f"Loaded {len(records)} sentence-level records (unchanged from EXP-003B)")

    results = {"dataset": "experiments/EXP-003B/features_sentence.jsonl (unmodified)"}
    computed_cf = None
    for name, fields in GROUPS.items():
        if name == "F_combined_non_length" and computed_cf is not None:
            print(f"\n=== Group {name}: identical to C_non_length_combined, reusing that result ===")
            results[name] = {**computed_cf, "group_name": name, "note": "identical feature set to C_non_length_combined, see module docstring"}
            continue
        print(f"\n=== Group {name}: {len(fields)} features ===")
        r = run_group(records, fields, name)
        results[name] = r
        if name == "C_non_length_combined":
            computed_cf = r
        print(f"  chosen_threshold={r['threshold_selection']['chosen_threshold']} "
              f"test_f1_machine={r['test_metrics_at_frozen_threshold']['f1_machine']:.3f} "
              f"test_precision={r['test_metrics_at_frozen_threshold']['precision_machine']:.3f} "
              f"test_recall={r['test_metrics_at_frozen_threshold']['recall_machine']:.3f} "
              f"top1_test={r['top1_localization']['test']['top1_accuracy']}")

    import platform

    import sklearn

    results["reproducibility"] = {
        "random_seed": RANDOM_SEED, "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "source_dataset": "experiments/EXP-003B/features_sentence.jsonl",
        "note": "PRIMARY-DATASET-v1 and EXP-003B's sentence-level dataset are UNCHANGED by this script",
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
