# Two-device HV length derivative: design controls

Candidate SHA256
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`
changes only original XM31 and XM33 from L0.5 to0.6µm in parent
`53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2`.
W1µm, AS/AD0.34µm², PS/PD2.68µm and every other source byte remain unchanged.
The separate source and generator are under
`candidates/bgr_loop24_qref4_r253p465_hv06/`; neither source is adopted.

The pinned public process specification states the3.3V/27°C HV-NMOS condition
for LG≥0.6µm. This derivative addresses that length condition only; it is not
a3.6V/125°C reliability solution or an invented lower-voltage operating rating.
The full physical layout, wiring CPEX and area/power qualification remain open.

## Stock diffusion applicability

`audit_short_hv_diffusion.py` instantiated two stock nmosHV W1µm/ng1 PCells only
in memory. [Audit](short_hv_diffusion_20260922_r1.json): **passed**. Both lengths
produce two exact0.34×1µm diffusion rectangles, area0.34µm² and full perimeter
2.68µm each. Normalized source/drain region XOR is empty. Gate area increases
0.5→0.6µm²; the drain shifts0.1µm and native bbox width1.72→1.82µm at2.04µm
height. Total native bbox increase is0.408µm² across the two devices, not a
legal-placement estimate. Polygon vertices are on the5nm drawing grid.

Pinned PDK commit84374023ee8b4b126bebbba67fcbada0a9c0ff0b, KLayout0.30.9;
native code/technology hashes are retained. No design GDS was saved, and this
was not full DRC/LVS or new PEX.

## Nominal sweep

[Nominal audit](short_hv_nominal_audit_20260922_r1.json): **passed**,34 points
−40…125°C. Simulated TC8.529822579ppm/°C, VREF25=1.04544958413V,
IPTAT25=4.106693993µA and I25=317.573550µA. Runtime20.581s under120s bound.
The input deck is byte-identical to the parent nominal deck. All2842 pre/post
temperature parameter strings match exactly; only the two expected L values
differ from the parent's2842 parameters. The0.6µm model readback is
`6.000000000000001e-7`m; an initial analysis compared it to a Python decimal
literal and failed on binary rounding. The corrected audit freezes the exact
reported strings without relaxing pre/post or non-target comparisons.
Maximum VREF difference from parent across temperature is0.544nV. The retained
temperature-limiter NaN warning is not erased by finite final data.

## Frozen-input startup controls

The wrapper preserves the original27°C/3V input ramps and numerical settings,
adding only one-thread setting and23 terminal-node exports. Source substitution
is separate. Removing those deck additions recovers each original input byte.
Run: `runs/bgr_loop24q4_hv06_startup2_20260922_r3/`.

|Ramp|Required endpoint|Result|Simulated observations|
|---|---:|---|---|
|1ms|3ms|passed|1627 rows; VREFend1.045457678V; IPTATend4.134102683µA; observed peak supply319.599087µA;15.766s runtime|
|100ms|300ms|failed|Aborted39.269494543ms,241 rows, despite solver exit0;7.573s runtime|

The slow ramp reports timestep-too-small, timestep2.5e-16s, at
`q.xbgr.xq76_u24.qnpn13g2`; temperature-limiter NaN is present. Its final partial
VREF is0.633535V and IPTAT0.173852µA, not a completed startup result. No longer
watchdog, tolerance change, retry ladder or acceptance waiver was attempted.
[Partial diagnostics](short_hv_startup_diagnostics_20260922_r3.json) preserve
original statuses and interval-limited terminal extrema.

Both data/terminal grids are finite, exactly equal and strictly increasing.
UIC explicitly skips an initial operating-point solution; supply stimulus is
zero at time zero but first saved points are20ns and2µs. There is no terminal
coverage or peak bound for the omitted initial intervals. Prepared r1/r2
records remain **not run**: a proposed first-saved-point=0 condition conflicted
with the original UIC fixture and was withdrawn before execution. No zero-time
row was fabricated. r3 checks the original positive-first-step bounds.

The fast-ramp level and observed HBT VCE checks passed. This is not high-rail,
high-temperature reliability, all-ramp convergence, physical fit or adoption.

## Exact source-only parent control

One parent-source100ms control uses the failed derivative's exact deck, init,
models, settings, UIC/time-grid criteria and300s watchdog. The copied source
alone reverts the two L changes; the mechanical equality gate passed. Evidence
is under `runs/bgr_loop24q4_parent_startup100ms_20260922_r1/`.
The parent control also **failed**, after7.515s, at39.269383643ms with241 finite
rows and the same Q76_u24 timestep-too-small/2.5e-16s diagnostic and temperature
limiter NaN. Its time grids passed the identical checks. Thus the slow-ramp
failure exists before the two L changes; it cannot be attributed solely to
that geometry-condition remedy. The abort times differ by about111ns, but
this is not full waveform parity or proof of a physical failure mechanism.
The shared enlarged-candidate startup/model trajectory remains unresolved.
No further retry or source mutation was performed. All original failures remain.

Pinned ngspice46/x86_64 image config SHA256
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
Exact commands, source/deck/model/OSDI hashes and output histories are in the
run manifests. No models/cards/tolerances changed. No MC or additional load
campaign was launched.
