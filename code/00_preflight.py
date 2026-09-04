from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
VERIFY = ROOT / "verification"

EXPECTED_HASHES = {
    "owid-energy-data.csv": "266f2e2baad7975351bc9bb4aa061d22b1da9fe4c47d51d2ac6071e01e171f76",
    "owid-energy-codebook.csv": "3cc9b7db0d921496e2988568ce3aee5ed41f50431dd234a0663b5f0a4b2e32bb",
    "imf-green-bonds-feature-query.json": "9838ee3f2e52233d0b071ce30b8b8b2416da6cd4d9f821c686e95b89b488a956",
    "imf-green-bonds-layer-metadata.json": "333f4c77c2449cd24c1038b3391e53397ebf75be8b72f02989d5d2bcb72069d1",
    "imf-green-bonds-item-metadata.json": "a4a85ede58dec24a820c9faae3ef379c42d1b35975919482fa76d28738453fbb",
    "wdi-gdp-current-usd-2005-2024.json": "771d493d14497ce2604db81873e793f4cab13e4e74d751b48bc3d179a39d4dbe",
}

EXPECTED_PACKAGES = {
    "numpy": "2.3.5",
    "pandas": "2.2.3",
    "scipy": "1.17.0",
    "matplotlib": "3.10.8",
    "seaborn": "0.13.2",
    "pyfixest": "0.60.0",
    "wildboottest": "0.3.2",
    "statsmodels": "0.15.0",
    "pyarrow": "25.0.1",
    "pytest": "9.1.1",
    "python-docx": "1.2.0",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config = json.loads((ROOT / "config" / "analysis_config.json").read_text())
    countries = set(config["country_iso3"])
    checks: dict[str, object] = {}

    actual_hashes = {name: sha256(RAW / name) for name in EXPECTED_HASHES}
    checks["raw_hashes_match"] = actual_hashes == EXPECTED_HASHES
    checks["raw_hashes"] = actual_hashes

    package_versions = {name: version(name) for name in EXPECTED_PACKAGES}
    checks["package_versions_match"] = package_versions == EXPECTED_PACKAGES
    checks["package_versions"] = package_versions
    checks["python_version"] = platform.python_version()
    checks["python_major_minor_match"] = platform.python_version_tuple()[:2] == ("3", "12")

    owid = pd.read_csv(RAW / "owid-energy-data.csv")
    owid = owid.loc[
        owid["iso_code"].isin(countries)
        & owid["year"].between(config["lag_buffer_year"], config["analysis_end_year"])
    ]
    physical = [
        "coal_electricity",
        "gas_electricity",
        "oil_electricity",
        "fossil_electricity",
        "renewables_electricity",
        "electricity_generation",
        "population",
    ]
    checks["owid_rows"] = len(owid)
    checks["owid_unique_keys"] = not owid.duplicated(["iso_code", "year"]).any()
    checks["owid_complete"] = not owid[physical].isna().any().any()
    reconciliation = (
        owid["coal_electricity"]
        + owid["gas_electricity"]
        + owid["oil_electricity"]
        - owid["fossil_electricity"]
    ).abs()
    checks["max_fossil_reconciliation_twh"] = float(reconciliation.max())
    checks["fossil_reconciliation_pass"] = bool(reconciliation.max() <= 0.0010001)

    imf_object = json.loads((RAW / "imf-green-bonds-feature-query.json").read_text())
    imf = pd.DataFrame([feature["attributes"] for feature in imf_object["features"]])
    green = imf.loc[imf["Indicator"].eq("Green Bond Issuances by Country")]
    green_g20 = green.loc[green["ISO3"].isin(countries)]
    checks["imf_g20_country_rows"] = len(green_g20)
    checks["imf_unique_country_rows"] = not green_g20["ISO3"].duplicated().any()
    checks["imf_country_set_match"] = set(green_g20["ISO3"]) == countries

    wdi_object = json.loads((RAW / "wdi-gdp-current-usd-2005-2024.json").read_text())
    wdi = pd.DataFrame(wdi_object[1])
    checks["wdi_rows"] = len(wdi)
    checks["wdi_unique_keys"] = not wdi.duplicated(["countryiso3code", "date"]).any()
    checks["wdi_complete_positive"] = bool(wdi["value"].notna().all() and (wdi["value"] > 0).all())
    checks["wdi_country_set_match"] = set(wdi["countryiso3code"]) == countries

    required_true = [
        "raw_hashes_match",
        "package_versions_match",
        "python_major_minor_match",
        "owid_unique_keys",
        "owid_complete",
        "fossil_reconciliation_pass",
        "imf_unique_country_rows",
        "imf_country_set_match",
        "wdi_unique_keys",
        "wdi_complete_positive",
        "wdi_country_set_match",
    ]
    counts_pass = checks["owid_rows"] == 380 and checks["imf_g20_country_rows"] == 19 and checks["wdi_rows"] == 380
    checks["baseline_pass"] = bool(counts_pass and all(checks[key] for key in required_true))
    checks["decision"] = "IMPLEMENTATION BASELINE PASS" if checks["baseline_pass"] else "IMPLEMENTATION BASELINE FAIL"

    VERIFY.mkdir(parents=True, exist_ok=True)
    output = VERIFY / "preflight_report.json"
    output.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n")
    print(checks["decision"])
    print(output)
    if not checks["baseline_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
