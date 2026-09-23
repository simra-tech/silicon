# Matched solver characterization

Nine simulated controls completed with the unchanged 586 source, model cards,
seed/draw, 32 µs endpoint and original watchdogs. Only the declared KLU solver
selector changed relative to each SPARSE reference. This is characterization,
not solver adoption or release of an adverse population.

Three corner replay/repeat pairs passed the full 3,180-parameter identity
checks. Each independent same-KLU repeat was byte-exact, including its time
grid. Every SPARSE-versus-KLU exact-wave and exact-grid comparison failed and
remains explicitly failed.

| Corner | SPARSE / KLU replay time (s) | Frequency difference (ppm) | Rising-edge count, both | Maximum paired edge difference (ps) |
|---|---:|---:|---:|---:|
| Typical | 370.39 / 385.34 | +0.5744 | 48 | 25.864 |
| Slow | 260.13 / 270.84 | +17.9645 | 37 | 229.478 |
| Fast | 466.18 / 380.67 | −26.0654 | 59 | 666.800 |

Edges are interpolated actual 0.6 V rising crossings, paired by index. Whole-wave
union-grid differences and all thirteen original columns are retained in the
JSON reports. Neither these descriptive differences nor exact KLU repeatability
waive the original SPARSE comparison failures. The earlier 19× improvement on
the failed fast-seed prefix does not generalize to these controls.

The paired typical 100/−40/125 °C controls also passed all 3,180 parameters,
finite endpoint, positive frequency and original 1.6 V HBT external-VCE checks.
They took 364.72/269.64/391.55 s. Their SPARSE exact-wave/grid comparisons failed;
corresponding rising-edge counts were 58/37/62 and maximum paired differences
147.926/392.139/415.825 ps. Same-instance temperature-return controls are a
separate, in-progress gate; these three controls do not establish return
equality or the complete mismatch qualification.

Original typical-population 600 s failures remain in the denominator. New
samples 74143/74144/74145 finished all four planned attempts but have numerical
failures at 100/125/125 °C. The latter two continued advancing throughout the
final recorded minute, using approximately 98% process CPU-to-wall time.
Their conditional linear endpoint forecasts were approximately 54/53 further
seconds; this is host telemetry, not saved-wave completion, a recovery
authorization or an accuracy result. No retries or population solver changes
are part of this milestone.

Machine-independent compact evidence is under
`portable_evidence/t2f586-klu-matched-temperature-20260923/`; original bulk
artifacts remain bound by logical run IDs and hashes. The matched-control,
event-comparison, and timeout-progress JSON reports retain exact outcomes and
their source/analyzer identities.
