"""
Prepare SEPAL Classification training CSV from validated NFI LULC points.

Reads lucs_office_validated_esa_esri_ndvi.csv and writes:
  sepal_training/sepal_train.csv
  sepal_training/sepal_test.csv
  sepal_training/legend_codes.csv
  sepal_training/class_counts.csv

SEPAL TRN CSV import expects longitude, latitude, and a class value.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "lucs_office_validated_esa_esri_ndvi.csv"
OUT_DIR = ROOT / "sepal_training"

# Optional Level-1 style merges for more stable national RF mapping
MERGE_LEVEL1 = {
    "Annual Crop": "Cultivated",
    "Perennial crop": "Cultivated",
    "Natural regenerated forest": "Forest",
    "Lake": "Inland water",
    "Pond": "Inland water",
    "Raffia/Palms -": "Other woodedland",
}

# Stable integer codes (merged names included)
CLASS_CODES = {
    "Barren Land": 1,
    "Natural": 2,
    "Natural Grassland": 3,
    "Built up area": 4,
    "Wooded grassland": 5,
    "Cultivated": 6,
    "Forest": 7,
    "Other woodedland": 8,
    "Inland water": 9,
    "Annual Crop": 10,
    "Perennial crop": 11,
    "Lake": 12,
    "Pond": 13,
    "Natural regenerated forest": 14,
    "Raffia/Palms -": 15,
}


def assign_codes(labels: pd.Series) -> pd.Series:
    missing = sorted(set(labels.unique()) - set(CLASS_CODES))
    if missing:
        next_code = max(CLASS_CODES.values()) + 1
        for name in missing:
            CLASS_CODES[name] = next_code
            next_code += 1
    return labels.map(CLASS_CODES)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SEPAL training CSVs")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--test-size", type=float, default=0.30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--merge-level1",
        action="store_true",
        help="Merge rare Final LULC classes into more stable map classes",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Drop classes with fewer than this many points after merge",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required = {"lon", "lat", "final_lulc"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise SystemExit(f"Missing columns: {sorted(missing_cols)}")

    out = df[["su_no", "plot_no", "lon", "lat", "final_lulc"]].copy()
    out = out.dropna(subset=["lon", "lat", "final_lulc"])
    out["class_name"] = out["final_lulc"].astype(str).str.strip()

    if args.merge_level1:
        out["class_name"] = out["class_name"].replace(MERGE_LEVEL1)

    counts = out["class_name"].value_counts()
    rare = counts[counts < args.min_count].index.tolist()
    if rare:
        out = out[~out["class_name"].isin(rare)]

    out["class_code"] = assign_codes(out["class_name"])
    out = out.rename(columns={"lon": "longitude", "lat": "latitude"})

    # Stratified split; fall back if a class has < 2 points
    try:
        train_df, test_df = train_test_split(
            out,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=out["class_code"],
        )
    except ValueError:
        train_df, test_df = train_test_split(
            out,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=None,
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)

    sepal_cols = ["longitude", "latitude", "class_code", "class_name", "su_no", "plot_no"]
    train_df[sepal_cols].to_csv(args.out_dir / "sepal_train.csv", index=False)
    test_df[sepal_cols].to_csv(args.out_dir / "sepal_test.csv", index=False)

    legend = (
        out[["class_code", "class_name"]]
        .drop_duplicates()
        .sort_values("class_code")
        .reset_index(drop=True)
    )
    legend["n_total"] = legend["class_name"].map(out["class_name"].value_counts())
    legend["n_train"] = legend["class_name"].map(train_df["class_name"].value_counts())
    legend["n_test"] = legend["class_name"].map(test_df["class_name"].value_counts())
    legend.to_csv(args.out_dir / "legend_codes.csv", index=False)

    counts_out = (
        out["class_name"]
        .value_counts()
        .rename_axis("class_name")
        .reset_index(name="count")
    )
    counts_out["class_code"] = counts_out["class_name"].map(CLASS_CODES)
    counts_out.to_csv(args.out_dir / "class_counts.csv", index=False)

    print(f"Rows in:     {len(df)}")
    print(f"Rows used:   {len(out)}")
    print(f"Train:       {len(train_df)} -> {args.out_dir / 'sepal_train.csv'}")
    print(f"Test:        {len(test_df)} -> {args.out_dir / 'sepal_test.csv'}")
    print(f"Classes:     {legend['class_name'].tolist()}")
    print(f"Merge L1:    {args.merge_level1}")


if __name__ == "__main__":
    main()
