# Physical verification collector and scratch geometry trials

This record extends `P01_CLOSURE_20260921.md`. Its earlier “not run” entries
remain accurate for the earlier audit; the executions below are subsequent.
The delivered GDS and installed PDK have not been changed. All geometry
candidates are **non-production diagnostics** under `build/scratch`.

## Collector implementation

`blocks/g1_padring/flow/signoff/signoff.sh` now calls `signoff_runner.py`.
The runner uses a new output directory, preserves retained evidence with
SHA-256 hashes, persists an explicit status for each planned check, continues
independent checks after failures, and exits nonzero if any required check
failed or did not complete. Missing tools/timeouts are “not run”, with the
reason; a tool that exits zero without its acceptance evidence is “failed”.
DRC acceptance requires a valid KLayout report containing zero markers. LVS
requires the explicit comparison PASS signature in addition to process success.
Retained run metrics are labelled retained and cannot replace fresh final-GDS
checks. Full IO-inclusive LVS is explicitly “not run” in the collector because
a qualified full-IO procedure is not yet implemented.

Executed collection-only command:

```sh
G1_CPUS=2 flow/run.sh bash designs/g1-guardian/blocks/g1_padring/flow/signoff/signoff.sh assembly-1350 --collect-only --output designs/g1-guardian/review/audits/signoff-collector-20260921-r4
```

Result: **failed/incomplete, exit 1**, as required. Retained antenna, original
streamout XOR, Magic DRC and Netgen LVS failures are explicit. New checks are
all explicitly “not run”. This command tests collection and failure propagation;
it is not a fresh physical signoff. Retained hard DRC/density/routing/STA/critical-pin successes retain their
original, narrower scope. The later r5 collection corrects the prior grid
status to **failed**: raw VDDA `PSM-0069` overrides the aggregate zero metric. The manifest pins
the executed script hash; subsequent source changes require a new output name.

Four independent fixture tests pass (r5 additionally covers raw supply failure overriding a zero metric), covering continuation after process
failure, zero-exit DRC violations, missing reports, timeout, later success,
valid empty reports, invalid report roots and portable paths:

```sh
python3 -m unittest discover -s designs/g1-guardian/review/audits -p test_signoff_collector.py -v
```

Results: `signoff-collector-tests-20260921-r4.log`. The old collector's reports
remain untouched. Full execution of every collector check is **not run**.

## Geometry and reproduction

The base delivered GDS SHA-256 is
`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`.
Tool: KLayout 0.30.9, pinned EDA image
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
PDK: `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.
Every trial directory retains the exact generator snapshot, commands, hashes,
logs and unmodified stock-deck marker databases. Decks run sequentially with
two threads and 600-second watchdogs. A completed diagnostic command does not
mean its checks passed; check status is taken from `manifest.json`.

Trial 1 inserted the 60 missing recommended pad-exit polygons on their
corresponding TM1/TM2 layers. This cleared all Pad.fR markers but intruded into
the adjacent IO-cell TM2 spacing; the candidate is rejected.

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/pad-exit-20260921/generator.py --mode pad --work build/scratch/pad-exit-20260921-replay --report designs/g1-guardian/review/audits/pad-exit-20260921-replay
```

The actual original invocation used `geometry_candidates.py` and the output
names `pad-exit-20260921`; the snapshot above reproduces that exact version
without overwriting evidence. Full stock DRC completed in 255.66 seconds:
**failed, 58 TM2.b markers**, zero Pad.fR markers. Stock antenna completed in
133.94 seconds: **failed, 9 markers**, three each at Metal5, TopMetal1 and
TopMetal2. For example the inward extension reduces a north-edge TM2 gap to
1.5 µm between y=1202 and y=1200.5 µm.

Trial 2 moves all 24 bondpads 4 µm toward their nearest die edge. Top-level TM1
and TM2 cover the swept original/new bondpad area, maintaining overlap to the
existing stub while increasing the distance from the new opening to the
unchanged inward metal boundary. This changes bondpad centers and would
require a revised bonding map before production adoption.

The antenna trial duplicates the existing MP0 dummy in each `sg13g2_IOPadIn`,
translating its active/poly/implant/oxide/contact/M1 geometry by -5 µm locally
and joining its nwell to the existing nwell. MP0 has G/S/D/B all tied to VDD in
the stock CDL. This increases actual connected gate area by 2.0925 µm² per
input pad; it does not disconnect the functional receiver gate or waive an
antenna rule. Cell-local poly/contact/via/metal extraction verifies the new
gate, source, drain and existing well-tap metal are VDD. This connectivity
probe does not replace transistor LVS, well-resistance analysis or electrical
qualification. Exact windows and placement are in the candidate manifest.

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/geometry_candidates.py --mode pad_outward_dummy --work build/scratch/pad-outward-dummy-20260921 --report designs/g1-guardian/review/audits/pad-outward-dummy-20260921
```

Trial 2 stock full DRC completed in 244.67 seconds: **failed, 44 markers**
(1 AFil.c1, 27 AFil.c, 1 AFil.d, 1 GFil.d, 1 GFil.e, 3 M1.b,
10 M1Fil.c). All Pad.fR and TM2.b markers cleared. Remaining markers cluster
around the added dummy geometry and pre-existing assembled fill. Stock antenna
completed in 108.17 seconds: **passed, zero markers**. This supports the connected
VDD gate-area mechanism, but the candidate fails DRC and cannot be adopted.

Trial 3 retains trial 2's pad/device geometry and removes only 19 nearby
existing dummy-fill elements: datatype 22 on Activ, GatPoly and Metal1.
Affected top-level fill arrays are split into retained individual elements;
remote elements and all functional drawing layers are preserved. This resolves
the concrete fill collision rather than changing any rule. The exact removed
boxes are recorded in `pad-outward-dummy-clean-20260921/manifest.json`.

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/geometry_candidates.py --mode pad_outward_dummy_clean --work build/scratch/pad-outward-dummy-clean-20260921 --report designs/g1-guardian/review/audits/pad-outward-dummy-clean-20260921
```

Trial 3 stock full DRC completed in 210.01 seconds: **passed, zero markers**,
including both hard and recommended rules. Stock antenna **passed, zero markers**
in 127.82 seconds. Stock density **passed, zero markers** in 30.34 seconds.
The all-layer polygon comparison `fill_delta.json` proves that trial 3 changes
only removal of 3 Activ/22, 5 GatPoly/22 and 11 Metal1/22 polygons from trial 2;
removed areas are respectively 34.68, 35.00 and 33.50 µm². Every other polygon
layer is identical. Text labels are outside that comparison.

Exact-candidate core LVS **passed**, explicit stock comparison match, in
1153.79 seconds wrapper wall time. Its compressed LVSDB and extracted/reference
netlists are preserved in `pad-outward-dummy-clean-lvs-20260921/core_evidence`.
Comparison to the retained passing core input shows only the 19 removed fill
polygons; every other polygon layer is identical. Full IO-inclusive LVS **failed** after 1591.44 seconds: 52 matched circuit
pairs, 14 unmatched IO children, four unmatched corner/filler reference
cells and 11 skipped parents including the chip top. The 14 IO child names
match the retained stock-ring failure set. Evidence is in
`p01-full-io-normalized-20260921`; see `IO_TOPOLOGY_20260921.md`. Metal-only supply
isolation on the exact clean candidate also **passed**; its full log is retained. Parasitic extraction,
startup/power-sequence simulation and production adoption are **not run**. An antenna or DRC success alone cannot
close the independent baseline IO extraction/recognition/device mismatches.

## Scoped adoption requirements

A reviewable production implementation would change the local pad-placement
generator to the recorded outward centers, maintain the connecting TM1/TM2
stub geometry, and update the bonding coordinates. The added all-VDD device
must be represented explicitly in a local derived-cell schematic/CDL (or as a
matching parallel device), with an appropriate fill keepout before regeneration.
Editing only the GDS would intentionally leave a schematic/layout mismatch;
this diagnostic does not authorize or establish equivalence to the stock IO
CDL. The existing resistor-recognition and clamp/diode/substrate correspondence
failures also remain independent blockers. Required acceptance includes stock
hard/recommended DRC, density and antenna, matched full IO-inclusive LVS,
parasitic extraction, supply-sequence/electrical checks, and assembled-view
regressions on the final generated deliverable.

The source-generation proposal has now been executed separately in
`build/scratch/p01-adoption-20260921-r3`, with review artifacts in
`p01-adoption-20260921-r3/`. The helper and its adoption requirements are in
`blocks/g1_padring/flow/p01_adoption/README.md`. The full proposed snapshot has
zero polygon XOR against the checked candidate; no-fill metadata is present
only in the generated standalone local IO source for future regeneration.
`git apply --check` passes on the proposed config/RTL patch. The patch is
**not applied**, generated views are **not promoted**, and copied timing
is **unqualified**. The complete 24-pad coordinate delta is recorded.
