"""Helpers that preserve the LULC Validation baseline join keys and summaries."""

from __future__ import annotations

import pandas as pd


def find_col(df: pd.DataFrame, candidates):
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    for c in df.columns:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None


def plot_uid(su, plot_no) -> pd.Series:
    return su.astype(str).str.strip() + "-" + plot_no.astype(str).str.strip()


def lulc_validation_summary(lulc: pd.DataFrame) -> dict:
    """Recompute baseline-style acceptance counts from the validated table."""
    vt = find_col(lulc, ["validation_true"])
    forest = find_col(lulc, ["inside_forest_reserved"])
    final_col = find_col(lulc, ["final_lulc", "New LCU"])
    n = int(len(lulc))
    accepted = int(lulc[vt].sum()) if vt else None
    n_forest = int(lulc[forest].sum()) if forest else None
    out = {
        "n_rows": n,
        "accepted_true": accepted,
        "updated_false": (n - accepted) if accepted is not None else None,
        "accepted_pct": round(100.0 * accepted / n, 1) if accepted and n else None,
        "inside_forest_reserved": n_forest,
        "n_final_lulc_classes": int(lulc[final_col].nunique()) if final_col else None,
        "baseline": "10.LULC_Validation",
    }
    return out


def land_use_proportion_by_su(lulc: pd.DataFrame, su_col: str, class_col: str, plots_per_su: int = 5) -> pd.DataFrame:
    """Word calc section 5: Land Use Proportion = n plots of class / 5."""
    d = lulc[[su_col, class_col]].copy()
    d[su_col] = d[su_col].astype(str).str.strip()
    # one row per plot preferred: if multiple LUCS segments, take first final_lulc per plot if plot present
    counts = d.groupby([su_col, class_col], dropna=False).size().rename("n_plots").reset_index()
    counts["land_use_proportion"] = counts["n_plots"] / float(plots_per_su)
    return counts
