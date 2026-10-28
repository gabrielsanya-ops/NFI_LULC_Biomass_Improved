"""Tree and shrub formulas from NFI_ KSA Calculation_Trees&shrubs.docx.

Constants and equations are taken from docs/_calc_doc_extract.md (document extract).
Carbon outputs are labeled provisional. National stock totals require design weights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Calculation document constants
FORM_FACTOR = 0.65  # FRA report Saudi Arabia 2015
WOOD_DENSITY = 0.6  # FRA report Saudi Arabia 2015
BEF = 2.0  # IPCC biomass expansion factor
ROOT_SHOOT = 0.28  # FRA 2020 naturally regenerated tropical dry forest
CARBON_FRACTION = 0.47  # FRA 2020
CO2EQ_FACTOR = 3.67
CONVERSION_FACTOR_HA = 10  # plot 1000 m2 = 0.1 ha
PLOT_AREA_M2 = 1000.0

# Shrub allometric coefficients (document section 8.4)
SHRUB_A = -0.37
SHRUB_B_CD = 1.903
SHRUB_B_H = 0.652
SHRUB_INTERCEPT_ADD = 1.403
SHRUB_SCALE = 1000.0

TREE_EXCLUDE_SUBSTRINGS = ("calotropis", "palm", "grass")
SHRUB_EXCLUDE_SUBSTRINGS = ("grass",)


def basal_area_m2(dbh_cm):
    """Basal Area (m2) = (pi * DBH^2) / 40000. DBH in cm."""
    dbh = np.asarray(dbh_cm, dtype=float)
    return (np.pi * dbh**2) / 40000.0


def tree_volume_m3(dbh_cm, height_m, form_factor: float = FORM_FACTOR):
    """Tree volume (m3) = BA * height * form factor."""
    return basal_area_m2(dbh_cm) * np.asarray(height_m, dtype=float) * form_factor


def tree_agb_mg(dbh_cm, height_m, wood_density: float = WOOD_DENSITY, bef: float = BEF, form_factor: float = FORM_FACTOR):
    """AGB (Mg) = volume * wood density * BEF."""
    return tree_volume_m3(dbh_cm, height_m, form_factor) * wood_density * bef


def tree_bgb_mg(agb_mg, root_shoot: float = ROOT_SHOOT):
    """BGB (Mg) = AGB * root:shoot."""
    return np.asarray(agb_mg, dtype=float) * root_shoot


def total_biomass_mg(agb_mg, bgb_mg):
    """Implied Total biomass = AGB + BGB (used by carbon formula; not written explicitly)."""
    return np.asarray(agb_mg, dtype=float) + np.asarray(bgb_mg, dtype=float)


def carbon_mg(total_biomass, carbon_fraction: float = CARBON_FRACTION):
    """Carbon (Mg) = Total biomass * 0.47."""
    return np.asarray(total_biomass, dtype=float) * carbon_fraction


def co2eq_mg(carbon, factor: float = CO2EQ_FACTOR):
    """CO2 equivalent (Mg) = Carbon * 3.67."""
    return np.asarray(carbon, dtype=float) * factor


def exclude_by_substrings(series: pd.Series, substrings) -> pd.Series:
    """True = keep row. Case-insensitive substring exclusion."""
    s = series.astype(str).str.lower()
    keep = pd.Series(True, index=series.index)
    for sub in substrings:
        keep &= ~s.str.contains(str(sub).lower(), na=False)
    return keep


def apply_tree_metrics(df: pd.DataFrame, dbh_col: str, height_col: str) -> pd.DataFrame:
    out = df.copy()
    dbh = pd.to_numeric(out[dbh_col], errors="coerce")
    ht = pd.to_numeric(out[height_col], errors="coerce")
    out["basal_area_m2"] = basal_area_m2(dbh)
    out["volume_m3"] = tree_volume_m3(dbh, ht)
    out["agb_mg"] = tree_agb_mg(dbh, ht)
    out["bgb_mg"] = tree_bgb_mg(out["agb_mg"])
    out["total_biomass_mg"] = total_biomass_mg(out["agb_mg"], out["bgb_mg"])
    out["carbon_mg_provisional"] = carbon_mg(out["total_biomass_mg"])
    out["co2eq_mg_provisional"] = co2eq_mg(out["carbon_mg_provisional"])
    return out


def shrub_agb_mg(mean_cd_m, height_cm):
    """Document shrub AGB equation (natural log assumed; marked in open questions).

    AGB = (exp(-0.37 + 1.903*log(CD) + 0.652*log(H)) + 1.403) / 1000
    CD in m, H in cm. Labeled Mg/ha in source; applied per shrub record here.
    """
    cd = np.asarray(mean_cd_m, dtype=float)
    h = np.asarray(height_cm, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = np.exp(SHRUB_A + SHRUB_B_CD * np.log(cd) + SHRUB_B_H * np.log(h)) + SHRUB_INTERCEPT_ADD
    return raw / SHRUB_SCALE
