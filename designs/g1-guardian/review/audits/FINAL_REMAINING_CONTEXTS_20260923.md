# Five additional final-route contexts

Four selected midpoint contexts passed the original every-entry 1% transverse
convergence gate. The SENSE input pair failed. All 120 independent capacitor-network
AC checks passed their original `1e-25 F` threshold. This does not qualify full
routes, actual switching response, or threshold/temperature accuracy.

The batch took 234.636 seconds, serial on one CPU. It used the same final filled
GDS `4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299`
and audited DEF/geometry as the [initial final-route context](FINAL_FILLED_CONTEXT_20260923.md).
Pinned IHP revision `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9,
KPEX 0.3.12 and ngspice 46 are unchanged. No geometry, model or rule deck changed.

Each source-bound clip is 20 µm long, centered on the selected shared interval,
with transverse widths of 12, 24 and 48 µm. No-fill/actual-fill geometry is held
exactly; fill is considered grounded or floating, with other clipped conductors
and substrate grounded. Below-M1 geometry, Active/poly fill and devices are omitted.

| Pair | Layer; full shared interval | Center separation | Maximum relative 24→48 change | Context status |
| --- | --- | ---: | ---: | --- |
| ISENSE / VREF | M5; 76.80 µm | 0.42 µm | 0.0055692% | Passed |
| Buffered VREF / hard-DAC bit 2 | M5; 75.36 µm | 0.42 µm | 0.0098355% | Passed |
| IPTAT / ISENSE | M4; 72.96 µm | 0.48 µm | 0.0001284% | Passed |
| SENSE N / P | M4; 85.26 µm | 11.04 µm | 5.49947% among nonzero denominators | **Failed** |
| VREF / PCASC | M3; 184.80 µm | 0.42 µm | 0.0001160% | Passed |

These are not full-interval extractions: only the central 20 µm was extracted.
No multiplication by total route length is justified.

## SENSE failure retained

The original checker rejected a zero denominator before writing a context JSON.
Its failed command and traceback are retained. A separate read-only entry report
then evaluated all entries without changing the original formula or threshold.
Zero/zero relative entries remain undefined/failed, not silently accepted under
a new absolute tolerance. The nonzero entries also show a genuine failure of
the existing 1% convergence gate: maximum 5.49947%.

At 48 µm width the actual-floating-fill matrix, simulated in fF, is
`[[2.9074118735, -0.0023561568], [-0.0023561568, 2.8378502778]]`.
The corresponding 24 µm matrix is
`[[2.8961014244, -0.0024394088], [-0.0024394088, 2.7486376091]]`.
No-fill and grounded-fill mutual terms are zero in this extracted model;
this is not proof of physically zero long-range coupling.

| Remaining check | Status |
| --- | --- |
| Original context-entry reporter positive/rejection controls | Passed, five tests |
| SENSE context convergence at the existing width | Failed, retained |
| Larger context and longitudinal/end/branch coverage | Not run |
| Actual-source electrical coupling, complete RC and power acceptance | Not run |
| Random seed for deterministic capacitor-network analysis | Not applicable |

[Portable evidence](final-remaining-context-evidence-20260923-r1/export_manifest.json)
records exact commands, original/exported hashes, extraction results, all 120
AC checks, and the failed and diagnostic SENSE reports. Completed initial
VREF/clock extraction and fullchip GDS are not redundantly exported.
