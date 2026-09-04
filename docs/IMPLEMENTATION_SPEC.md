# Implementation Handoff Specification

## 1. Locked Primary RQ and sub-RQs

**Primary RQ:** Across G20 electricity systems, to what extent is recorded green-bond issuance aligned with distinct annual physical transition outcomes: renewable addition, coal contraction, absolute fossil contraction, and coal contraction without gas- or oil-based offsetting?

**Sub-RQs:**

1. How frequently does recorded issuance coexist with each physical outcome, and how large is the difference between renewable-addition and absolute-fossil-contraction frequencies?
2. After accounting for stable country characteristics and common year shocks, how does issuance intensity relate to absolute fossil contraction, and how does that association compare with the other physical margins?
3. Are conclusions sensitive to material-change thresholds, non-recorded-issuance treatment, scale denominator, period or any single country?

## 2. Scientific scope

### In scope

- Jurisdiction-level financial–physical alignment.
- Annual country-level green-bond issuance attributed by issuer incorporation.
- Annual absolute electricity generation from renewables, coal, gas, oil and total fossil sources.
- Descriptive profiles and fixed-effects associations.
- Pre-specified measurement, timing, scale and influence sensitivities.

### Out of scope

- Project destination or use-of-proceeds allocation.
- Causal financing effectiveness, additionality or treatment effects.
- Bond pricing, yields, spreads or portfolio performance.
- A weighted credibility score, country rating or league table.
- Mechanism discovery after results.
- Transition matrices, spell models, latent regimes or survival models.

## 3. Locked outcomes, functional unit and estimands

- **Functional unit:** Country-year.
- **Primary endpoint:** `fossil_contraction`, the indicator that annual total fossil electricity changes by less than zero under the strict-sign baseline.
- **Benchmark endpoint:** `renewable_addition`.
- **Secondary endpoints:** `coal_contraction` and `unoffset_coal_contraction`.
- **Primary descriptive estimands:** Outcome frequencies and mean/median absolute TWh changes by recorded-issuance status; renewable-addition minus fossil-contraction frequency gap.
- **Primary associational estimand:** The within-country, common-year-adjusted change in the probability of fossil contraction associated with a one-basis-point increase in annual issuance/GDP.
- **Comparative estimands:** Identically defined coefficients for the benchmark and secondary endpoints.

## 4. Locked exposure architecture

- `issuance_usd = IMF_value_billion × 1e9`.
- `issuance_bp_gdp = 10,000 × issuance_usd / nominal_gdp_usd`.
- `recorded_positive_issuance = 1[IMF_value_billion > 0]`.
- Blank IMF cells become zero only inside the computational variable representing `no recorded issuance`; retain an explicit source-status flag.
- `pre_entry = 1` before a country's first positive recorded issuance.
- `post_entry_no_record = 1` after first entry when the annual cell has no recorded amount.
- One-year lag is sensitivity-only and non-causal.

## 5. Geography, population and time

- Nineteen country members of the G20: ARG, AUS, BRA, CAN, CHN, FRA, DEU, IND, IDN, ITA, JPN, MEX, RUS, SAU, ZAF, KOR, TUR, GBR and USA.
- Do not include the European Union separately.
- Analysis years 2006–2024; 2005 only supplies first differences.
- Expected unrestricted panel: 361 country-years.
- Coal outcomes require positive prior-year coal generation; expected eligibility: 342 country-years.

## 6. Group and technology strategy

- Renewables follow the frozen OWID `renewables_electricity` boundary.
- Fossil follows the frozen OWID `fossil_electricity` boundary.
- Coal, gas and oil use their corresponding OWID electricity variables.
- Do not reclassify nuclear, bioenergy or imported electricity after inspecting outcomes.
- Do not create post-result regional or income groups.

## 7. State and variable representation

For source `X` in TWh:

`delta_X_it = X_it - X_i,t-1`.

Strict-sign indicators:

- `renewable_addition = 1[delta_renewables > 0]`.
- `coal_contraction = 1[delta_coal < 0]` for coal-eligible rows.
- `fossil_contraction = 1[delta_fossil < 0]`.
- `unoffset_coal_contraction = 1[delta_coal < 0 and delta_gas + delta_oil <= 0]` for coal-eligible rows.

Materiality indicators use `m_it(tau) = tau × electricity_generation_i,t-1`, where `tau` is 0.001 or 0.0025, for the focal renewable, coal or fossil change. The combined gas-plus-oil no-offset condition remains `<= 0`.

## 8. Frozen core data sources

Use only the files and hashes in `docs/DATA_SOURCE_MANIFEST.md`. Raw inputs are immutable. A hash mismatch is a hard stop.

## 9. Locked scientific and statistical chain

1. The financial dataset records issuance attributed to an issuer jurisdiction.
2. The energy dataset records physical generation inside a national electricity-system boundary.
3. Merging by ISO3 and year creates a jurisdiction-level alignment panel.
4. Descriptive overlap establishes coexistence, not allocation or causality.
5. Country fixed effects remove stable country differences; year fixed effects remove common year shocks.
6. Remaining coefficients are conditional associations and may still reflect reverse causality, time-varying policy and omitted factors.
7. CRV3 and wild-cluster inference address finite-cluster uncertainty but do not repair identification.

## 10. Software components

- Python 3.12.
- pandas/numpy: data handling and deterministic transformations.
- pyfixest: fixed-effects linear probability models and CRV3 covariance.
- wildboottest through the supported pyfixest interface: wild-cluster inference.
- scipy/statsmodels only for supporting diagnostics where their implementation is explicitly tested.
- matplotlib/seaborn: code-generated figures.
- python-docx: later manuscript assembly; not part of scientific estimation.
- pytest: transformation and regression tests.

## 11. Locked measurement boundary

- `Green bonds` is the measured financial construct; do not substitute the broader phrase `green finance` in empirical claims.
- Issuer incorporation is not investment destination.
- Electricity generation is not installed capacity, emissions, consumption or investment.
- Annual direction is not long-run structural transition.
- A decline in fossil generation is not proof that green bonds caused fossil exit.

## 12. Feasibility boundary

- Do not estimate an endpoint when its eligibility sample is undefined or below the locked data-quality envelope.
- Do not impute physical generation, GDP or ISO3 identifiers.
- Do not interpolate issuance amounts.
- Do not create country-level outstanding amounts from cumulative issuance.

## 13. Time representation

- Contemporaneous annual alignment is primary.
- A one-year lag is sensitivity-only.
- No data-driven lag selection.
- No persistence or spell claim in the primary manuscript.

## 14. Main and sensitivity specifications

### Main model

`Y_k,it = alpha_i + lambda_t + beta_k issuance_bp_gdp_it + epsilon_k,it`.

- `k = fossil_contraction` is primary.
- Country and year fixed effects are mandatory.
- CRV3 covariance clustered by country is the primary reported covariance.
- Use a `t(G-1)` reference with `G = 19` for coefficient inference.

### Sensitivities

1. `tau = 0.001` and `tau = 0.0025` physical thresholds.
2. Positive-recorded-issuance indicator.
3. One-year lagged issuance intensity.
4. Issuance USD per person.
5. 2016–2024 period.
6. Exclude pre-entry blank years.
7. Leave one country out.
8. Wild-cluster bootstrap-t with a fixed seed and pre-specified iteration count.
9. Holm correction across three secondary endpoint tests.

## 15. End-of-life/accounting treatment

Not applicable. Bond maturity and project asset life are not observed. Do not interpret annual issuance as outstanding finance or annual generation as asset retirement.

## 16. False-result hard gate

Reject a headline interpretation when any of the following holds:

- source or derived hashes fail;
- the primary sign reverses at either materiality threshold;
- the conclusion depends on excluding or including one country;
- the result exists only under a lag or denominator chosen after inspection;
- the coefficient is statistically fragile under CRV3 and wild-cluster inference;
- the magnitude is negligible even if a p-value is small;
- the prose implies project allocation, additionality or causality.

## 17. Admissible evidence envelope

- Descriptive frequencies, absolute TWh changes and model-adjusted probability associations are admissible.
- `Indicates`, `is associated with`, `coincides with` and `is consistent with` are admissible when numerically supported.
- `Causes`, `drives`, `delivers`, `finances domestic exit`, `impact` and `effectiveness` are inadmissible for headline interpretation.

## 18. Uncertainty architecture

- CRV3 country-clustered standard errors and finite-cluster reference distribution.
- Wild-cluster bootstrap-t sensitivity with fixed seed.
- Country-resampling descriptive intervals where relevant.
- Leave-one-country-out influence diagnostics.
- Holm-adjusted secondary-family inference.
- Exact denominators and event counts accompany percentages.

## 19. Data storage contract

- `data/raw`: immutable frozen sources.
- `data/derived`: analytical panel and machine-readable transformations.
- `results`: coefficients, intervals, robustness and influence outputs.
- `tables`: publication tables generated from results.
- `figures`: publication figures generated from results.
- `verification`: hashes, data audit and reproducibility report.
- `logs`: timestamped execution logs.
- `config`: country list, thresholds, seed and source paths.

## 20. Reproducibility rules

- One master command reproduces all derived data, results, tables, figures and verification outputs.
- Fixed random seed: `20260904`.
- No manual edits to generated CSV, table or figure outputs.
- Exact package versions are pinned.
- Each table and figure maps to one generating script/output file.
- Raw-data redistribution follows the source licence; restricted raw data are replaced by retrieval instructions and checksums.

## 21. Forbidden shortcuts

- Silent zero imputation without the source-status flag.
- Dropping an inconvenient country or year.
- Selecting thresholds, lags, transformations or subgroups after results.
- Reporting conventional iid or HC standard errors as primary.
- Treating four outcomes as four unadjusted confirmatory tests.
- Editing a chart or table manually.
- Copying a primary estimand or narrative from the earlier three papers.

## 22. Implementation order

1. Verify raw hashes.
2. Parse and harmonise each source separately.
3. Run source-specific quality checks.
4. Merge by ISO3-year and assert the expected panel.
5. Generate locked variables and threshold variants.
6. Save the derived panel and hash.
7. Produce descriptive outputs.
8. Estimate the primary model.
9. Run comparative models and multiplicity control.
10. Run timing, scale, period and influence sensitivities.
11. Generate tables and figures.
12. Run final verification and create a result manifest.
13. Draft the manuscript only after outputs pass.

## 23. Change-control rule

If a locked requirement conflicts with the data or software, stop before substantive estimation, identify the exact conflict, document evidence and scientific consequences, and obtain approval before changing the design. Null or unattractive findings do not justify a change.

## 24. Final handoff status

**IMPLEMENTATION HANDOFF READY**

Next action: environment setup and implementation preflight.
