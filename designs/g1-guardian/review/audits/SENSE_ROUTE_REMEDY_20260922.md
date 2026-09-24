# Isolated SENSE input-route candidate

An unpromoted scratch candidate replaces the assembled P/N input routes, whose prior nominal resistance model failed the 19.9 V/V gain criterion. The delivered GDS and earlier pad/dummy candidate are unchanged. This route change does not resize SENSE devices.

Initial diagnostic candidate: `build/scratch/sense-route-remedy-20260922-r3/g1_chip_top.gds`, SHA-256 `7be3798b2722b1706e9b0f44c8b49fefc85f2a1b98c814428798e6ec59448bec`. Source is the earlier unpromoted pad/dummy candidate, SHA-256 `2d895efbb0e1c35ed7c891d376b010e041005d731ecd6d5448d872adfe55c9ca`.

After runtime identity qualification, regeneration under pinned KLayout 0.30.9 produced `build/scratch/sense-route-remedy-20260922-pinned-r1/g1_chip_top.gds`, SHA-256 `af9ac30034c8c11e09d1f24f732f3476c5653fb95eaa0b67f214c2e14c56f76d`. Whole-layout nontext polygon XOR against the initial 0.30.8 candidate is zero on every layer, and the conductor probes passed again. This establishes geometry parity; it is not extraction or simulation parity.

| Input | M3 width | M4 track / width | Via3 arrays | Fixed LEF R estimate | LEF ground C estimate |
|---|---:|---:|---:|---:|---:|
| P | 1.0 µm | x=1024.5 µm / 0.5 µm | two 2×2 arrays | 20.51836 Ω | 7.2244 fF |
| N | 1.0 µm | x=1021.0 µm / 2.5 µm | two 2×2 arrays | 20.587576 Ω | 20.9549 fF |

Each array has four 0.19 µm cuts on 0.41 µm pitch, with 0.05 µm drawn enclosure on both metals. These dimensions were selected from the unchanged stock rule definitions and the pinned stock hard/recommended DRC passed with zero markers. The estimated branch mismatch is 0.069216 Ω. R uses 0.103 Ω/square and ideal parallel 20 Ω cuts. Current crowding, spreading, junction corrections, terminal access, process and temperature variation are omitted. Ground C uses the prior LEF area/edge coefficients; it excludes coupling and actual floating fill. Capacitance remains unequal and requires dynamic evaluation.

Resistance-source clarification: historical run manifests call this a “nominal geometry estimate,” but these LEF coefficients equal the pinned process specification's **maximum reference-condition values**, not its targets. Section 2.13 gives M2–5 sheet resistance min/target/max 0.073/0.088/0.103 Ω/square; section 2.14 gives Via1–4 resistance 5/9/20 Ω/cut. Source PDF revision 1.2, SHA-256 `974d505886ee62932a50c52c22fbc290db4a70d8a7ce129c0ca8d7934aee160e`, pages 14–15. Original source manifests and simulation values are preserved. The target metal temperature coefficient of 3500 ppm/K is not a guaranteed hot-resistance bound; via temperature coefficients are not specified in that table. The 2× model remains a diagnostic stress, not a foundry process/temperature bound.

The independent geometry audit passed on the saved candidate: each pad probe connects to its respective macro pin and new M4 track; P and N are distinct and separate from the sampled supply conductors. This uses physical metal/via tracing without label-based or virtual merging. It is not transistor LVS or an exhaustive terminal audit. Whole-layout nontext polygon XOR changes exactly M3/Via3/M4 drawing and M3/M4 fill. All other nontext layers are identical to the source. The only removed fill is one 16 µm² polygon on each of M3 and M4. Affected fill is flattened at the top level; remaining polygon geometry is unchanged.

| Check | Status |
|---|---|
| Scratch geometry generation | passed, KLayout 0.30.8 |
| Whole-layout polygon XOR and selected conductor probes | passed, KLayout 0.30.8 |
| Pinned KLayout 0.30.9 geometry parity and selected conductor probes | passed |
| Stock hard/recommended DRC | passed; zero markers, 365.496 s |
| Stock antenna | passed; zero markers, 121.207 s |
| Stock density | passed; zero markers, 43.609 s |
| Core LVS | passed; explicit stock comparison match, 221.204 s |
| IO-inclusive LVS | not run; prior independent IO-LVS failure remains |
| Local extracted coupling and fill network reduction | passed; fixed-window diagnostic, eight AC checks |
| Extracted resistance and whole-route fill convergence | not run |
| Candidate 27-point route-resistance electrical anchor | passed; scoped nominal gain check |
| Nominal route-R/C AC sensitivity | passed; nine scoped fixtures, 18 AC sweeps |
| Fixed-LEF-R 108-tuple PVT anchor | gain passed; strict zero-R exact-parity gate failed at five tuples |
| Temperature-dependent route R, route-C PVT and transient response | not run |
| Production adoption | not run |

Generation failures r1 (KLayout Box API mismatch) and r2 (incorrect assumed via cell prefix) are preserved with source snapshots and failure records; neither wrote candidate GDS. r3 uses the observed `VIA_Via3_XY` cell name and passed the independent geometry audit. New evidence occupies approximately 61 MiB.

The first candidate core comparison failed because the core-only view placed SENSE labels at the obsolete DEF route midpoints, outside the new M4 tracks. All 52 circuit pairs matched, but stock top-port checking correctly failed. That run is retained in `sense-route-remedy-core-lvs-20260922-r1/`. The optional manifest-bound label override validates the exact GDS hash and actual M4 containment, then changes only generated verification-view text. A fresh run in `sense-route-remedy-core-lvs-20260922-r2/` explicitly passed. Independent whole-core nontext polygon XOR between both views is zero; reference CDL SHA-256 is identical, `70f0a6b1a107a9252fac29d55c9af8b128fff0f4c71e657e882229a639674ea5`. Neither physical candidate GDS nor source reference was changed. Full IO-inclusive LVS is still separately unresolved.

Reproduction in a qualified environment, using fresh output paths:

```sh
python3 designs/g1-guardian/review/audits/prepare_sense_route_remedy.py --output build/scratch/sense-route-remedy-NEW
python3 designs/g1-guardian/review/audits/audit_sense_route_remedy.py build/scratch/sense-route-remedy-NEW/g1_chip_top.gds --output build/scratch/sense-route-remedy-NEW/geometry_audit.json
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/run_sense_input_route_anchor.py --output designs/g1-guardian/review/audits/sense-route-remedy-anchor-NEW --candidate-manifest build/scratch/sense-route-remedy-NEW/manifest.json
```

The electrical command completed under the pinned runtime in `sense-route-remedy-anchor-20260922-r1/`, using the candidate's explicit P/N estimates at scales 0/1/2 and preserving nine operating points at each scale. All 27 points completed. The zero-R control exactly reproduces all seven original printed vectors at every point. The [acceptance record](sense-route-remedy-anchor-20260922-r1/acceptance.json) checks gain 19.9–20.1 V/V at all three common modes.

| Route-R scale | Simulated gain range V/V | CM output span at 25 mV shunt |
|---|---:|---:|
| 0 | 19.98798–19.98810 | 0.06 mV |
| 1 | 19.94666–19.94678 | 0.06 mV |
| 2 | 19.90552–19.90574 | 0.06 mV |

The prior baseline geometry model produced gain 19.71696 V/V at CM=0 and a 2.34 mV common-mode output span. The candidate resolves that demonstrated nominal resistance-model failure. The 0.06 mV spans use six-significant-digit printed data; they are descriptive, not a separately qualified CMRR limit. Scaling is a diagnostic sensitivity, not a physical bound. Actual BGR bias, input-pad capacitance, process/temperature resistance variation, full-route extracted coupling and transient response remain **not run** for this route candidate.

## Frozen 108-tuple fixed-resistance PVT anchor

Both shards completed under the pinned runtime: 108 MOS/resistor/supply/temperature tuples × three route-R scales × three common modes × three shunt values = 2,916 operating points. The grid is MOS TT/SS/FF, resistor typ/bcs/wcs, VDDA 3.0/3.3/3.6 V, and −40/27/85/125 °C, with cap_typ. The source is the unchanged baseline SENSE schematic, not a resized candidate. Rail/VREF/PTAT sources remain ideal; route resistances stay fixed at the LEF-based values at every temperature.

| Route-R scale | Numerical completion | Simulated gain range V/V | Tuples failing 19.9–20.1 V/V |
|---|---|---:|---:|
| 0 | passed, 972 OP | 19.97770–19.99074 | 0/108 |
| 1 | passed, 972 OP | 19.93226–19.95674 | 0/108 |
| 2, diagnostic | passed, 972 OP | 19.88690–19.91612 | 39/108 |

The [strict merged record](sense-route-remedy-pvt-merged-20260922-r1.json) is **failed**, not waived: 103/108 zero-R tuples reproduce all seven original printed vectors exactly; five do not. Maximum differences are 3 µV at ISENSE, 10 µV at VPED, 1 µV at an internal OTA input and 1 nA in supply current. The zero-R fixture inserts two zero-volt sources and renames the DUT input nodes, which is electrically equivalent in the ideal circuit but changes the numerical matrix.

A separate [exact-deck diagnostic](sense-zero-route-parity-probe-20260922-r1/summary.json) ran the untouched original source decks at all five affected corners. All five exactly reproduced their historical baseline vectors; all five repeated inserted-zero-source decks exactly reproduced the corresponding PVT vectors. This distinguishes the reproducible fixture-topology effect from host/source parity drift. At that stage, numerical-equivalence acceptance with a nonzero tolerance was **not run**; no original tolerance or failure was retroactively changed. Gain results above remain descriptive completed simulations, not promotion approval.

Subsequent, separately contracted [tight-solver equivalence](sense-zero-route-equivalence-20260922-r1/summary.json) **passed** all five pairs/ten leaves/90 OP. Before launch, the [new engineering contract](sense-zero-route-equivalence-contract-20260922-r1.json) froze voltage difference ≤5 µV, current difference ≤max(1 pA, 1e-4×absolute reference current), and gain difference <0.001 V/V. Both fixtures used reltol=1e-7, vntol=1e-10, abstol=1e-15, inherited gmin=1e-13 and 17-significant-digit exports. Maximum voltage difference was 9.81 pV, maximum gain difference 1.97e-10 V/V, and maximum current-difference/limit ratio 1.13e-7. The complete pinned model tree and physical source hashes were identical before/after. This supports numerical equivalence of the two ideal-zero-R fixtures under tighter solving; the original exact-parity failure remains unchanged. A 108-tuple tight-solver expansion subsequently started under its own frozen contract; no route adoption is implied.

The first tight expansion completed 38 passing tuples before its supervisor received external SIGTERM on the next source leaf after 4.44 seconds (four of nine OP rows). This was not its 120-second watchdog or an observed gain failure; the signal sender is unknown. The original terminal-failed summary and interrupted leaf are retained. After absence of the old process tree and a fresh resource check, an immutable continuation restarted that incomplete tuple and the remaining 69, with identical solver settings, contract, source decks, model tree, fixed route resistances and gain bounds.

The [strict final merge](sense-route-pvt-tight-merged-20260922-r1.json) **passed** all 108 tuples, 324 complete leaves and 2,916 OP points. It verifies every accepted deck/run/source/contract binding and preserves the original interruption record. Fixed-R candidate gain ranges from 19.93220496 to 19.95331936 V/V, within the unchanged 19.9–20.1 criterion. Zero-R equivalence maxima are 14.9962 nV, 6.55e-9 V/V gain difference, and 7.55e-6 of the allowed current-difference limit. Raw zero-shunt ISENSE−VPED offsets span −2.53542 to −1.11920 mV; they are retained as observations, not a new offset waiver. All per-CM gain, offset, midpoint-linearity and supply-current observations are included.

This closes the focused fixed-LEF-R/tight-numerics gate for SENSE candidate `af9ac300...`, not the later priority21 via candidate or gm4 circuitry. The LEF values remain reference-condition table maxima, not guaranteed hot-metal/via corner bounds. Full coupled RC, applicable hot/lifetime current margin, full IO-inclusive LVS and production promotion remain unqualified. The original five exact-parity mismatches and 39 two-times-R diagnostic gain failures are unchanged.

Commands used `G1_CPUS=1 G1_CPUSET=3` and `7` for the respective shards, with `flow/run.sh` and `check_sense_route_pvt.py --manifest build/scratch/sense-route-remedy-20260922-pinned-r1/manifest.json --output ... --shard 0|1 --shards 2`. Each leaf had a 120 s watchdog, finite/unique-row checks and an explicit completion marker. Source/deck hashes, exact offsets, original failures and logs are retained in `sense-route-remedy-pvt-shard0-20260922-r1/` and `sense-route-remedy-pvt-shard1-20260922-r1/`. `merge_sense_route_pvt.py` independently recomputes gain and verifies complete, disjoint coverage.

## Local coupling diagnostic

The exact candidate metal/via geometry in the same fixed window `[1016,468,1028,488]` µm as the delivered-layout pilot was extracted with the unchanged KPEX 0.3.12 IHP 2.5D CC deck. Candidate provenance binds the GDS SHA-256 and new P/N track centers; round-trip clipping XOR is zero. The no-fill graph contains nine capacitors/five nets; actual fill contains 389 capacitors/61 nets, including 56 fill nodes. Context conductors and substrate are treated as grounded boundary conditions, not claimed actual chip net identities.

| Fill condition | P ground equivalent fF | N ground equivalent fF | P–N mutual fF |
|---|---:|---:|---:|
| No fill | 1.490446 | 2.981410 | 0.494271 |
| Actual fill, grounded | 2.363705 | 6.184477 | 0.494271 |
| Actual fill, floating | 1.887071 | 4.290896 | 0.804981 |

The floating reduction conserves zero small-signal fill charge; maximum residual is 3.94e-31 F. All eight independently generated ngspice AC checks passed the 1e-25 F comparison tolerance. The delivered-layout pilot's mutual values were 3.487750 fF without fill and 3.636670 fF with actual floating fill. Candidate mutual coupling is lower in this window, while ground-capacitance asymmetry increases. Neither result bounds the whole route or establishes circuit dynamic performance. Devices and outside-window conductor continuation are absent; longitudinal/full-route convergence remains **not run**.

Evidence: `sense-route-remedy-fill-clip-20260922-r1/`, `sense-route-remedy-fill-pex-20260922-r1/`, and [reduction](sense-route-remedy-fill-analysis-20260922-r1/summary.json) / [independent AC checks](sense-route-remedy-fill-analysis-20260922-r1/ac_checks.json). Commands were run sequentially using `G1_CPUS=1 G1_CPUSET=3 G1_MEMORY=3g flow/run.sh` and fresh outputs:

```sh
python3 designs/g1-guardian/review/audits/prepare_fill_clip.py --gds build/scratch/sense-route-remedy-20260922-pinned-r1/g1_chip_top.gds --route-manifest build/scratch/sense-route-remedy-20260922-pinned-r1/manifest.json --output designs/g1-guardian/review/audits/sense-route-remedy-fill-clip-NEW
python3 designs/g1-guardian/review/audits/run_fill_clip_pex.py --clip designs/g1-guardian/review/audits/sense-route-remedy-fill-clip-NEW --output designs/g1-guardian/review/audits/sense-route-remedy-fill-pex-NEW
python3 designs/g1-guardian/review/audits/analyze_fill_clip.py --input designs/g1-guardian/review/audits/sense-route-remedy-fill-pex-NEW --output designs/g1-guardian/review/audits/sense-route-remedy-fill-analysis-NEW
python3 designs/g1-guardian/review/audits/check_fill_clip_ac.py designs/g1-guardian/review/audits/sense-route-remedy-fill-analysis-NEW
```

### Transverse-context sensitivity

`check_sense_clip_convergence.py` repeats the exact candidate extraction with 24 and 48 µm window widths centered at x=1022 µm, keeping y=468–488 µm fixed. Both completed, including all 16 capacitor-network AC checks. The added context conductors remain explicit grounded boundary assumptions. No implicit electrical-net identities are assigned to them.

| Window width µm | Floating-fill P ground fF | N ground fF | Mutual fF |
|---|---:|---:|---:|
| 12 | 1.887071 | 4.290896 | 0.804981 |
| 24 | 1.978982 | 4.365348 | 0.798163 |
| 48 | 1.979050 | 4.365986 | 0.798119 |

The 24→48 µm changes are 0.00342%, 0.01463%, and −0.00559%, respectively. This demonstrates small transverse-context sensitivity for this fixed-length local extraction, not longitudinal or whole-route convergence. Evidence: [context ladder](sense-route-remedy-clip-convergence-20260922-r1/summary.json).

### Circuit AC sensitivity with explicit source impedance

`check_sense_route_ac.py` completed nine fixtures: three route models (R-only control, the 48 µm local floating-fill capacitance network, and whole-route LEF ground-capacitance estimates) at 0/1/10 Ω assumed resistance per Kelvin lead. The source is the declared 25 mΩ shunt at 1 A, represented by a Norton current source and physical shunt resistance. The 0 Ω lead case is the existing ideal-Kelvin assumption; 1/10 Ω cases are sensitivities, not specified board impedances or guaranteed bounds. Each route is represented by equal half-resistors around a lumped midpoint capacitance network. These models do not substitute for distributed extraction.

All 18 differential/common-mode AC sweeps completed with 201 finite points from 1 kHz to 100 MHz. Conditions are TT, 27 °C, 3.3 V, 25 mV shunt, true average CM=0, ideal rails/VREF/PTAT, and the baseline schematic SENSE/load. No pad, package, actual BGR, mismatch, or process/temperature qualification is implied. The first sampled −3 dB crossing lies in 3.981–4.217 MHz for every case. Simulated 1 kHz differential gain is 19.94691/19.94491/19.92693 V/V for lead resistance 0/1/10 Ω per branch.

| Model relative to same-lead R-only control | Lead Ω/branch | Maximum complex differential-H change through 10 MHz, µV/V | Common-mode-H change, µV/V |
|---|---:|---:|---:|
| Local 48 µm clip C | 0 | 14.38 | 9.61 |
| Whole-route LEF ground-C estimate | 0 | 29.06 | 55.28 |
| Local 48 µm clip C | 10 | 28.37 | 18.95 |
| Whole-route LEF ground-C estimate | 10 | 57.36 | 108.98 |

The tested capacitance asymmetry has a small incremental linearized response in these source fixtures. This does not bound large-signal common-mode disturbances, unknown board filters or coupling outside the clip. Raw decks, logs, complex transfer arrays and [comparisons](sense-route-remedy-ac-20260922-r1/comparisons.json) are retained in `sense-route-remedy-ac-20260922-r1/`.
