from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
RESULTS = ROOT / "results"
VERIFY = ROOT / "verification"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    panel = pd.read_csv(DERIVED / "analytical_panel_2006_2024.csv")
    main_models = pd.read_csv(RESULTS / "main_models.csv")
    robustness = pd.read_csv(RESULTS / "robustness_models.csv")
    thresholds = pd.read_csv(RESULTS / "threshold_models_all_outcomes.csv")
    loco = pd.read_csv(RESULTS / "loco_all_outcomes.csv")
    bootstrap = pd.read_csv(RESULTS / "descriptive_cluster_bootstrap.csv")

    checks: dict[str, object] = {}
    checks["panel_dimensions"] = len(panel) == 361 and panel["iso3"].nunique() == 19 and panel["year"].nunique() == 19
    checks["panel_unique"] = not panel.duplicated(["iso3", "year"]).any()
    checks["primary_complete"] = panel["fossil_contraction"].notna().all()
    checks["finance_complete"] = panel["issuance_bp_gdp"].notna().all()
    checks["coal_eligibility"] = int(panel["coal_eligible"].sum()) == 342
    checks["unoffset_subset"] = bool(
        (panel.loc[panel["unoffset_coal_contraction"].eq(1), "coal_contraction"].eq(1)).all()
    )

    for prefix in ["renewable_addition", "fossil_contraction", "coal_contraction", "unoffset_coal_contraction"]:
        strict = panel[f"{prefix}_strict"].sum(skipna=True)
        m010 = panel[f"{prefix}_m010"].sum(skipna=True)
        m025 = panel[f"{prefix}_m025"].sum(skipna=True)
        checks[f"threshold_monotonic_{prefix}"] = bool(strict >= m010 >= m025)

    recalculated_intensity = 10_000 * panel["issuance_usd"] / panel["gdp_current_usd"]
    checks["finance_formula"] = bool(np.allclose(panel["issuance_bp_gdp"], recalculated_intensity, rtol=1e-12, atol=1e-12))
    checks["main_model_rows"] = len(main_models) == 4 and set(main_models["outcome"]) == {
        "fossil_contraction",
        "renewable_addition",
        "coal_contraction",
        "unoffset_coal_contraction",
    }
    checks["primary_wild_bootstrap"] = bool(
        main_models.loc[main_models["outcome"].eq("fossil_contraction"), "wild_p_value"].notna().all()
    )
    checks["robustness_rows"] = len(robustness) == 7
    checks["threshold_model_rows"] = len(thresholds) == 8
    checks["loco_rows"] = len(loco) == 76
    checks["bootstrap_complete"] = bool(bootstrap[["point_estimate", "ci_low", "ci_high"]].notna().all().all())
    checks["bootstrap_ordered"] = bool(
        (bootstrap["ci_low"] <= bootstrap["point_estimate"]).all()
        and (bootstrap["point_estimate"] <= bootstrap["ci_high"]).all()
    )
    checks["primary_loco_sign_stable"] = bool(
        (loco.loc[loco["outcome"].eq("fossil_contraction"), "coefficient"] < 0).all()
    )
    checks["primary_threshold_sign_stable"] = bool(
        (robustness.loc[robustness["specification"].str.contains("materiality"), "coefficient"] < 0).all()
    )

    required = [key for key, value in checks.items() if isinstance(value, (bool, np.bool_))]
    checks["all_checks_pass"] = bool(all(bool(checks[key]) for key in required))
    checks["decision"] = "VERIFICATION PASS" if checks["all_checks_pass"] else "VERIFICATION FAIL"
    checks["derived_csv_sha256"] = sha256(DERIVED / "analytical_panel_2006_2024.csv")
    checks["result_files"] = {
        path.name: sha256(path) for path in sorted(RESULTS.glob("*.csv"))
    }
    (VERIFY / "verification_report.json").write_text(
        json.dumps(
            checks,
            indent=2,
            sort_keys=True,
            default=lambda value: value.item() if isinstance(value, np.generic) else str(value),
        )
        + "\n"
    )
    print(checks["decision"])
    if not checks["all_checks_pass"]:
        failed = [key for key in required if not checks[key]]
        print("Failed checks:", failed)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
