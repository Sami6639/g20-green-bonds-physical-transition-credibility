from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
VERIFY = ROOT / "verification"
CONFIG = json.loads((ROOT / "config" / "analysis_config.json").read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_owid() -> pd.DataFrame:
    columns = [
        "country",
        "iso_code",
        "year",
        "coal_electricity",
        "gas_electricity",
        "oil_electricity",
        "fossil_electricity",
        "renewables_electricity",
        "electricity_generation",
        "population",
    ]
    frame = pd.read_csv(RAW / "owid-energy-data.csv", usecols=columns)
    frame = frame.loc[
        frame["iso_code"].isin(CONFIG["country_iso3"])
        & frame["year"].between(CONFIG["lag_buffer_year"], CONFIG["analysis_end_year"])
    ].copy()
    frame = frame.rename(columns={"iso_code": "iso3"})
    if frame.duplicated(["iso3", "year"]).any():
        raise ValueError("Duplicate OWID country-year keys")
    if len(frame) != 19 * 20:
        raise ValueError(f"Unexpected OWID buffer size: {len(frame)}")
    return frame


def load_imf() -> pd.DataFrame:
    raw = json.loads((RAW / "imf-green-bonds-feature-query.json").read_text())
    frame = pd.DataFrame([feature["attributes"] for feature in raw["features"]])
    frame = frame.loc[
        frame["Indicator"].eq("Green Bond Issuances by Country")
        & frame["ISO3"].isin(CONFIG["country_iso3"])
    ].copy()
    if frame["ISO3"].duplicated().any() or len(frame) != 19:
        raise ValueError("IMF G20 country rows are not unique and complete")
    year_columns = [f"F{year}" for year in range(CONFIG["analysis_start_year"], CONFIG["analysis_end_year"] + 1)]
    frame = frame.melt(
        id_vars=["Country", "ISO3"],
        value_vars=year_columns,
        var_name="year",
        value_name="imf_issuance_billion_usd_raw",
    )
    frame["year"] = frame["year"].str.removeprefix("F").astype(int)
    frame = frame.rename(columns={"Country": "imf_country", "ISO3": "iso3"})
    frame["imf_cell_observed"] = frame["imf_issuance_billion_usd_raw"].notna().astype(int)
    frame["recorded_positive_issuance"] = frame["imf_issuance_billion_usd_raw"].fillna(0).gt(0).astype(int)
    frame["issuance_billion_usd"] = frame["imf_issuance_billion_usd_raw"].fillna(0.0)
    frame["issuance_usd"] = frame["issuance_billion_usd"] * 1_000_000_000.0
    first_entry = (
        frame.loc[frame["recorded_positive_issuance"].eq(1)]
        .groupby("iso3")["year"]
        .min()
        .rename("first_recorded_issuance_year")
    )
    frame = frame.merge(first_entry, on="iso3", how="left", validate="many_to_one")
    frame["pre_entry"] = frame["year"].lt(frame["first_recorded_issuance_year"]).astype(int)
    frame["post_entry_no_record"] = (
        frame["year"].ge(frame["first_recorded_issuance_year"])
        & frame["recorded_positive_issuance"].eq(0)
    ).astype(int)
    return frame


def load_wdi() -> pd.DataFrame:
    raw = json.loads((RAW / "wdi-gdp-current-usd-2005-2024.json").read_text())
    frame = pd.DataFrame(raw[1])
    frame = frame[["countryiso3code", "date", "value"]].rename(
        columns={"countryiso3code": "iso3", "date": "year", "value": "gdp_current_usd"}
    )
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["iso3", "year"]).any() or len(frame) != 19 * 20:
        raise ValueError("WDI G20 country-year rows are not unique and complete")
    if frame["gdp_current_usd"].isna().any() or frame["gdp_current_usd"].le(0).any():
        raise ValueError("WDI GDP contains missing or non-positive values")
    return frame


def build_panel() -> pd.DataFrame:
    owid = load_owid().sort_values(["iso3", "year"])
    wdi = load_wdi()
    finance = load_imf()

    lag_variables = [
        "coal_electricity",
        "gas_electricity",
        "oil_electricity",
        "fossil_electricity",
        "renewables_electricity",
        "electricity_generation",
    ]
    for variable in lag_variables:
        owid[f"lag_{variable}"] = owid.groupby("iso3")[variable].shift(1)
        owid[f"delta_{variable}"] = owid[variable] - owid[f"lag_{variable}"]

    panel = owid.loc[owid["year"].between(CONFIG["analysis_start_year"], CONFIG["analysis_end_year"])].copy()
    panel = panel.merge(wdi, on=["iso3", "year"], how="left", validate="one_to_one")
    panel = panel.merge(finance, on=["iso3", "year"], how="left", validate="one_to_one")
    if len(panel) != 19 * 19 or panel.duplicated(["iso3", "year"]).any():
        raise ValueError("Unexpected analytical panel dimensions")

    panel["issuance_bp_gdp"] = 10_000.0 * panel["issuance_usd"] / panel["gdp_current_usd"]
    panel["issuance_usd_per_capita"] = panel["issuance_usd"] / panel["population"]
    panel["issuance_100usd_per_capita"] = panel["issuance_usd_per_capita"] / 100.0
    panel["cluster_id"] = pd.Categorical(panel["iso3"], categories=CONFIG["country_iso3"]).codes.astype(int)
    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
    panel["lag_issuance_bp_gdp"] = panel.groupby("iso3")["issuance_bp_gdp"].shift(1)
    panel["coal_eligible"] = panel["lag_coal_electricity"].gt(0).astype(int)
    panel["delta_gas_oil"] = panel["delta_gas_electricity"] + panel["delta_oil_electricity"]

    suffixes = {0.0: "strict", 0.001: "m010", 0.0025: "m025"}
    for threshold, suffix in suffixes.items():
        material_change = threshold * panel["lag_electricity_generation"]
        panel[f"renewable_addition_{suffix}"] = panel["delta_renewables_electricity"].gt(material_change).astype(int)
        panel[f"fossil_contraction_{suffix}"] = panel["delta_fossil_electricity"].lt(-material_change).astype(int)

        coal_contracts = panel["delta_coal_electricity"].lt(-material_change)
        panel[f"coal_contraction_{suffix}"] = np.where(
            panel["coal_eligible"].eq(1), coal_contracts.astype(int), np.nan
        )
        panel[f"unoffset_coal_contraction_{suffix}"] = np.where(
            panel["coal_eligible"].eq(1),
            (coal_contracts & panel["delta_gas_oil"].le(0)).astype(int),
            np.nan,
        )

    panel["renewable_addition"] = panel["renewable_addition_strict"]
    panel["fossil_contraction"] = panel["fossil_contraction_strict"]
    panel["coal_contraction"] = panel["coal_contraction_strict"]
    panel["unoffset_coal_contraction"] = panel["unoffset_coal_contraction_strict"]
    return panel


def main() -> None:
    panel = build_panel()
    DERIVED.mkdir(parents=True, exist_ok=True)
    VERIFY.mkdir(parents=True, exist_ok=True)
    csv_path = DERIVED / "analytical_panel_2006_2024.csv"
    parquet_path = DERIVED / "analytical_panel_2006_2024.parquet"
    panel.to_csv(csv_path, index=False)
    panel.to_parquet(parquet_path, index=False)

    audit = {
        "rows": len(panel),
        "countries": int(panel["iso3"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "unique_country_year": bool(not panel.duplicated(["iso3", "year"]).any()),
        "primary_outcome_complete": bool(panel["fossil_contraction"].notna().all()),
        "finance_intensity_complete": bool(panel["issuance_bp_gdp"].notna().all()),
        "coal_eligible_rows": int(panel["coal_eligible"].sum()),
        "positive_recorded_issuance_rows": int(panel["recorded_positive_issuance"].sum()),
        "imf_blank_rows": int(panel["imf_cell_observed"].eq(0).sum()),
        "csv_sha256": sha256(csv_path),
        "parquet_sha256": sha256(parquet_path),
    }
    (VERIFY / "panel_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
