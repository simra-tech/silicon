# GATE manual-isolation timestep diagnostic

This is a diagnostic of the original IO-first/open-switch fixture. It does
not qualify the 16 µs isolation or safety requirement. The frozen original
fixture SHA-256 is `d55c4b9fd10572478981b652b7cda2b6e14f6247303d9850dd3ba8fbc9b86743`.
`prepare_probe.py` verifies that hash and holds its entire circuit, includes,
sources, PDK, models, and `.option` line. It changes only output control:
ngspice-46 batch `-r` with a dot `.tran` streams a binary rawfile. The original
1 ns print/maximum step and 120 s run bound are retained. The method is
documented in the [ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf),
section “Rawfile”. The prior `.control tran` form did not stream with `-r` in
the pinned runtime; a tiny local RC control demonstrated this distinction.

Two 1.2 µs prefix controls finished under the same source and solver options.
The original-style `wrdata` prefix and the `-r` binary prefix matched exactly
for 1,211 time points and nine common vectors. The `.save all` prefix matched
the same text prefix exactly across 24 common vectors and 1,211 points.
These are output-method controls, not substitutes for the 16 µs test.

Both 16 µs raw diagnostics again hit the unchanged 120 s bound. The selected
19-vector rawfile reached 1.376328308105382 µs; `.save all` (868 variables)
reached 1.3763334503172933 µs with 5,394 complete saved points. The original
nonstreaming run reported about 1.37643 µs. In the all-vector result, 4,002
accepted steps were below 10 ps, beginning near 1.375992 µs; 2,710 were below
0.1 ps, and the last 1,000 points advanced only 48.599 ps. The smallest
last-1,000 step was 15.259 fs. This directly confirms an accepted-timestep
collapse, not a host-capacity stall.

The last 1,000 points show numerical chatter concentrated in the real TI FET
subcircuit (`XFET`): nodes `xfet.4`, `.7`, `.10` and `.6`, `.8`, `.9`, `.12`,
`.13` each reverse saved-point direction 781 times within approximately
1.8 nV. By comparison, `v(xpe.xi0.net7)` and `v(vdda)` each move smoothly by
about 80 µV in that window. The raw trace localizes the strongest visible
chatter to `XFET`; it does not prove that this subcircuit alone causes the
solver step selection. The pinned TI model contains drain/source parasitic
inductors `LDD=0.05 nH`, `LSS=0.20 nH`, milliohm-scale series resistors and
nonlinear capacitances. This topology is a plausible stiffness mechanism,
but no component has been removed, fitted, or blamed as a proven cause.

Evidence is retained under the simulation bulk root in
`gate-manual-stream-20260923-r1/{control_prefix,raw_prefix,raw_prefix_all,raw_full,raw_full_all}`;
the two full run receipts remain in the local verification store with their
timeout statuses. `analyze_stream.py` checks finite strictly increasing
saved time, parses complete binary rows even after termination, compares the
prefix, and reports tail behavior. `prepare_fet_sensitivity.py` made two
separate exact-inverse, one-line TI model perturbations, both explicitly
nonphysical: `RDP` 0.19 → 1.9 mΩ and `LDD` 0.05 → 0.5 nH. The circuit source,
stimulus and solver options otherwise remained held; the original model and
failed run were retained. Both 120 s runs still collapsed near the same
simulated time: 1.3763332366942465 µs (`RDP10`) and 1.3762929534911428 µs
(`LDD10`), with minimum last-1,000 steps again 15.259 fs. These tests rule
out either single tenfold perturbation as a numerical remedy. They do not
isolate a unique offending element or justify a vendor-model change.

`probe_first_order.py` subsequently held the circuit, included files, and all
tolerances fixed, changing only Gear integration to `maxord=1`. It also timed
out after 120 s: 5,068 saved points reached 1.3761899854199562 µs. Exact inverse
and before/after include hashes passed; solver endpoint failed. First-order
integration does not remedy this stall. Its bulk evidence is
`gate-first-order-20260923-r1`. Integration-order convergence remains not run.

`probe_fet_absent.py` prepares a separate single-instance deletion diagnostic:
the external `XFET` instance alone is removed, with original solver settings
and every other circuit element held. This is deliberately not a physical
board model and cannot establish safety or qualify a replacement FET model.
It timed out at 1.3763239288329242 µs (5,171 points). Independently replacing
only the EN input pad with an ideal zero-volt EN-core source also timed out,
at 1.3763223266600703 µs (5,240 points). Thus the stall can occur without the
external FET, and removing the EN-pad path alone is not a remedy. Neither
altered circuit is an electrical acceptance model.

`probe_pad_only.py` constructs smaller diagnostic fixtures: one output pad,
ideal zero-volt core drive, 20 pF output load, and the original decoupled
rail ramps, includes, temperature and solver options. These are not the
original load or complete chip. All runs retain the 120 s bound.

| Diagnostic | Endpoint | Result |
|---|---:|---|
| Explicit-bulk 30 mA pad alone | 16 µs, 16,024 points | Passed numerical endpoint in 18.762 s |
| Explicit-bulk 4 mA pad alone | 1.375412331 µs, 13,880 points | Failed: timeout |
| 4 mA, tighter relative/absolute tolerances | 1.375331226 µs, 11,592 points | Failed: timeout |
| 4 mA, trapezoidal integration | 1.375285812 µs, 10,262 points | Failed: timeout |
| Original six-pin 4 mA source with global substrate tie | 1.375412575 µs, 13,887 points | Failed: timeout |

The tighter case uses `reltol=0.001 abstol=1e-12 vntol=1e-6 chgtol=1e-15`;
the trapezoidal case changes only `method=gear` to `method=trap` relative to
the isolated-pad baseline. `audit_pad_variants.py` independently passed exact
emitted-deck inverses and rejected a deliberately changed output capacitance
for both cases. Included files remained hash-identical before/after each run.
The native-source control selects the original library definitions, whose
unchanged prefix is separately established; it is not a source-interface
reversion for the design. These observations reproduce the stall in a smaller
pad fixture, but do not establish an upstream defect or a physical remedy.

Bulk summaries and raw traces are retained in `gate-pad-only-{30mA,4mA}-20260923-r1`,
`gate-pad-tight-4mA-20260923-r1`, `gate-pad-trap-4mA-20260923-r1`, and
`gate-pad-native-4mA-20260923-r1`. The two deletion controls are retained in
`gate-fet-absent-20260923-r1` and `gate-en-pad-absent-20260923-r1`.
The original full 16 µs electrical criteria, missing-core/closed-switch
controls, hardware checks, and safety acceptance are **not run**.
