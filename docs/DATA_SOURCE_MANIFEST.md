# Data Source Manifest

Access date for the frozen source files: 4 September 2026 (UTC).

| Source file | Provider and source | Coverage/role | SHA-256 | Status |
|---|---|---|---|---|
| `owid-energy-data.csv` | Our World in Data Energy dataset | Physical electricity-generation variables; 2005–2024 buffer and analysis | `266f2e2baad7975351bc9bb4aa061d22b1da9fe4c47d51d2ac6071e01e171f76` | LOCKED |
| `owid-energy-codebook.csv` | Our World in Data Energy codebook | Variable definitions and provider lineage | `3cc9b7db0d921496e2988568ce3aee5ed41f50431dd234a0663b5f0a4b2e32bb` | LOCKED |
| `imf-green-bonds-feature-query.json` | IMF Climate Change Dashboard; underlying LSEG/Refinitiv records and IMF calculations | Country-attributed annual green-bond issuance, 2006–2024 | `9838ee3f2e52233d0b071ce30b8b8b2416da6cd4d9f821c686e95b89b488a956` | LOCKED LOCALLY; REDISTRIBUTION VALIDATION REQUIRED |
| `imf-green-bonds-layer-metadata.json` | IMF/ArcGIS feature-layer metadata | Field schema and service metadata | `333f4c77c2449cd24c1038b3391e53397ebf75be8b72f02989d5d2bcb72069d1` | LOCKED |
| `imf-green-bonds-item-metadata.json` | IMF/ArcGIS item metadata | Attribution, public-access status and IMF usage-terms reference | `a4a85ede58dec24a820c9faae3ef379c42d1b35975919482fa76d28738453fbb` | LOCKED |
| `wdi-gdp-current-usd-2005-2024.json` | World Bank, World Development Indicators, `NY.GDP.MKTP.CD` | Nominal-GDP denominator in current USD | `771d493d14497ce2604db81873e793f4cab13e4e74d751b48bc3d179a39d4dbe` | LOCKED |

## Canonical source locations

- OWID Energy data: `https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv`
- OWID codebook: `https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-codebook.csv`
- IMF Green Bonds item: `https://www.arcgis.com/home/item.html?id=8e2772e0b65f4e33a80183ce9583d062`
- IMF Green Bonds feature service: `https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Indicator_10_Green_Finance/FeatureServer/0`
- World Bank GDP indicator: `https://api.worldbank.org/v2/country/{countries}/indicator/NY.GDP.MKTP.CD?date=2005:2024&format=json`

## Source-version notes

- The World Bank response reports `lastupdated = 2026-07-13` and contains all 380 required country-years for 19 countries over 2005–2024.
- The IMF feature layer reports its last data edit at `2025-05-19T17:34:53.692Z`; the public item was modified at `2025-05-20T14:09:23Z`.
- The IMF item attributes the source to Refinitiv, country authorities and IMF staff calculations and links to IMF Copyright and Usage terms. The raw financial source must not be placed in a public repository until redistribution permission is verified. A reproducible download script, metadata and checksums may be distributed if permitted.

## Canonical units

- Electricity generation: TWh.
- Green-bond issuance: billion current US dollars in the provider table; converted to current US dollars before normalisation.
- GDP: current US dollars.
- Issuance intensity: basis points of GDP, `10,000 × issuance_USD / GDP_USD`.
- Population sensitivity: issuance current US dollars per person.

## Immutable-raw rule

Files in `data/raw` are immutable. Cleaning, harmonisation and analytical variables must be written to `data/derived`; no script may overwrite a raw file.
