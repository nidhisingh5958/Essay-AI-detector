import pandas as pd

from extract_prompts import extract_prompt_records


def test_extract_prompt_records_groups_and_summarizes():
    df = pd.DataFrame(
        {
            "prompt_name": ["Cats", "Cats", "Dogs"],
            "assignment": ["Write about cats.", "Write about cats.", "Write about dogs."],
            "task": ["Independent", "Independent", "Independent"],
            "full_text": ["one two three four five", "one two three", "one two"],
        }
    )
    records = extract_prompt_records(df)
    by_id = {r["prompt_id"]: r for r in records}

    assert set(by_id.keys()) == {"Cats", "Dogs"}
    assert by_id["Cats"]["essay_count"] == 2
    assert by_id["Cats"]["prompt_text"] == "Write about cats."
    assert by_id["Cats"]["prompt_text_is_consistent"] is True
    assert by_id["Dogs"]["essay_count"] == 1
    assert by_id["Cats"]["length_stats_words"]["min"] == 3
    assert by_id["Cats"]["length_stats_words"]["max"] == 5


def test_extract_prompt_records_flags_inconsistent_assignment_text():
    df = pd.DataFrame(
        {
            "prompt_name": ["Cats", "Cats"],
            "assignment": ["Write about cats.", "Write about kittens."],
            "task": ["Independent", "Independent"],
            "full_text": ["one two three", "four five six"],
        }
    )
    records = extract_prompt_records(df)
    assert records[0]["prompt_text_is_consistent"] is False
