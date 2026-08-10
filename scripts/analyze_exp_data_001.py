"""
Analysis pass over EXP-DATA-001's raw output (samples.jsonl, diffs.json).
Produces the statistics reports/EXP-DATA-001.md is built from. Kept
separate from run_exp_data_001.py so re-analyzing doesn't require
re-generating (and, per this experiment's explicit instructions, so a
methodology flaw found here gets documented and fixed in code, not
patched by silently regenerating until the numbers look better).
"""

import json
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generation_utils import near_duplicate_pairs  # noqa: E402


def load():
    records = [json.loads(l) for l in open(OUTPUT_DIR / "samples.jsonl")]
    diffs = json.loads((OUTPUT_DIR / "diffs.json").read_text())
    return records, diffs


def qc_counts(records):
    from collections import Counter

    by_cat = {}
    for r in records:
        by_cat.setdefault(r["transformation_type"], Counter())[r["qc_status"]] += 1
    return {cat: dict(counts) for cat, counts in by_cat.items()}


def length_stats(records):
    from collections import defaultdict

    by_cat = defaultdict(list)
    for r in records:
        if r["actual_length_words"]:
            by_cat[r["transformation_type"]].append(
                {"target": r["target_length_words"], "actual": r["actual_length_words"]}
            )
    out = {}
    for cat, vals in by_cat.items():
        actuals = [v["actual"] for v in vals]
        out[cat] = {
            "n": len(actuals),
            "min": min(actuals),
            "median": statistics.median(actuals),
            "max": max(actuals),
        }
    return out


def corrected_prompt_leakage_check(records):
    """Re-check prompt_leakage excluding the prompt_text portion of the
    instruction, since the pilot found the original check flags essays
    for legitimately echoing the *topic* they were asked to write about,
    not the instructional wrapper. Only applies to full_ai (the only
    category whose instruction embeds prompt_text)."""
    import pandas as pd

    df = pd.read_csv(
        REPO_ROOT / "data" / "raw" / "persuade_2.0" / "persuade_2.0_human_scores_demo_id_github.csv",
        dtype={"essay_id_comp": str},
    )
    assignments = dict(zip(df["essay_id_comp"], df["assignment"]))

    from generation_utils import check_prompt_leakage

    META_WRAPPER = (
        "Write a {task_type_desc} essay of approximately {target_words} words responding to the "
        "following prompt. Write in the voice of a student. Return only the essay, with no preamble "
        "or title.\n\nPrompt: "
    )

    results = {}
    for r in records:
        if r["transformation_type"] != "full_ai":
            continue
        family_id = r["family_id"]
        target_words = r["target_length_words"]
        meta_only = META_WRAPPER.format(task_type_desc="persuasive/argumentative", target_words=target_words)
        flagged_meta_only = check_prompt_leakage(meta_only, r["text"])
        flagged_original = "prompt_leakage" in r["qc_notes"]
        results[r["sample_id"]] = {
            "original_check_flagged": flagged_original,
            "corrected_check_flagged": flagged_meta_only,
        }
    return results


def diff_similarity_distribution(diffs):
    out = {}
    for category, entries in diffs.items():
        all_ratios = []
        n_structure_drift = 0
        n_aligned = 0
        for entry in entries:
            if entry["structure_drift"]:
                n_structure_drift += 1
                continue
            n_aligned += 1
            for _, _, ratio in entry["pairs"]:
                all_ratios.append(ratio)
        out[category] = {
            "n_families": len(entries),
            "n_structure_drift": n_structure_drift,
            "n_aligned": n_aligned,
            "n_sentence_pairs": len(all_ratios),
            "ratios": sorted(all_ratios),
        }
    return out


def main():
    records, diffs = load()

    print("=== QC status by category ===")
    print(json.dumps(qc_counts(records), indent=2))

    print("\n=== Length stats by category (words) ===")
    print(json.dumps(length_stats(records), indent=2))

    print("\n=== Corrected prompt_leakage re-check (full_ai) ===")
    corrected = corrected_prompt_leakage_check(records)
    print(json.dumps(corrected, indent=2))

    print("\n=== Diff similarity distribution (light/moderate polish) ===")
    dist = diff_similarity_distribution(diffs)
    for cat, d in dist.items():
        print(cat, {k: v for k, v in d.items() if k != "ratios"})
        if d["ratios"]:
            print("  ratios:", [round(r, 2) for r in d["ratios"]])

    print("\n=== Near-duplicate check across full_ai texts ===")
    full_ai_texts = [r["text"] for r in records if r["transformation_type"] == "full_ai"]
    full_ai_ids = [r["sample_id"] for r in records if r["transformation_type"] == "full_ai"]
    pairs = near_duplicate_pairs(full_ai_texts)
    print([(full_ai_ids[i], full_ai_ids[j]) for i, j in pairs])

    print("\n=== Near-duplicate check across ALL generated (non-human) texts ===")
    gen_texts = [r["text"] for r in records if r["label"] != "human" and r["text"]]
    gen_ids = [r["sample_id"] for r in records if r["label"] != "human" and r["text"]]
    pairs = near_duplicate_pairs(gen_texts)
    print([(gen_ids[i], gen_ids[j]) for i, j in pairs])


if __name__ == "__main__":
    main()
