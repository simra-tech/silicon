# Focused interface coupling contract

These are prospective engineering diagnostic gates, not added signed product
specifications or a claim of complete parasitic extraction. Electrical coupling
checks below are **not run**. Local clip preparation, extraction and independent
capacitor-network checks for ISENSE/clock have **passed**; broader context work
is in progress. Physical measurement for the numerical network check is
**not applicable**; actual silicon coupling measurements remain **not run**.

Delivered GDS SHA-256:
`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`.
The unchanged pinned KPEX 0.3.12 rules are used; individual manifests hash them.

| Victim / neighbor | Layer | Track x coordinates (µm), victim first | Shared y interval (µm) |
| --- | --- | --- | --- |
| ISENSE / comparator clock | Metal4 | 733.92 / 734.40 | 601.02–630.42 |
| VREF / DAC soft bit 5 | Metal2 | 732.00 / 731.52 | 653.94–768.60 |
| Buffered VREF / DAC hard bit 4 | Metal4 | 732.96 / 732.48 | 646.38–765.24 |
| IPTAT / ISENSE | Metal4 | 733.44 / 733.92 | 502.32–763.14 |

These are vertical routes. The cross-section's longitudinal midpoint is a y
coordinate, not an x coordinate. Initial helper preparation transposed the axes
and failed its target-presence assertion before extraction; its failed source
snapshot/log are retained. Corrected preparation checks both targets cross the
clip's longitudinal boundaries and verifies exact exported polygon XOR.

The local study fixes longitudinal length at 20 µm and tests transverse context
12, 24 and 48 µm. The prospectively declared convergence gate is ≤1% relative
change in every element of the reduced 2×2 capacitance matrix from 24 to 48 µm,
for both no-fill/actual-fill and grounded/floating-fill boundaries. Independent
ngspice AC checks must reproduce all matrix entries within 1e−25 F. This checks
the mathematical reduction, not the physical validity of grounding unknown
context conductors. No full-route capacitance is obtained simply by multiplying
a local midpoint result by route length. Endpoints, longitudinal context,
neighbor activity and outside-clip connectivity remain separate requirements.

Electrical evaluation must use actual source/load operating points and driving
impedance, source hashes and a zero-added-coupling control. The original
finite-load-step VREF droop is not an AC impedance characterization. Inject the
recorded clock waveform and actual DAC transitions; also test a separately
labeled deliberately aligned transition as a sensitivity. Do not treat a
configuration-only DAC wire as a continuously toggling clock, or quietly waive
configuration-time transients. Preserve arming, mask and threshold states.

Before examining electrical outcomes, reserve **50 µV shunt-equivalent** as a
diagnostic limit for incremental coupling-induced error at actual comparator
decision instants. This is half the smallest ±0.1 mV near-boundary displacement
requested by V05, not an allocated product tolerance or proof of the total
±10% threshold target. Use the simulated local transfer gain/divider ratio to
refer error to the shunt, not an assumed gain at every PVT point. Report continuous
saved peaks and settled values separately. Require unchanged correct decisions
for the separately specified trip/no-trip guards; retain ambiguity inside the
unqualified decision band. A passed incremental diagnostic cannot compensate
for a failed baseline decision, residual offset or total-threshold check.

IPTAT also feeds temperature/timing functions. Report induced bias-current,
oscillator-period and calibrated-temperature errors explicitly; no new absolute
temperature-error budget is invented here. The existing ±2 °C total requirement
and adopted calibration policy remain the system gate. Unknown source impedances,
aggressor amplitudes or omitted return paths prevent whole-interface acceptance.
