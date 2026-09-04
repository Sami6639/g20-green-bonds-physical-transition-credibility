# Verified Results Memo

Analysis date: 2026-09-04  
Primary sample: 19 G20 country members, 2006–2024, 361 country-years.  
Lag buffer: 2005.  
Primary exposure: annual recorded green-bond issuance divided by nominal GDP, expressed in basis points.  
Primary outcome: annual absolute fossil-electricity contraction.

## Descriptive evidence

- Positive recorded issuance appears in 186 country-years; 175 country-years contain no recorded issuance.
- Across all observations, fossil electricity contracts in 42.38% of country-years, renewable generation increases in 73.41%, coal contracts in 50.29% of eligible country-years, and coal contracts without a combined gas-or-oil increase in 21.93%.
- The renewable-addition rate exceeds the fossil-contraction rate by 31.02 percentage points (20,000-draw country-cluster bootstrap 95% interval: 20.50–42.11 pp).
- Raw outcome frequencies are more favorable in positive-issuance years: 53.76% versus 30.29% for fossil contraction and 81.72% versus 64.57% for renewable addition. These comparisons are descriptive and confounded by country composition and calendar time.

## Fixed-effects evidence

The country- and year-fixed-effects linear probability models use CRV3 cluster-jackknife standard errors and t(G−1) inference. Coefficients below are converted to percentage-point changes in outcome probability per 10-basis-point increase in issuance/GDP.

| Outcome | Effect per 10 bp | 95% CI | p-value | Interpretation |
|---|---:|---:|---:|---|
| Fossil contraction | −1.56 pp | −3.53 to 0.42 | 0.115 | No positive within-country alignment; interval includes zero |
| Renewable addition | −3.66 pp | −5.00 to −2.32 | <0.001 | Negative conditional association; not a causal adverse effect |
| Coal contraction | −1.40 pp | −3.12 to 0.32 | 0.104 | No positive alignment after controls |
| Unoffset coal contraction | −0.90 pp | −2.46 to 0.66 | 0.241 | No positive alignment after controls |

The primary fossil-contraction wild-cluster-bootstrap-t p-value is 0.124 (9,999 replications, Webb weights, WCR33). Holm adjustment across the three secondary outcomes leaves only the negative renewable-addition association statistically detectable.

## Robustness

- The primary issuance-intensity coefficient remains negative under 0.10% and 0.25% material-change thresholds, a one-year lag, per-capita scaling, the 2016–2024 window, and exclusion of pre-market-entry country-years.
- The sign is negative in all 19 leave-one-country-out re-estimations; the range is −0.001881 to −0.000984 probability units per basis point.
- A binary positive-issuance indicator is positive but imprecise after country and year fixed effects (9.50 pp; 95% CI −11.54 to 30.55).
- Two sensitivity specifications drop two singleton fixed effects automatically; their estimates are retained only as secondary checks and this software behavior must be disclosed.

## Interpretation lock

1. The results do not identify the causal effect of green bonds on electricity systems.
2. No domestic project-allocation link is observed.
3. The contrast between favorable raw active-year frequencies and non-positive within-country issuance-intensity estimates is substantively central: market presence and issuance scale are not equivalent physical signals.
4. The defensible conclusion is that recorded green-bond volume, by itself, is not a sufficient jurisdiction-level proxy for contemporaneous physical fossil exit in G20 electricity systems.
