# Green Bonds without Fossil Exit?

This repository contains the reproducibility materials for *Green Bonds without Fossil Exit? Physical Transition Credibility in G20 Electricity Systems*.

The study evaluates whether recorded green-bond issuance intensity is aligned with four annual electricity-system outcomes across 19 G20 country members from 2006 to 2024: renewable addition, coal contraction, total fossil contraction, and coal contraction without gas- or oil-based offsetting. The design is descriptive and associational; it does not estimate a causal financing effect.

## Reproduce the results

1. Create the locked environment:

   ```bash
   conda env create -f environment.yml
   conda activate g20-green-bond-physical-alignment
   ```

2. Place the frozen source files listed in `docs/DATA_SOURCE_MANIFEST.md` in `data/raw/`. If redistribution of a source snapshot is not permitted, run `python code/00_download_sources.py` to retrieve it from the official provider and check for source drift.

3. Run the complete pipeline:

   ```bash
   python run_all.py
   pytest -q
   ```

Successful execution ends with `REPRODUCIBILITY PIPELINE PASS` and `VERIFICATION PASS`.

## Repository map

- `code/`: source retrieval, panel construction, analysis, verification, and Word-manuscript generation.
- `config/`: locked country, period, threshold, bootstrap, and estimand settings.
- `data/derived/`: analytical panel when redistribution is permitted.
- `docs/`: decision log, implementation specification, source manifest, results memo, and reference-verification manifest.
- `figures/`: publication figures in PNG and SVG formats.
- `results/`: machine-readable analytical results.
- `tables/`: machine-readable table sources.
- `tests/`: reproducibility tests.
- `verification/`: checksums and machine-readable audit reports.

## Data boundary

Electricity data are from Our World in Data, GDP is from the World Bank World Development Indicators, and green-bond issuance is from the IMF Climate Change Indicators Dashboard. The IMF source attributes issuance to the issuer's country of incorporation; it does not identify the location or sectoral allocation of proceeds. A blank dashboard cell is coded as no recorded issuance, not as verified absence of every eligible transaction.

Provider-level financial observations are redistributed only when their terms permit. The public package otherwise supplies official retrieval locations, metadata, checksums, code, derived outputs permitted by the source terms, and complete result manifests.

## Reproducibility controls

- Frozen project seed: `20260904`.
- Country-cluster bootstrap: 20,000 replications.
- Primary wild-cluster bootstrap-t: 9,999 replications, Webb weights, WCR33.
- Small-cluster inference: CRV3 with a `t(G−1)` reference distribution.
- Primary endpoint: annual absolute total-fossil-electricity contraction.

## License and citation

Code is released under the MIT License. Source data retain their providers' terms; see `LICENSES.md`. Citation metadata are available in `CITATION.cff`.
