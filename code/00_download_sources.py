from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = json.loads((ROOT / "config" / "analysis_config.json").read_text())

SERVICE = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Indicator_10_Green_Finance/FeatureServer/0"
ITEM = "https://www.arcgis.com/sharing/rest/content/items/8e2772e0b65f4e33a80183ce9583d062"

SOURCES = {
    "owid-energy-data.csv": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
    "owid-energy-codebook.csv": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-codebook.csv",
    "imf-green-bonds-feature-query.json": SERVICE + "/query?" + urllib.parse.urlencode(
        {"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json"}
    ),
    "imf-green-bonds-layer-metadata.json": SERVICE + "?f=pjson",
    "imf-green-bonds-item-metadata.json": ITEM + "?f=pjson",
    "wdi-gdp-current-usd-2005-2024.json": (
        "https://api.worldbank.org/v2/country/"
        + ";".join(CONFIG["country_iso3"])
        + "/indicator/NY.GDP.MKTP.CD?"
        + urllib.parse.urlencode({"date": "2005:2024", "format": "json", "per_page": 20000})
    ),
}

EXPECTED = {
    "owid-energy-data.csv": "266f2e2baad7975351bc9bb4aa061d22b1da9fe4c47d51d2ac6071e01e171f76",
    "owid-energy-codebook.csv": "3cc9b7db0d921496e2988568ce3aee5ed41f50431dd234a0663b5f0a4b2e32bb",
    "imf-green-bonds-feature-query.json": "9838ee3f2e52233d0b071ce30b8b8b2416da6cd4d9f821c686e95b89b488a956",
    "imf-green-bonds-layer-metadata.json": "333f4c77c2449cd24c1038b3391e53397ebf75be8b72f02989d5d2bcb72069d1",
    "imf-green-bonds-item-metadata.json": "a4a85ede58dec24a820c9faae3ef379c42d1b35975919482fa76d28738453fbb",
    "wdi-gdp-current-usd-2005-2024.json": "771d493d14497ce2604db81873e793f4cab13e4e74d751b48bc3d179a39d4dbe",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    drift = []
    for name, url in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "G20-green-bond-reproducibility/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
        digest = sha256(payload)
        target = RAW / name
        target.write_bytes(payload)
        status = "FROZEN MATCH" if digest == EXPECTED[name] else "SOURCE DRIFT"
        print(f"{name}: {status} ({digest})")
        if digest != EXPECTED[name]:
            drift.append(name)
    if drift:
        raise SystemExit(
            "Provider responses no longer match the frozen snapshots: " + ", ".join(drift)
            + ". Review source-version changes before running the locked analysis."
        )


if __name__ == "__main__":
    main()
