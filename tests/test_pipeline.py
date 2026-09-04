from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_preflight_passes() -> None:
    report = json.loads((ROOT / "verification" / "preflight_report.json").read_text())
    assert report["baseline_pass"] is True


def test_panel_contract() -> None:
    panel = pd.read_csv(ROOT / "data" / "derived" / "analytical_panel_2006_2024.csv")
    assert panel.shape[0] == 361
    assert panel["iso3"].nunique() == 19
    assert not panel.duplicated(["iso3", "year"]).any()
    assert panel["fossil_contraction"].notna().all()
    assert int(panel["coal_eligible"].sum()) == 342


def test_physical_state_invariants() -> None:
    panel = pd.read_csv(ROOT / "data" / "derived" / "analytical_panel_2006_2024.csv")
    assert panel.loc[panel["unoffset_coal_contraction"].eq(1), "coal_contraction"].eq(1).all()
    for outcome in ["renewable_addition", "fossil_contraction", "coal_contraction", "unoffset_coal_contraction"]:
        assert panel[f"{outcome}_strict"].sum(skipna=True) >= panel[f"{outcome}_m010"].sum(skipna=True)
        assert panel[f"{outcome}_m010"].sum(skipna=True) >= panel[f"{outcome}_m025"].sum(skipna=True)


def test_verification_passes() -> None:
    report = json.loads((ROOT / "verification" / "verification_report.json").read_text())
    assert report["all_checks_pass"] is True
