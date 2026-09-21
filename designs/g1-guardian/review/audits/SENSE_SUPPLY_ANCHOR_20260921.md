# SENSE transistor-level supply/return resistance anchor

All **54 selected DC operating points** solve and their 18 endpoint-gain checks
pass **20 ±0.1 V/V** with routing-derived supply/return resistance. At a 3.0 V
source and twice nominal resistance, minimum local rail is **2.948695 V** and
maximum incremental global input-referred output shift is **50.5 uV** versus
the ideal-rail control. This is a bounded TT/27 C schematic DC result;
transient response, bandwidth, joint reference/receiver behavior and whole-chip
IR acceptance are **not run** by this check.

## Fixture and provenance

`run_sense_supply_anchor.py` copies the existing nine-point
`g1_sense/sim/qualification/corners-20260921-a/tt_typ_3.3V_27C.cir` and its
`sense_substrate_tied.spice`. No block source, installed model/deck or delivered
geometry is changed. Inputs, copied netlist, ngspice version and model-provenance
record are SHA-256 pinned in [run provenance](sense-supply-anchor-20260921-r2/provenance.json).
The pinned unchanged PDK is `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
ngspice46, image
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
Runs use one ngspice thread, sequentially, with a 90 s per-case watchdog.

Source levels are 3.3 and 3.0 V. Resistance scales are ideal zero, nominal and
2x. Nominal forward resistance is **14.8379 ohm** and return is **11.1348 ohm**:
the largest modeled single-access values for SENSE in the actual-route mesh
plus macro access and approximate VDDA padbare feed. The 2x scale is an
assumed resistance sensitivity, not a PDK temperature/process corner.
Only SENSE's current loads these resistors; other chip currents do not.
The ideal PTAT source remains sourced from local VDD. VREF=1.04 V, shunt
stimulus, output fixture load and their returns remain referenced to global0.
Only DUT VSS, including the copied resistor substrate connections, moves to the
local return. Thus this test preserves external reference/input semantics
instead of silently moving every voltage source with DUT ground.

Each case covers true global average input common mode −0.1/0/+0.3 V and
shunt differential 0/25/50 mV. Outputs are retained relative to both global0
and localVSS. Local ground rise can put local input common mode below the prior
−0.1 V qualification floor; this is part of the declared perturbation, not a
new all-corner input-range claim. No actual BGR, comparator, IO mesh, package,
other chip load or thermal model is present.

## Results

[Analysis r3](sense-supply-anchor-analysis-20260921-r3/summary.json) combines the
four nonzero-resistance cases from run r2 with the two corrected ideal controls
from run r3. Maximum resistor voltage consistency residual is below 4.87 uV,
passing the stated 10 uV check that accommodates ngspice's retained roughly
six-significant-digit `echo` output.

| Source | Resistance scale | Minimum local VDD−VSS | Maximum VSS rise | Maximum incremental global input-referred shift |
|---|---:|---:|---:|---:|
| 3.3 V | ideal | 3.300000 V | 0 | control |
| 3.3 V | 1x | 3.274206 V | 10.834 mV | 23.0 uV |
| 3.3 V | 2x | 3.248449 V | 21.651 mV | 44.5 uV |
| 3.0 V | ideal | 3.000000 V | 0 | control |
| 3.0 V | 1x | 2.974329 V | 10.781 mV | 20.5 uV |
| 3.0 V | 2x | 2.948695 V | 21.545 mV | 50.5 uV |

Endpoint gains span **19.98798–19.99260 V/V** across all cases/common modes.
Gain uses the 0-to-50 mV output difference; the middle point is retained for
nonlinearity inspection. Incremental input-referred shift divides the changed
global output by20. It is not the total input offset, calibrated residual,
comparator trip error or mismatch envelope. Local-output changes differ because
DUT ground moves; no shared-ground cancellation with a receiver is assumed.
The nominal-resistance supply/return loss near26 mV agrees with the earlier
conditional known-load calculation's scale, while this transistor fixture
allows device currents and operating points to respond to the perturbed rail.

## Failed and corrected setup checks

- Run r1 used a thread pool around the shared watchdog. The watchdog installs
  process signal handlers, so it raised an exception after launching children.
  Its container exited; those checks are **not run to verified completion**.
  Decks, partial manifests, logs and disposition remain preserved. R2 uses the
  watchdog correctly from the main thread.
- R2's ideal controls initially represented shorts with 1e-9-ohm resistors.
  Signal outputs matched the original baseline, but numerical conditioning
  shifted reported source current by up to about3.3 uA. Those control currents
  are not used. Only the two controls were rerun in r3 with ideal zero-volt
  connections; all seven original signal/current columns then match all18
  retained original control operating points exactly at printed precision.
- R3's run metadata still names the superseded1e-9-ohm placeholder; hashed
  actual decks contain ideal0V connections. Its disposition records that
  correction and the current runner emits0 for future control metadata.
  Earlier manifests and analyses were not overwritten.

The authoritative selected set is36 nonzero-resistance OP from r2 plus18
ideal-control OP from r3. All72 OP including the superseded18 controls completed,
but only the corrected54 are used for the conclusion.

## Reproduction

Current runner reproduces all six cases with ideal controls directly. Use fresh
output paths; evidence is never overwritten.

```sh
G1_CPUS=2 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/review/audits/run_sense_supply_anchor.py --output build/scratch/sense-supply-repeat
python3 designs/g1-guardian/review/audits/analyze_sense_supply_anchor.py --run build/scratch/sense-supply-repeat --output build/scratch/sense-supply-analysis-repeat
```

To reproduce the retained combined analysis exactly, use run r2 and
`--baseline-run designs/g1-guardian/review/audits/sense-supply-anchor-20260921-r3`.

IOVDD/IOVSS impedance is not inferred from core VDDA/VSS. The separate
[GATE split-current audit](GATE_SPLIT_POWER_20260921.md) leaves loaded IO IR
unqualified. A next dynamic check requires actual current waveforms, local
capacitance and shared rail/return coupling with BGR/TRIP; this static anchor
alone does not establish transient immunity or tapeout readiness.
