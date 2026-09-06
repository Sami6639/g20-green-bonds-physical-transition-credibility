"""Reproduce the exploratory exposure diagnostics in manuscript Table S6.

Run after code/01_build_panel.py. This supplement leaves the locked main
analysis unchanged. Only aggregate estimates and verification metadata are
written; provider-level observations and the analytical panel remain local.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/derived/analytical_panel_2006_2024.csv"


def slope(frame: pd.DataFrame, exposure: str) -> float:
    """OLS with an intercept and explicit country/year indicators."""
    design = np.column_stack([
        frame[exposure].to_numpy(dtype=float),
        np.ones(len(frame)),
        pd.get_dummies(frame["iso3"], drop_first=True, dtype=float).to_numpy(),
        pd.get_dummies(frame["year"], drop_first=True, dtype=float).to_numpy(),
    ])
    outcome = frame["fossil_contraction"].to_numpy(dtype=float)
    return float(np.linalg.lstsq(design, outcome, rcond=None)[0][0])


def fit(frame: pd.DataFrame, exposure: str, label: str, scale: float) -> dict:
    """Retain the small-sample-adjusted CRV3 scaling of PyFixest 0.60.0.

    The unscaled covariance is the sum of squared deviations of each
    leave-country-out slope from the full-sample slope. Multiply by
    G/(G-1) and (N-1)/(N-K), with K = year levels + one slope. Country
    effects are nested in country clusters. This is the retained software
    convention, rather than the unadjusted (G-1)/G jackknife scaling.
    """
    countries = sorted(frame["iso3"].unique())
    n, groups = len(frame), len(countries)
    coefficient = slope(frame, exposure)
    deleted = np.array([
        slope(frame.loc[frame["iso3"].ne(country)], exposure)
        for country in countries
    ])
    parameters = int(frame["year"].nunique()) + 1
    correction = groups / (groups - 1) * (n - 1) / (n - parameters)
    standard_error = float(np.sqrt(correction * np.sum((deleted - coefficient) ** 2)))
    critical = float(t.ppf(0.975, groups - 1))
    low, high = coefficient - critical * standard_error, coefficient + critical * standard_error
    return {
        "diagnostic": label,
        "exposure": exposure,
        "effect_unit": "One asinh unit" if scale == 100 else "10 basis points",
        "n": n,
        "clusters": groups,
        "coefficient": coefficient,
        "standard_error_crv3": standard_error,
        "df": groups - 1,
        "ci_low": low,
        "ci_high": high,
        "p_value": float(2 * t.sf(abs(coefficient / standard_error), groups - 1)),
        "effect_pp": scale * coefficient,
        "ci_low_pp": scale * low,
        "ci_high_pp": scale * high,
    }


def main() -> None:
    frame = pd.read_csv(PANEL)
    columns = ["iso3", "year", "issuance_bp_gdp", "fossil_contraction"]
    if frame[columns].isna().any().any() or frame.duplicated(["iso3", "year"]).any():
        raise ValueError("Missing values or duplicate country-year keys")
    if len(frame) != 361 or frame["iso3"].nunique() != 19:
        raise ValueError("Expected the locked 361-observation, 19-country panel")
    if set(frame["year"]) != set(range(2006, 2025)):
        raise ValueError("Unexpected analysis period")
    if frame["issuance_bp_gdp"].lt(0).any() or not frame["fossil_contraction"].isin([0, 1]).all():
        raise ValueError("Invalid exposure or binary outcome")
    frame = frame[columns].sort_values(["iso3", "year"]).reset_index(drop=True)
    cutoff = float(frame["issuance_bp_gdp"].quantile(0.99, interpolation="linear"))
    frame["issuance_asinh"] = np.arcsinh(frame["issuance_bp_gdp"])
    frame["issuance_winsor99"] = frame["issuance_bp_gdp"].clip(upper=cutoff)
    top_five = frame.sort_values(
        ["issuance_bp_gdp", "iso3", "year"],
        ascending=[False, True, True], kind="mergesort",
    ).head(5).index
    rows = [
        fit(frame, "issuance_bp_gdp", "Baseline", 1000),
        fit(frame, "issuance_asinh", "Inverse-hyperbolic-sine exposure", 100),
        fit(frame, "issuance_winsor99", "Upper-tail winsorized at 99th percentile", 1000),
        fit(frame.loc[frame["issuance_bp_gdp"].le(cutoff)], "issuance_bp_gdp", "Upper 1% trimmed", 1000),
        fit(frame.drop(top_five), "issuance_bp_gdp", "Five largest observations removed", 1000),
    ]
    results = pd.DataFrame(rows)
    # Independent target: the retained, published manuscript table.
    expected = [
        (361, -1.56, -3.53, 0.42, 0.115),
        (361, -1.15, -7.88, 5.57, 0.723),
        (361, -1.57, -4.15, 1.01, 0.217),
        (357, -0.35, -3.26, 2.56, 0.803),
        (356, 0.08, -3.49, 3.65, 0.964),
    ]
    observed = [
        (int(row["n"]), round(row["effect_pp"], 2), round(row["ci_low_pp"], 2),
         round(row["ci_high_pp"], 2), round(row["p_value"], 3))
        for row in rows
    ]
    if observed != expected:
        raise AssertionError(f"Table S6 mismatch: {observed}")
    for directory in ["results", "tables", "verification"]:
        (ROOT / directory).mkdir(exist_ok=True)
    results_path = ROOT / "results/exposure_diagnostics.csv"
    table_path = ROOT / "tables/table_s6_exposure_diagnostics.csv"
    results.to_csv(results_path, index=False)
    table = results[["diagnostic", "effect_unit", "n", "effect_pp", "ci_low_pp", "ci_high_pp", "p_value"]].copy()
    table.to_csv(table_path, index=False, float_format="%.12g")
    manifest = {
        "status": "TABLE S6 VERIFIED",
        "scope": "Exploratory diagnostics; no change to the locked main analysis",
        "estimator": "Country/year OLS; retained PyFixest 0.60.0 small-sample-adjusted CRV3 convention",
        "ssc": {"k_adj": True, "G_adj": True, "k_fixef": "nonnested", "G_df": "min"},
        "reference_distribution": "t(G-1)",
        "percentile": 0.99,
        "quantile_interpolation": "linear",
        "transform": "asinh(issuance in basis points of GDP)",
        "comparison": "All five rows match manuscript Table S6 at reported precision",
        "files": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__), results_path, table_path]
        },
    }
    (ROOT / "verification/s6_diagnostics_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(table.to_string(index=False))
    print("TABLE S6 VERIFIED")


if __name__ == "__main__":
    main()
