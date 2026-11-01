#!/usr/bin/env python
"""Report or optionally materialize the approved chronological PaySim split.

No model is trained and the raw CSV is never modified. By default this script
prints split counts only. Pass --write-splits to write feature-only CSV files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path("data/raw/PS_20174392719_1491204439457_log.csv")
FEATURES = ["step", "type", "amount"]
TARGET = "isFraud"
KEEP = FEATURES + [TARGET]
SPLITS = [("train", 1, 322), ("validation", 323, 377), ("test", 378, 743)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--write-splits", action="store_true", help="write feature/target-only CSVs under data/processed")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    if not args.csv.is_file():
        raise FileNotFoundError(args.csv)

    total_rows = 0
    summaries = {name: {"rows": 0, "fraud": 0} for name, _, _ in SPLITS}
    writers = {}
    try:
        if args.write_splits:
            args.output_dir.mkdir(parents=True, exist_ok=True)
        for frame in pd.read_csv(args.csv, usecols=["step", *KEEP], chunksize=250_000):
            total_rows += len(frame)
            for name, low, high in SPLITS:
                part = frame.loc[frame["step"].between(low, high), KEEP]
                if part.empty:
                    continue
                summaries[name]["rows"] += len(part)
                summaries[name]["fraud"] += int(part[TARGET].sum())
                if args.write_splits:
                    path = args.output_dir / f"paysim_{name}.csv"
                    if name not in writers:
                        writers[name] = path.open("w", encoding="utf-8", newline="")
                        part.to_csv(writers[name], index=False, header=True)
                    else:
                        part.to_csv(writers[name], index=False, header=False)
    finally:
        for handle in writers.values():
            handle.close()

    print(f"Input: {args.csv.resolve()}")
    print(f"Rows: {total_rows:,}; features: {', '.join(FEATURES)}; target: {TARGET}")
    print("Excluded: nameOrig, nameDest, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, isFlaggedFraud")
    print("Split | inclusive step range | rows | legitimate | fraud | fraud %")
    for name, low, high in SPLITS:
        n = summaries[name]["rows"]
        fraud = summaries[name]["fraud"]
        legit = n - fraud
        pct = 100 * fraud / n if n else 0.0
        print(f"{name} | {low}-{high} | {n:,} | {legit:,} | {fraud:,} | {pct:.6f}%")
    if args.write_splits:
        print(f"Feature/target-only split files written to: {args.output_dir.resolve()}")
    else:
        print("No derived split files written. Pass --write-splits to materialize them.")


if __name__ == "__main__":
    main()
