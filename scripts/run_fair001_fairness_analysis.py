"""
FAIR-001 -- Stage 2: fairness join and subgroup analysis. Joins the
already-frozen, already-scored predictions (run_fair001_score_all.py's
output) against PERSUADE's `ell_status` field (primary variable, DEC-018)
and, where available, ELLIPSE's continuous proficiency subscores
(secondary/exploratory variable, FAIR-001.md), via `family_id ==
essay_id_comp` / `text_id_kaggle`. This join happens ONLY in this
analysis script, in memory, and is never written back into any feature
file or used to retrain anything.

Small-sample rule (DEC-018, fixed in advance): fewer than 10 subgroup
members -> reported as INSUFFICIENT DATA, never given a bare rate
presented as reliable.

Output: experiments/FAIR-001/results.json
"""

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

PERSUADE_FILE = REPO_ROOT / "data" / "raw" / "persuade_2.0" / "persuade_2.0_human_scores_demo_id_github.csv"
ELLIPSE_FILE = REPO_ROOT / "data" / "raw" / "ellipse_corpus" / "ELLIPSE_Final_github.csv"
FAIR001_DIR = REPO_ROOT / "experiments" / "FAIR-001"
RESULTS_PATH = FAIR001_DIR / "results.json"

MIN_SUBGROUP_N = 10  # fewer than this -> INSUFFICIENT DATA (DEC-018, fixed before execution)

DEMOGRAPHIC_FIELDS = ["gender", "race_ethnicity", "economically_disadvantaged", "student_disability_status", "ell_status"]

FEATURE_FILES_TO_CHECK = [
    REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl",
    REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl",
    REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl",
    REPO_ROOT / "experiments" / "EXP-003C" / "features_essay.jsonl",
    REPO_ROOT / "experiments" / "GEN-001" / "features_phi.jsonl",
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify_no_demographic_leakage() -> dict:
    """Programmatic check, run every time this script executes -- not a
    one-off design-phase claim. Returns {file: [leaked fields]} -- empty
    dict means clean."""
    leaks = {}
    for path in FEATURE_FILES_TO_CHECK:
        if not path.exists():
            continue
        records = load_jsonl(path)
        found = set()
        for r in records:
            found |= (set(r.keys()) & set(DEMOGRAPHIC_FIELDS))
        if found:
            leaks[str(path)] = sorted(found)
    return leaks


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    phat = k / n
    denom = 1 + z**2 / n
    center = phat + z**2 / (2 * n)
    margin = z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))
    return ((center - margin) / denom, (center + margin) / denom)


def load_ell_status_by_family() -> dict[str, str]:
    import pandas as pd

    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    out = {}
    for _, row in df.iterrows():
        val = row["ell_status"]
        out[row["essay_id_comp"]] = val if isinstance(val, str) and val.strip() else "unlabeled"
    return out


def load_ellipse_proficiency_by_family() -> dict[str, dict]:
    import pandas as pd

    df = pd.read_csv(ELLIPSE_FILE, dtype={"text_id_kaggle": str})
    out = {}
    for _, row in df.iterrows():
        out[row["text_id_kaggle"]] = {
            "Overall": float(row["Overall"]), "Cohesion": float(row["Cohesion"]),
            "Syntax": float(row["Syntax"]), "Vocabulary": float(row["Vocabulary"]),
            "Phraseology": float(row["Phraseology"]), "Grammar": float(row["Grammar"]),
            "Conventions": float(row["Conventions"]),
        }
    return out


def score_summary(scores: list[float]) -> dict:
    import numpy as np

    if not scores:
        return {"n": 0}
    arr = np.array(scores)
    return {
        "n": int(len(arr)), "mean": round(float(np.mean(arr)), 4), "median": round(float(np.median(arr)), 4),
        "std": round(float(np.std(arr)), 4), "min": round(float(np.min(arr)), 4), "max": round(float(np.max(arr)), 4),
    }


def subgroup_report(records: list[dict], ell_status_by_family: dict[str, str], role: str) -> dict:
    """role is 'human_false_positive' or 'ai_false_negative' -- controls
    which error type and which score is examined."""
    by_group: dict[str, list[dict]] = {}
    for r in records:
        group = ell_status_by_family.get(r["family_id"], "unlabeled")
        by_group.setdefault(group, []).append(r)

    out = {}
    for group in ("Yes", "No", "unlabeled"):
        recs = by_group.get(group, [])
        n = len(recs)
        errors = sum(1 for r in recs if (r["false_positive"] if role == "human_false_positive" else r["false_negative"]))
        rate = errors / n if n else None
        scores = [r["score"] for r in recs]
        entry = {
            "n": n,
            "error_count": errors,
            "error_rate": round(rate, 4) if rate is not None else None,
            "score_distribution": score_summary(scores),
            "sufficient_data": n >= MIN_SUBGROUP_N,
        }
        if n >= MIN_SUBGROUP_N:
            lo, hi = wilson_interval(errors, n)
            entry["error_rate_95ci"] = [round(lo, 4), round(hi, 4)]
        else:
            entry["error_rate_95ci"] = None
            entry["note"] = f"INSUFFICIENT DATA (n={n} < {MIN_SUBGROUP_N}) -- rate not to be treated as reliable"
        out[group] = entry
    return out


def ellipse_secondary_analysis(exp003a_scored: list[dict], ell_status_by_family: dict, ellipse_by_family: dict) -> dict:
    """Exploratory only: correlate ELLIPSE's continuous Overall
    proficiency score against the frozen detector's raw P(machine) score,
    for the small set of families present in both PERSUADE and ELLIPSE.
    n is even smaller than the primary ell_status=Yes group -- reported
    with maximal caution, never as a formal fairness conclusion."""
    human_scores = {r["family_id"]: r["score"] for r in exp003a_scored if r["true_label"] == "human"}
    rows = []
    for family_id, prof in ellipse_by_family.items():
        if family_id in human_scores:
            rows.append({
                "family_id": family_id,
                "ell_status": ell_status_by_family.get(family_id, "unlabeled"),
                "detector_p_machine_score": human_scores[family_id],
                "ellipse_overall_proficiency": prof["Overall"],
            })
    n = len(rows)
    result = {"n": n, "rows": rows, "sufficient_data": n >= MIN_SUBGROUP_N}
    if n < MIN_SUBGROUP_N:
        result["note"] = f"INSUFFICIENT DATA (n={n} < {MIN_SUBGROUP_N}) -- descriptive rows only, no correlation statistic computed or claimed"
    return result


def main() -> None:
    leaks = verify_no_demographic_leakage()
    if leaks:
        raise RuntimeError(f"Demographic field leakage detected in feature files -- STOP: {leaks}")
    print("Verified: no demographic field present in any feature file used by this project.")

    ell_status_by_family = load_ell_status_by_family()
    ellipse_by_family = load_ellipse_proficiency_by_family()

    exp003a_scored = load_jsonl(FAIR001_DIR / "scored_exp003a_all_families.jsonl")
    exp003b_scored = load_jsonl(FAIR001_DIR / "scored_exp003b_essay_all_families.jsonl")

    # Distribution of ell_status among the 150 PRIMARY-DATASET-v1 families (re-verified, not assumed)
    all_family_ids = {r["family_id"] for r in exp003a_scored} | {r["family_id"] for r in exp003b_scored}
    group_counts = {"Yes": 0, "No": 0, "unlabeled": 0}
    for fid in all_family_ids:
        group_counts[ell_status_by_family.get(fid, "unlabeled")] += 1

    results: dict = {
        "no_demographic_leakage_verified": True,
        "n_families_total": len(all_family_ids),
        "ell_status_distribution_all_families": group_counts,
    }

    # --- EXP-003A (human vs full_ai): human false-positive rate by ell_status ---
    human_a = [r for r in exp003a_scored if r["true_label"] == "human"]
    machine_a = [r for r in exp003a_scored if r["true_label"] == "machine"]
    results["exp003a_human_false_positive_by_ell_status"] = subgroup_report(human_a, ell_status_by_family, "human_false_positive")
    results["exp003a_ai_false_negative_by_ell_status"] = subgroup_report(machine_a, ell_status_by_family, "ai_false_negative")

    # --- EXP-003B essay-level (human vs ai_assisted): SCOPED WITH CAVEAT, near-chance detector ---
    human_b = [r for r in exp003b_scored if r["true_label"] == "human"]
    ai_assisted_b = [r for r in exp003b_scored if r["true_label"] == "ai_assisted"]
    results["exp003b_essay_level_caveat"] = (
        "EXP-003B's essay-level detector performs at near-chance level (frozen threshold 0.34 flags "
        "almost everyone ai_assisted: validation recall_machine=1.0, precision_machine=0.5). Any subgroup "
        "finding below answers 'does a near-random classifier's randomness correlate with subgroup', "
        "NOT 'does a working detector treat subgroups differently' -- these are different questions "
        "(FAIR-001.md A.4)."
    )
    results["exp003b_human_false_positive_by_ell_status"] = subgroup_report(human_b, ell_status_by_family, "human_false_positive")
    results["exp003b_ai_assisted_false_negative_by_ell_status"] = subgroup_report(ai_assisted_b, ell_status_by_family, "ai_false_negative")

    # --- ELLIPSE secondary/exploratory analysis ---
    results["ellipse_secondary_analysis"] = ellipse_secondary_analysis(exp003a_scored, ell_status_by_family, ellipse_by_family)

    # --- Reproducibility record ---
    results["reproducibility"] = {
        "scoring_script": "scripts/run_fair001_score_all.py",
        "analysis_script": "scripts/run_fair001_fairness_analysis.py",
        "exp003a_frozen_threshold": 0.47,
        "exp003b_essay_frozen_threshold": 0.34,
        "min_subgroup_n_threshold": MIN_SUBGROUP_N,
        "fairness_variable_source": "PERSUADE 2.0 ell_status (primary), ELLIPSE_Final_github.csv proficiency subscores (secondary/exploratory)",
        "join_key": "family_id == essay_id_comp (PERSUADE) == text_id_kaggle (ELLIPSE)",
        "demographic_fields_checked": DEMOGRAPHIC_FIELDS,
        "feature_files_checked_for_leakage": [str(p.relative_to(REPO_ROOT)) for p in FEATURE_FILES_TO_CHECK],
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")
    print(json.dumps({k: v for k, v in results.items() if k != "ellipse_secondary_analysis"}, indent=2)[:4000])


if __name__ == "__main__":
    main()
