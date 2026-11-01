#!/usr/bin/env python
"""Read-only inspection of a PaySim CSV; writes a Markdown report only."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


EXCLUDED_FEATURES = {
    "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"
}
EXPECTED_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest",
    "isFraud", "isFlaggedFraud",
]


def inspect(csv_path: Path, chunk_size: int = 250_000) -> tuple[str, dict]:
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    header = pd.read_csv(csv_path, nrows=0).columns.tolist()
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected schema. Found: {header!r}")

    row_count = 0
    null_counts = pd.Series(0, index=header, dtype="int64")
    fraud_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    fraud_by_type: dict[str, dict[str, int]] = {}
    step_counts: dict[int, int] = {}
    steps_min = steps_max = None
    numeric_min: dict[str, float] = {}
    numeric_max: dict[str, float] = {}
    invalid_values: dict[str, int] = {}
    zero_amount = flagged_count = fraud_flagged_count = 0
    orig_prefixes: dict[str, int] = {}
    dest_prefixes: dict[str, int] = {}
    orig_unique: set[str] = set()
    dest_unique: set[str] = set()
    orig_count = dest_count = 0
    orig_repeated = dest_repeated = 0
    hash_chunks = []

    for frame in pd.read_csv(csv_path, chunksize=chunk_size):
        n = len(frame)
        row_count += n
        null_counts += frame.isna().sum()
        hash_chunks.append(pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype="uint64"))

        for key, value in frame["isFraud"].value_counts(dropna=False).items():
            fraud_counts[str(key)] = fraud_counts.get(str(key), 0) + int(value)
        for key, value in frame["type"].value_counts(dropna=False).items():
            type_counts[str(key)] = type_counts.get(str(key), 0) + int(value)
        cross = pd.crosstab(frame["type"], frame["isFraud"])
        for tx_type, row in cross.iterrows():
            entry = fraud_by_type.setdefault(str(tx_type), {})
            for label, value in row.items():
                entry[str(label)] = entry.get(str(label), 0) + int(value)

        smin, smax = int(frame["step"].min()), int(frame["step"].max())
        steps_min = smin if steps_min is None else min(steps_min, smin)
        steps_max = smax if steps_max is None else max(steps_max, smax)
        sc = frame["step"].value_counts()
        for key, value in sc.items():
            step_counts[int(key)] = step_counts.get(int(key), 0) + int(value)

        for col in ["step", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
            lo, hi = float(frame[col].min()), float(frame[col].max())
            numeric_min[col] = min(numeric_min.get(col, lo), lo)
            numeric_max[col] = max(numeric_max.get(col, hi), hi)

        invalid_values["nonbinary_isFraud"] = invalid_values.get("nonbinary_isFraud", 0) + int((~frame["isFraud"].isin([0, 1])).sum())
        invalid_values["nonbinary_isFlaggedFraud"] = invalid_values.get("nonbinary_isFlaggedFraud", 0) + int((~frame["isFlaggedFraud"].isin([0, 1])).sum())
        invalid_values["negative_amount"] = invalid_values.get("negative_amount", 0) + int((frame["amount"] < 0).sum())
        invalid_values["nonpositive_step"] = invalid_values.get("nonpositive_step", 0) + int((frame["step"] <= 0).sum())
        invalid_values["negative_balance_values"] = invalid_values.get("negative_balance_values", 0) + int((frame[["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]] < 0).any(axis=1).sum())
        zero_amount += int((frame["amount"] == 0).sum())
        flagged_count += int((frame["isFlaggedFraud"] == 1).sum())
        fraud_flagged_count += int(((frame["isFlaggedFraud"] == 1) & (frame["isFraud"] == 1)).sum())
        for col, agg in [("nameOrig", orig_prefixes), ("nameDest", dest_prefixes)]:
            prefixes = frame[col].dropna().astype(str).str[:1].value_counts()
            for key, value in prefixes.items():
                agg[str(key)] = agg.get(str(key), 0) + int(value)

        for col, seen in [("nameOrig", orig_unique), ("nameDest", dest_unique)]:
            vals = frame[col].dropna().astype(str)
            total = len(vals)
            prior_or_local_unique = len(set(vals) - seen)
            repeated = total - prior_or_local_unique
            if col == "nameOrig":
                orig_count += total
                orig_repeated += repeated
            else:
                dest_count += total
                dest_repeated += repeated
            seen.update(vals)

    fraud_hashes = np.concatenate(hash_chunks)
    duplicate_rows = int(len(fraud_hashes) - len(np.unique(fraud_hashes)))
    fraud = fraud_counts.get("1", 0)
    legitimate = fraud_counts.get("0", 0)
    fraud_pct = fraud * 100 / row_count if row_count else 0

    details = {
        "file": str(csv_path.resolve()), "size_bytes": csv_path.stat().st_size,
        "columns": header, "rows": row_count, "null_counts": null_counts.to_dict(),
        "duplicate_rows_hash_estimate": duplicate_rows, "fraud_counts": fraud_counts,
        "fraud_percent": fraud_pct, "type_counts": dict(sorted(type_counts.items())),
        "step_min": steps_min, "step_max": steps_max, "unique_steps": len(step_counts),
        "min_step_count": min(step_counts.values()), "max_step_count": max(step_counts.values()),
        "first_steps": sorted(step_counts.items())[:5], "last_steps": sorted(step_counts.items())[-5:],
        "numeric_min": numeric_min, "numeric_max": numeric_max, "invalid_values": invalid_values,
        "nameOrig_unique": len(orig_unique), "nameOrig_repeats": orig_repeated,
        "nameDest_unique": len(dest_unique), "nameDest_repeats": dest_repeated,
        "nameOrig_unique_fraction": len(orig_unique) / orig_count if orig_count else 0,
        "nameDest_unique_fraction": len(dest_unique) / dest_count if dest_count else 0,
        "fraud_by_type": fraud_by_type, "zero_amount": zero_amount,
        "flagged_count": flagged_count, "fraud_flagged_count": fraud_flagged_count,
        "orig_prefixes": orig_prefixes, "dest_prefixes": dest_prefixes,
        "missing_step_values": sorted(set(range(steps_min, steps_max + 1)) - set(step_counts)),
    }
    return header, details


def as_markdown(d: dict) -> str:
    size_mib = d["size_bytes"] / (1024 ** 2)
    lines = [
        "# PaySim CSV inspection report", "",
        "## File and schema", "",
        f"- **File:** `{d['file']}`",
        f"- **Size:** {d['size_bytes']:,} bytes ({size_mib:.2f} MiB)",
        f"- **Rows:** {d['rows']:,}",
        f"- **Columns ({len(d['columns'])}):** " + ", ".join(f"`{c}`" for c in d["columns"]),
        "- **Exact duplicate rows:** The count below is based on 64-bit row hashes; hash collisions are theoretically possible, so treat this as an extremely close duplicate count rather than a byte-for-byte proof.",
        f"- **Duplicate row count:** {d['duplicate_rows_hash_estimate']:,}",
        "", "## Missing values", "",
        "| Column | Missing |", "|---|---:|",
    ]
    lines += [f"| `{k}` | {v:,} |" for k, v in d["null_counts"].items()]
    lines += ["", "## Labels and class balance", "",
              f"- Legitimate (`isFraud=0`): {d['fraud_counts'].get('0', 0):,}",
              f"- Fraud (`isFraud=1`): {d['fraud_counts'].get('1', 0):,}",
              f"- Fraud percentage: {d['fraud_percent']:.6f}%", "",
              "## Transaction types", "", "| Type | Count |", "|---|---:|"]
    lines += [f"| `{k}` | {v:,} |" for k, v in d["type_counts"].items()]
    lines += ["", "## Step/time distribution", "",
              f"- `step` range: {d['step_min']}–{d['step_max']} ({d['unique_steps']} unique values).",
              f"- Transactions per step range: {d['min_step_count']:,}–{d['max_step_count']:,}.",
              "- First five step counts: " + ", ".join(f"{k}: {v:,}" for k, v in d["first_steps"]),
              "- Last five step counts: " + ", ".join(f"{k}: {v:,}" for k, v in d["last_steps"]),
              "- `step` is relative simulation time, not a calendar timestamp.",
              "- Missing integer steps inside the observed range: " + (", ".join(map(str, d["missing_step_values"])) if d["missing_step_values"] else "none"),
              "", "## Identifier-cardinality assessment", "",
              f"- `nameOrig`: {d['nameOrig_unique']:,} unique non-null values; {d['nameOrig_repeats']:,} occurrences beyond each identifier’s first occurrence; unique-value fraction {d['nameOrig_unique_fraction']:.2%}.",
              f"- `nameDest`: {d['nameDest_unique']:,} unique non-null values; {d['nameDest_repeats']:,} occurrences beyond each identifier’s first occurrence; unique-value fraction {d['nameDest_unique_fraction']:.2%}.",
              "- These are high-cardinality entity identifiers and are **not automatically recommended as prediction features**. They can enable memorization or leakage across random splits. Consider them for grouping, entity-history features built using past-only information, or a separately justified experiment with chronological/entity-aware validation.",
              "", "## Data checks and unexpected values", "",
              "| Check | Count |", "|---|---:|"]
    lines += [f"| {k.replace('_', ' ')} | {v:,} |" for k, v in d["invalid_values"].items()]
    lines += [f"| zero amount transactions | {d['zero_amount']:,} |",
              f"| `isFlaggedFraud=1` records | {d['flagged_count']:,} |",
              f"| both fraud and flagged | {d['fraud_flagged_count']:,} |"]
    lines += ["", "Fraud labels by transaction type:", "", "| Type | Legitimate | Fraud |", "|---|---:|---:|"]
    lines += [f"| `{k}` | {v.get('0', 0):,} | {v.get('1', 0):,} |" for k, v in sorted(d["fraud_by_type"].items())]
    lines += ["", "First-character identifier counts:", "",
              "- `nameOrig`: " + ", ".join(f"{k}: {v:,}" for k, v in sorted(d["orig_prefixes"].items())),
              "- `nameDest`: " + ", ".join(f"{k}: {v:,}" for k, v in sorted(d["dest_prefixes"].items()))]
    lines += ["", "Numeric ranges:", "", "| Column | Min | Max |", "|---|---:|---:|"]
    lines += [f"| `{k}` | {v:g} | {d['numeric_max'][k]:g} |" for k, v in d["numeric_min"].items()]
    lines += ["", "### Leakage and candidate features", "",
              "The following four post-transaction balance fields are explicitly excluded from candidate prediction features: `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, and `newbalanceDest`. In particular, new balances directly describe state after processing, and balance fields can expose simulator mechanics/outcomes. They may be retained only for data-quality/accounting analysis, not as predictors in the planned pre-transaction task.",
              "", "`isFlaggedFraud` is a rule/flag field and should also be excluded as a predictor when predicting `isFraud`.",
              "", "## Reproducibility", "",
              "Run from the project root: `python scripts/inspect_paysim.py [path-to-csv]`. The script reads the source CSV and writes this Markdown report; it does not alter the CSV or train a model.",
              ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="?", type=Path, default=Path("data/raw/PS_20174392719_1491204439457_log.csv"))
    parser.add_argument("--chunk-size", type=int, default=250_000)
    args = parser.parse_args()
    _, result = inspect(args.csv, args.chunk_size)
    report = as_markdown(result)
    out = Path("docs/dataset_inspection.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport written to {out.resolve()}")


if __name__ == "__main__":
    main()
