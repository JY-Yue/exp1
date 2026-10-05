"""
csv_to_jspsych_lists.py

Reads a trials spreadsheet with columns:
    List, Trial, Item_name, Condition, Subtitle
and generates the `const lists = [...]` JavaScript block used by the
jsPsych experiment HTML file. Paste the printed output (or the contents
of the .js file this writes) directly over the existing `const lists = [...]`
block in your HTML file.

Usage:
    python csv_to_jspsych_lists.py trials.csv
    python csv_to_jspsych_lists.py trials.csv --output lists_output.js
"""

import argparse
import json
import sys

import pandas as pd

REQUIRED_COLUMNS = {"List", "Trial", "Item_name", "Condition", "Subtitle"}


def build_lists_js(csv_path: str) -> str:
    df = pd.read_csv(csv_path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required column(s): {sorted(missing)}")

    # Sort so trials come out in the right order within each list, and lists
    # come out in a stable, predictable order (list 0 first, etc.)
    df = df.sort_values(["List", "Trial"])

    list_lines = []
    for list_id, group in df.groupby("List", sort=True):
        group = group.sort_values("Trial")

        trial_entries = []
        for _, row in group.iterrows():
            item_name = str(row["Item_name"]).strip()
            condition = str(row["Condition"]).strip()
            # Blank/missing subtitle becomes "" here; the HTML file's
            # build_trial() falls back to its own placeholder text for
            # any subtitle that's empty, so this is safe either way.
            subtitle = "" if pd.isna(row["Subtitle"]) else str(row["Subtitle"]).strip()

            # json.dumps produces a valid JS array literal and handles
            # quote/apostrophe escaping in subtitles correctly.
            trial_entries.append(json.dumps([item_name, condition, subtitle]))

        list_lines.append(f"  [ {', \n'.join(trial_entries)} ], // List {list_id}")

    js_code = "const lists = [\n" + "\n".join(list_lines) + "\n];"
    return js_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="Path to your trials CSV file")
    parser.add_argument(
        "--output", "-o",
        default="lists_output.js",
        help="Where to write the generated JS (default: lists_output.js)"
    )
    args = parser.parse_args()

    try:
        js_code = build_lists_js(args.csv_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(js_code)

    print(js_code)
    print(f"\n--- Also written to {args.output} ---")


if __name__ == "__main__":
    main()
