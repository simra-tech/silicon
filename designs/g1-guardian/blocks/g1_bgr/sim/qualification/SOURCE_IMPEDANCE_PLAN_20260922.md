# Loaded reference driving-point AC characterization

Status before execution: **not run**. This is a simulation-only V21a input
characterization, not layout/PEX adoption or a coupling acceptance verdict.

Freeze baseline BGR C-PEX from `runs/bgr_noise_20260921_01/pex.spice`
(SHA256 `72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77`).
Freeze SENSE and full TRIP from the retained
`g1_trip/sim/qualification/dac-actualbgr-reset-klu-pilot-20260922-a/`
fixture. The latter includes the actual conditioner, DAC strings, switches,
level shifters, hold capacitance and both comparators held reset. Raw VREF
drives the SENSE reference-buffer input; the DAC strings load `vref_buf`,
not raw VREF. IPTAT drives the SENSE diode-connected input and bias gates.
Use nominal (non-mismatch) pinned model corners, retaining source bytes and
explicit device parameters. This is not replay of the archived mismatch sample.

First tuple: typical, 3.3V analog/1.2V digital, 25C, 25mV shunt,
soft/hard codes153/254. Then, only after nominal fixture qualification,
slowcold (ss/wcs/-40C,3.0/1.08V) and fasthot
(ff/bcs/125C,3.6/1.32V). Original tight solver settings and KLU/rshunt are
retained; no cards or tolerances modified. The 3.3/3.6V short-channel BGR
HV-device model-scope concern remains unresolved by this characterization.

For each tuple, run an uninstrumented OP control, then independently inject
zero-DC, 1A small-signal AC current from ground into VREF and IPTAT.
Zero-volt sensors split BGR output/supply from unchanged actual loads.
All other independent sources have zero AC amplitude. Sweep0.1Hz–100MHz,
50points/decade (451points). The 1A is a linearized normalization, not a
finite physical perturbation. Export real/imaginary node voltages, BGR
output-branch currents and analog supply current. V(node)/1A is the loaded
driving-point impedance with the other output loaded; it is not an isolated
unloaded source resistance. Cross-port/ISENSE/DAC responses are transfers
per ampere of injected current. No arbitrary noise/coupling budget is adopted.

Prospective fixture qualification: exact frozen-source/model/runtime hashes;
finite OP and AC vectors; correct451point grid/endpoints; solver completion
without error/aborted analysis; instrumented versus uninstrumented DC
voltages within1uV and total analog current within1nA. Operational sanity:
VREF and buffered VREF0.9–1.2V, IPTAT input0–1.5V, BGR currentpositive,
IPTAT outputcurrentpositive. Fail closed before later tuples if any fixture
gate fails. Preserve all failures, including zero-exit analysis failures.

The T2F interface has PBIAS/PCASC/VREF but no IPTAT pin. Running T2F is
periodic, so stationary OP-AC is not its running impedance. T2F-loaded AC
and periodic impedance are **not run**; no invented direct IPTAT load.
SENSE/TRIP are frozen schematic sources, BGR capacitance-only PEX; routing
resistance, newly affected layout parasitics and clocked kickback are not
represented. These are explicit limitations, not passed coverage.

Command (pinned flow, single CPU6,4GiB reservation, fresh0.25GiB resource gate):

```sh
G1_CPUSET=6 G1_CPUS=1 G1_MEMORY=4g G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim/qualification flow/run.sh python3 run_source_impedance.py --run-id bgr_loaded_ac_nominal_20260922_r1 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --tuple nominal
```

Three sequential leaves per tuple,120s OP/300s AC watchdogs, anticipated
under5min and10MiB per tuple; maximum720s if all leaves approach watchdogs.

Approved follow-up before launch: after both nominal current ports pass,
one same-source shunt-voltage AC leaf (Vsh AC1V, current probe AC0), same
DC equivalence gates,300s CPU6. This supplies complex local ISENSE and
comparator differential-input gain for input referral; do not substitute an
ideal resistor-ratio gain. Root's50uV shunt-increment-at-decision criterion is
an engineering coupling diagnostic, not an AC-amplitude product allocation.
Use `--shunt-only-reference bgr_loaded_ac_nominal_20260922_r1` with a new ID.

## Completed characterization

All12 approved leaves pass numerical, finite451-point AC and per-tuple
DC-equivalence gates. Largest node difference is102.86nV and largest analog
current difference0.1891nA, versus the frozen1uV/1nA limits. Each shunt leaf
has byte-identical instrumented OP output to its same-tuple current probes.
The original prospective statement above is retained as chronology.

| Tuple | Low-frequency loaded VREF Z | Loaded IPTAT Z | BGR supply current | IPTAT current | Total analog current |
|---|---:|---:|---:|---:|---:|
|Typical25C,3.3V|87.7727kΩ|21.9230kΩ|21.8937uA|4.10686uA|1.04800mA|
|Slow−40C,3.0V|98.5535kΩ|24.8717kΩ|14.9244uA|2.82962uA|0.702868mA|
|Fast125C,3.6V|78.3193kΩ|20.3876kΩ|33.9759uA|6.25396uA|1.64659mA|

All entries are simulated; impedance entries use0.1Hz linearized response.
Current sensors include retained1TOhm numerical shunts; the pA raw VREF
sensor current should not be interpreted as a characterized gate-leakage model.
Digital supply current is not included in the total analog-current column.
These are mismatch-disabled selected-corner models, not random seed51001 replay.

Local shunt-to-comparator-differential gain is9.99408,9.99506,9.98946V/V
respectively. At typical low frequency, a raw VREF change refers to
−0.0289131V/V equivalent shunt at the soft input and−0.0479800V/V at the
hard input; this differs from the ISENSE-only+0.0481096V/V because the
actual DAC thresholds also move. IPTAT referral is strongly frequency- and
corner-dependent. High-frequency ratios increase as the local shunt transfer
rolls off; that is not itself a sampled-decision failure or an AC product limit.

`loaded_source_impedance_{nominal,slowcold,fasthot}_20260922_r1.json` retains
all451 complex voltage/current/admittance/decision-transfer points with exact
source/model/runtime/manifest and waveform hashes. The new
`loaded_source_impedance_3tuple_20260922_r1.{png,svg,json}` summarizes them.
Reproduce using `run_source_impedance.py`, then `analyze_source_impedance.py`,
then `plot_source_impedance.py`; each run/output refuses accidental overwrite.

The pre-existing short-channel BGR HV-voltage model-scope issue and OSDI
warnings in retained logs remain unresolved. Numerical fixture qualification
is not model-range/reliability sign-off. Running T2F, clocked comparator
decisions, actual route endpoints/new PEX, mismatch statistics and product
coupling acceptance remain **not run** in this stationary characterization.
