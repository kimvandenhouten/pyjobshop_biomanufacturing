#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tabulate import tabulate  # type: ignore[import-untyped]


def main() -> int:
    parser = argparse.ArgumentParser(description="Read config.json and combine summary CSVs from a summaries folder.")
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Path to the summaries folder (e.g. summaries/summary_1759152789)",
    )
    args = parser.parse_args()

    path_to_summaries: Path = args.dir

    if not path_to_summaries.exists() or not path_to_summaries.is_dir():
        print(f"[ERROR] Folder not found or not a directory: {path_to_summaries}")
        return 1

    # 2) Read all CSVs starting with 'summary'
    csv_paths = sorted(path_to_summaries.glob("summary*.csv"))
    print(len(csv_paths))
    if not csv_paths:
        print("[WARN] No CSV files starting with 'summary' found in the folder.")
        return 0

    dfs = []
    for p in csv_paths:
        try:
            df = pd.read_csv(p)
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Skipping {p.name}: {e!r}")

    if not dfs:
        print("[WARN] No readable CSV files found.")
        return 0

    combined = pd.concat(dfs, ignore_index=True)
    combined.to_excel(path_to_summaries / "combined_summaries.xlsx", index=False)

    print(f"The length of the combined dataframe is {len(combined)}.")

    # 3) Print combined DataFrame with tabulate
    print("\n=== Combined summaries ===")
    print(tabulate(combined, headers="keys", tablefmt="pretty", showindex=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
