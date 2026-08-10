"""
Extract prompt metadata from the acquired PERSUADE 2.0 essay-level file.

Per generation-methodology.md Section 2: prompts are extracted from the
corpus's own metadata, not hand-authored ahead of time. This script reads
the real corpus file and writes one JSON record per prompt.

Usage:
    python extract_prompts.py
"""

import json
from pathlib import Path

import pandas as pd

PERSUADE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "persuade_2.0"
    / "persuade_2.0_human_scores_demo_id_github.csv"
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "prompts" / "persuade_2.0"


def extract_prompt_records(df: pd.DataFrame) -> list[dict]:
    """Group essays by prompt_name and summarize each prompt. Pure
    function of a dataframe with the expected PERSUADE columns, so it's
    testable against a small synthetic dataframe."""
    records = []
    for prompt_name, group in df.groupby("prompt_name"):
        assignments = group["assignment"].unique()
        word_counts = group["full_text"].apply(lambda t: len(str(t).split()))
        records.append(
            {
                "prompt_id": prompt_name,
                "prompt_text": assignments[0] if len(assignments) else None,
                "prompt_text_is_consistent": len(assignments) == 1,
                "task_type": group["task"].mode().iat[0] if not group["task"].mode().empty else None,
                "essay_count": int(len(group)),
                "length_stats_words": {
                    "min": int(word_counts.min()),
                    "median": float(word_counts.median()),
                    "p10": float(word_counts.quantile(0.10)),
                    "p90": float(word_counts.quantile(0.90)),
                    "max": int(word_counts.max()),
                },
            }
        )
    return records


def main() -> None:
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    records = extract_prompt_records(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for record in records:
        safe_name = "".join(c if c.isalnum() else "_" for c in record["prompt_id"]).strip("_")
        (OUTPUT_DIR / f"{safe_name}.json").write_text(json.dumps(record, indent=2))

    print(f"Wrote {len(records)} prompt files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
