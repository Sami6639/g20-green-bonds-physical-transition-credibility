# Table S6: exposure-distribution diagnostics

This supplement supplies the executable code and machine-readable results for the exploratory diagnostics retained in Table S6. It does not change the main exposure, endpoints, period, hypotheses or prespecified analysis.

## Reproduce

Use the repository's locked environment and official source-retrieval workflow. Once `code/01_build_panel.py` has created the local analytical panel, run:

```bash
python code/06_exposure_diagnostics.py
```

The script writes `results/exposure_diagnostics.csv`, `tables/table_s6_exposure_diagnostics.csv`, and `verification/s6_diagnostics_manifest.json`. It checks every displayed coefficient, confidence limit, p-value and sample size against Table S6. No provider observations or analytical panel are redistributed by this supplement.

## Definitions

- Baseline: untransformed issuance in basis points of nominal GDP.
- Inverse hyperbolic sine: `asinh(issuance_bp_gdp)`, reported per one transformed unit.
- Winsorization: replace exposure values above the pooled 99th percentile by that percentile.
- Upper-tail trimming: omit values strictly above the same percentile; retain 357 observations.
- Five largest observations: rank the original exposure in descending order and remove exactly five country-years; retain 356 observations. Country and year are deterministic tie-breakers.
- The pooled percentile uses linear interpolation in the original 361-observation panel. Outcomes and all remaining observations are unchanged.

## Inference and units

Each model is OLS with country and year fixed effects. The implementation refits OLS after deleting each country and computes the covariance around the full-sample coefficient. It reproduces the small-sample scaling of the retained PyFixest 0.60.0 CRV3 results: multiply the sum of squared deletion deviations by `G/(G-1) * (N-1)/(N-K)`, with `K = number of year levels + 1`. Country fixed effects are nested in the clustering dimension. These settings correspond to `k_adj=True`, `G_adj=True`, `k_fixef="nonnested"`, and `G_df="min"`; tests and confidence intervals use `t(G-1)`.

The software scaling is stated explicitly because it differs from a cluster-jackknife convention that applies only `(G-1)/G` to the same sum. The supplement retains the published variance scaling and does not replace it with a different estimator.

Multiply raw slopes and confidence limits by 1,000 for percentage-point changes per ten basis points. Multiply them by 100 for the asinh row. These diagnostics are exploratory and do not identify causal financing effects.

## Validation

All five Table S6 rows were reconstructed from source files matching the repository's frozen checksums and matched the manuscript at reported precision. The baseline result also matches `results/main_models.csv`. The independent OLS and deletion calculations reproduce the recorded covariance scaling without requiring an additional estimator package.

Source and output checksums are recorded in the repository's existing manifests and the supplementary S6 manifest. This check covers Table S6; it does not imply that the main wild-cluster bootstrap has been rerun.
