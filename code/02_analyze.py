from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats
from statsmodels.stats.multitest import multipletests


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "derived" / "analytical_panel_2006_2024.csv"
RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"
VERIFY = ROOT / "verification"
CONFIG = json.loads((ROOT / "config" / "analysis_config.json").read_text())
SEED = int(CONFIG["project_seed"])

OUTCOMES = [
    "fossil_contraction",
    "renewable_addition",
    "coal_contraction",
    "unoffset_coal_contraction",
]
OUTCOME_LABELS = {
    "fossil_contraction": "Fossil contraction",
    "renewable_addition": "Renewable addition",
    "coal_contraction": "Coal contraction",
    "unoffset_coal_contraction": "Unoffset coal contraction",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fit_model(
    frame: pd.DataFrame,
    outcome: str,
    exposure: str,
    specification: str,
    run_wild: bool = False,
) -> dict[str, object]:
    columns = [outcome, exposure, "iso3", "year", "cluster_id"]
    use = frame[columns].dropna().copy()
    clusters = int(use["cluster_id"].nunique())
    model = pf.feols(
        f"{outcome} ~ {exposure} | iso3 + year",
        data=use,
        vcov={"CRV3": "cluster_id"},
    )
    coefficient = float(model.coef().loc[exposure])
    standard_error = float(model.se().loc[exposure])
    t_value = coefficient / standard_error
    degrees_freedom = clusters - 1
    critical = stats.t.ppf(0.975, degrees_freedom)
    p_value = float(2 * stats.t.sf(abs(t_value), degrees_freedom))
    result: dict[str, object] = {
        "specification": specification,
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
        "exposure": exposure,
        "n": len(use),
        "clusters": clusters,
        "coefficient": coefficient,
        "standard_error_crv3": standard_error,
        "t_value": t_value,
        "df": degrees_freedom,
        "p_value_t_g_minus_1": p_value,
        "ci_low": coefficient - critical * standard_error,
        "ci_high": coefficient + critical * standard_error,
        "outcome_mean": float(use[outcome].mean()),
        "exposure_mean": float(use[exposure].mean()),
        "wild_bootstrap_type": "",
        "wild_weights": "",
        "wild_reps": np.nan,
        "wild_p_value": np.nan,
    }
    if run_wild:
        boot = model.wildboottest(
            reps=int(CONFIG["wild_cluster_bootstrap_replications"]),
            cluster="cluster_id",
            param=exposure,
            weights_type="webb",
            impose_null=True,
            bootstrap_type="33",
            seed=SEED,
        )
        result["wild_bootstrap_type"] = str(boot["bootstrap_type"])
        result["wild_weights"] = "webb"
        result["wild_reps"] = int(CONFIG["wild_cluster_bootstrap_replications"])
        result["wild_p_value"] = float(boot["Pr(>|t|)"])
    return result


def descriptive_outputs(panel: pd.DataFrame) -> None:
    summary = pd.DataFrame(
        [
            ("Country-years", len(panel)),
            ("Countries", panel["iso3"].nunique()),
            ("Years", panel["year"].nunique()),
            ("Positive recorded issuance country-years", panel["recorded_positive_issuance"].sum()),
            ("No-recorded-issuance country-years", panel["recorded_positive_issuance"].eq(0).sum()),
            ("Coal-eligible country-years", panel["coal_eligible"].sum()),
            ("Mean issuance, basis points of GDP", panel["issuance_bp_gdp"].mean()),
            ("Median issuance, basis points of GDP", panel["issuance_bp_gdp"].median()),
        ],
        columns=["Statistic", "Value"],
    )
    summary.to_csv(RESULTS / "sample_summary.csv", index=False)

    rows = []
    for status, group in panel.groupby("recorded_positive_issuance", sort=True):
        for outcome in OUTCOMES:
            values = group[outcome].dropna()
            rows.append(
                {
                    "recorded_positive_issuance": int(status),
                    "issuance_status": "Positive recorded issuance" if status else "No recorded issuance",
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "events": int(values.sum()),
                    "denominator": len(values),
                    "frequency": float(values.mean()),
                    "frequency_percent": float(100 * values.mean()),
                }
            )
    frequencies = pd.DataFrame(rows)
    frequencies.to_csv(RESULTS / "outcome_frequencies.csv", index=False)

    magnitude_rows = []
    delta_map = {
        "delta_renewables_electricity": "Renewable generation change",
        "delta_coal_electricity": "Coal generation change",
        "delta_gas_electricity": "Gas generation change",
        "delta_oil_electricity": "Oil generation change",
        "delta_fossil_electricity": "Fossil generation change",
    }
    for status, group in panel.groupby("recorded_positive_issuance", sort=True):
        for variable, label in delta_map.items():
            values = group[variable].dropna()
            magnitude_rows.append(
                {
                    "recorded_positive_issuance": int(status),
                    "issuance_status": "Positive recorded issuance" if status else "No recorded issuance",
                    "variable": variable,
                    "label": label,
                    "n": len(values),
                    "mean_twh": float(values.mean()),
                    "median_twh": float(values.median()),
                    "q25_twh": float(values.quantile(0.25)),
                    "q75_twh": float(values.quantile(0.75)),
                }
            )
    pd.DataFrame(magnitude_rows).to_csv(RESULTS / "physical_magnitudes_by_issuance.csv", index=False)

    annual = (
        panel.groupby("year")
        .agg(
            countries=("iso3", "nunique"),
            issuance_active_share=("recorded_positive_issuance", "mean"),
            issuance_billion_usd=("issuance_billion_usd", "sum"),
            issuance_bp_gdp_mean=("issuance_bp_gdp", "mean"),
            fossil_contraction_rate=("fossil_contraction", "mean"),
            renewable_addition_rate=("renewable_addition", "mean"),
            coal_contraction_rate=("coal_contraction", "mean"),
            unoffset_coal_contraction_rate=("unoffset_coal_contraction", "mean"),
        )
        .reset_index()
    )
    annual.to_csv(RESULTS / "annual_summary.csv", index=False)

    country = (
        panel.groupby(["iso3", "country"])
        .agg(
            years=("year", "count"),
            positive_issuance_years=("recorded_positive_issuance", "sum"),
            cumulative_issuance_billion_usd=("issuance_billion_usd", "sum"),
            fossil_contraction_rate=("fossil_contraction", "mean"),
            renewable_addition_rate=("renewable_addition", "mean"),
            coal_contraction_rate=("coal_contraction", "mean"),
            unoffset_coal_contraction_rate=("unoffset_coal_contraction", "mean"),
        )
        .reset_index()
    )
    country.to_csv(RESULTS / "country_summary.csv", index=False)


def cluster_bootstrap(panel: pd.DataFrame, replications: int = 20_000) -> pd.DataFrame:
    country_means = panel.groupby("iso3")[OUTCOMES].mean()
    country_means["addition_exit_gap"] = country_means["renewable_addition"] - country_means["fossil_contraction"]
    metrics = OUTCOMES + ["addition_exit_gap"]
    rng = np.random.default_rng(SEED)
    rows = []
    for metric in metrics:
        values = country_means[metric].dropna().to_numpy()
        draws = rng.integers(0, len(values), size=(replications, len(values)))
        estimates = values[draws].mean(axis=1)
        point = float(values.mean())
        low, high = np.quantile(estimates, [0.025, 0.975])
        rows.append(
            {
                "metric": metric,
                "label": OUTCOME_LABELS.get(metric, "Renewable-addition minus fossil-contraction gap"),
                "point_estimate": point,
                "ci_low": float(low),
                "ci_high": float(high),
                "replications": replications,
                "seed": SEED,
                "eligible_countries": len(values),
            }
        )
    return pd.DataFrame(rows)


def model_outputs(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    main_rows = []
    for outcome in OUTCOMES:
        main_rows.append(
            fit_model(
                panel,
                outcome,
                "issuance_bp_gdp",
                "Strict sign; country and year FE",
                run_wild=outcome == "fossil_contraction",
            )
        )
    main = pd.DataFrame(main_rows)
    secondary_mask = main["outcome"].ne("fossil_contraction")
    adjusted = multipletests(main.loc[secondary_mask, "p_value_t_g_minus_1"], method="holm")[1]
    main["holm_adjusted_p_secondary"] = np.nan
    main.loc[secondary_mask, "holm_adjusted_p_secondary"] = adjusted

    robustness_rows = []
    for suffix, label in [("m010", "0.10% materiality"), ("m025", "0.25% materiality")]:
        robustness_rows.append(
            fit_model(
                panel,
                f"fossil_contraction_{suffix}",
                "issuance_bp_gdp",
                label,
                run_wild=True,
            )
        )
    robustness_rows.extend(
        [
            fit_model(panel, "fossil_contraction", "recorded_positive_issuance", "Active-issuance indicator"),
            fit_model(panel, "fossil_contraction", "lag_issuance_bp_gdp", "One-year lag"),
            fit_model(panel, "fossil_contraction", "issuance_100usd_per_capita", "Per-capita scale"),
            fit_model(panel.loc[panel["year"].ge(2016)], "fossil_contraction", "issuance_bp_gdp", "2016-2024"),
            fit_model(panel.loc[panel["pre_entry"].eq(0)], "fossil_contraction", "issuance_bp_gdp", "Exclude pre-entry years"),
        ]
    )
    robustness = pd.DataFrame(robustness_rows)

    threshold_rows = []
    for suffix, label in [("m010", "0.10% materiality"), ("m025", "0.25% materiality")]:
        for outcome in OUTCOMES:
            threshold_rows.append(
                fit_model(
                    panel,
                    f"{outcome}_{suffix}",
                    "issuance_bp_gdp",
                    label,
                    run_wild=False,
                )
            )
    pd.DataFrame(threshold_rows).to_csv(RESULTS / "threshold_models_all_outcomes.csv", index=False)

    loco_rows = []
    for outcome in OUTCOMES:
        for iso3 in sorted(panel["iso3"].unique()):
            estimate = fit_model(
                panel.loc[panel["iso3"].ne(iso3)],
                outcome,
                "issuance_bp_gdp",
                f"Exclude {iso3}",
            )
            estimate["excluded_country"] = iso3
            loco_rows.append(estimate)
    loco = pd.DataFrame(loco_rows)
    return main, robustness, loco


def make_figures(panel: pd.DataFrame, main: pd.DataFrame) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Nimbus Roman", "Times New Roman", "DejaVu Serif"],
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    annual = pd.read_csv(RESULTS / "annual_summary.csv")
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.2), sharex=True)
    axes[0].plot(annual["year"], 100 * annual["issuance_active_share"], color="#147D64", marker="o", linewidth=1.6)
    axes[0].set_ylabel("Countries with recorded issuance (%)")
    axes[0].set_title("Green-bond issuance coverage")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].plot(annual["year"], 100 * annual["renewable_addition_rate"], label="Renewable addition", color="#2A9D8F")
    axes[1].plot(annual["year"], 100 * annual["fossil_contraction_rate"], label="Fossil contraction", color="#B23A48")
    axes[1].set_ylabel("Country-years (%)")
    axes[1].set_xlabel("Year")
    axes[1].set_title("Physical transition outcomes")
    axes[1].legend(frameon=False, ncol=2)
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_1_annual_alignment.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "figure_1_annual_alignment.svg", bbox_inches="tight")
    plt.close(fig)

    freq = pd.read_csv(RESULTS / "outcome_frequencies.csv")
    pivot = freq.pivot(index="outcome_label", columns="issuance_status", values="frequency_percent").reindex(
        [OUTCOME_LABELS[x] for x in OUTCOMES]
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    pivot.plot(kind="bar", ax=ax, color=["#B7B7B7", "#147D64"], width=0.75)
    ax.set_ylabel("Country-years (%)")
    ax.set_xlabel("")
    ax.set_title("Physical outcomes by issuance status")
    ax.legend(frameon=False, title="")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_2_outcomes_by_issuance.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "figure_2_outcomes_by_issuance.svg", bbox_inches="tight")
    plt.close(fig)

    plot = main.iloc[::-1].copy()
    plot["estimate_pp_10bp"] = 1000 * plot["coefficient"]
    plot["ci_low_pp_10bp"] = 1000 * plot["ci_low"]
    plot["ci_high_pp_10bp"] = 1000 * plot["ci_high"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = np.arange(len(plot))
    ax.errorbar(
        plot["estimate_pp_10bp"],
        y,
        xerr=[plot["estimate_pp_10bp"] - plot["ci_low_pp_10bp"], plot["ci_high_pp_10bp"] - plot["estimate_pp_10bp"]],
        fmt="o",
        color="#264653",
        ecolor="#264653",
        capsize=3,
    )
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(y, plot["outcome_label"])
    ax.set_xlabel("Probability change (percentage points per 10 bp of GDP)")
    ax.set_title("Issuance intensity and physical outcomes")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure_3_fixed_effects_estimates.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "figure_3_fixed_effects_estimates.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for directory in [RESULTS, TABLES, FIGURES, VERIFY]:
        directory.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(DATA)
    descriptive_outputs(panel)
    bootstrap = cluster_bootstrap(panel)
    bootstrap.to_csv(RESULTS / "descriptive_cluster_bootstrap.csv", index=False)
    main_models, robustness, loco = model_outputs(panel)
    main_models.to_csv(RESULTS / "main_models.csv", index=False)
    robustness.to_csv(RESULTS / "robustness_models.csv", index=False)
    loco.to_csv(RESULTS / "loco_all_outcomes.csv", index=False)

    table_map = {
        "sample_summary.csv": "table_1_sample_summary.csv",
        "outcome_frequencies.csv": "table_2_outcome_frequencies.csv",
        "main_models.csv": "table_3_main_models.csv",
        "robustness_models.csv": "table_s1_robustness.csv",
        "loco_all_outcomes.csv": "table_s2_loco.csv",
        "descriptive_cluster_bootstrap.csv": "table_s3_bootstrap.csv",
        "physical_magnitudes_by_issuance.csv": "table_s4_physical_magnitudes.csv",
        "threshold_models_all_outcomes.csv": "table_s5_threshold_models.csv",
    }
    for source, target in table_map.items():
        shutil.copyfile(RESULTS / source, TABLES / target)

    make_figures(panel, main_models)
    outputs = sorted(
        [path for directory in [RESULTS, TABLES, FIGURES] for path in directory.iterdir() if path.is_file()]
    )
    manifest = {
        "seed": SEED,
        "primary_outcome": CONFIG["primary_outcome"],
        "primary_exposure": CONFIG["primary_exposure"],
        "wild_cluster_bootstrap": {
            "replications": CONFIG["wild_cluster_bootstrap_replications"],
            "weights": "webb",
            "bootstrap_type": "33",
        },
        "outputs": {str(path.relative_to(ROOT)): sha256(path) for path in outputs},
    }
    (VERIFY / "result_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(main_models.to_string(index=False))
    print("\nPrimary robustness")
    print(robustness.to_string(index=False))


if __name__ == "__main__":
    main()
