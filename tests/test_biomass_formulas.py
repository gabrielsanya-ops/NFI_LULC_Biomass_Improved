"""Unit tests against calculation-document constants (docs/_calc_doc_extract.md)."""

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfi_improved.biomass import (  # noqa: E402
    BEF,
    CARBON_FRACTION,
    CO2EQ_FACTOR,
    FORM_FACTOR,
    ROOT_SHOOT,
    WOOD_DENSITY,
    basal_area_m2,
    carbon_mg,
    co2eq_mg,
    shrub_agb_mg,
    total_biomass_mg,
    tree_agb_mg,
    tree_bgb_mg,
    tree_volume_m3,
)


def test_constants_match_calc_doc():
    assert FORM_FACTOR == 0.65
    assert WOOD_DENSITY == 0.6
    assert BEF == 2.0
    assert ROOT_SHOOT == 0.28
    assert CARBON_FRACTION == 0.47
    assert CO2EQ_FACTOR == 3.67


def test_basal_area_10cm():
    # BA = pi * 100 / 40000
    expected = (math.pi * 100.0) / 40000.0
    assert abs(float(basal_area_m2(10.0)) - expected) < 1e-12


def test_volume_and_carbon_chain():
    dbh, ht = 20.0, 10.0
    ba = basal_area_m2(dbh)
    vol = tree_volume_m3(dbh, ht)
    assert abs(vol - ba * ht * FORM_FACTOR) < 1e-12
    agb = tree_agb_mg(dbh, ht)
    assert abs(agb - vol * WOOD_DENSITY * BEF) < 1e-12
    bgb = tree_bgb_mg(agb)
    assert abs(bgb - agb * ROOT_SHOOT) < 1e-12
    tot = total_biomass_mg(agb, bgb)
    c = carbon_mg(tot)
    assert abs(c - tot * CARBON_FRACTION) < 1e-12
    assert abs(co2eq_mg(c) - c * CO2EQ_FACTOR) < 1e-12


def test_shrub_agb_positive():
    val = float(shrub_agb_mg(1.0, 100.0))
    assert np.isfinite(val) and val > 0
