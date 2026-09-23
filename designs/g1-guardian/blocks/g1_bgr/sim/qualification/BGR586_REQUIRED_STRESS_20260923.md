# Current-source original stress characterization

The original three nominal fixtures are applied to source
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`:

- Supply dip: 3.3 V to 1.8 V at 5.01 us, restored at 10.01 us.
- R4 mode: 0 V to 3.3 V at 5.01 us, restored at 20.01 us.
- VREF load: 100 nA from 5.01 to 20.01 us, with the original 1 pF load.

Each keeps the original `tran 2n 40u`, implicit operating-point initialization,
seed, model sections, temperature, source and tolerances. The historical
capacitance-only source is replaced by the same canonical source used in the
current electrical campaigns; its 329 legacy capacitors remain. There is no
new physical RC or actual downstream-load claim. Initializer threads are
reduced from four to one. Read-only endpoint queries cover all 2,842 qualified
parameters and external terminal voltages for 637 MOS/HBT instances. No extra
OP or initial-condition constraint is inserted.

## Results and limits

Five source/transform/wave controls passed. All three runs completed to 40 us,
but **failed** their log gates: the temperature limiter reported NaN during
initialization, before dynamic gmin stepping completed. Zero exit status and a
saved endpoint do not waive that diagnostic. Original summaries and logs remain
unchanged. The independent saved-output audit passed in 11.837 s, preserving
all three failed log gates and reporting these scoped simulated results:

| Fixture | Saved rows | VREF minimum / maximum (V) | VREF endpoint (V) | IPTAT endpoint (uA) | Maximum saved HBT external \|VCE\| (V) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Supply dip | 20,077 | 0.856754 / 1.378863 | 1.045460219 | 4.165335 | 0.984135 |
| R4 mode | 20,124 | 0.919761 / 1.046078 | 1.045460218 | 4.134106 | 0.744346 |
| 100 nA load | 20,020 | 1.043228 / 1.045460 | 1.045460218 | 4.134131 | 0.722959 |

All saved vectors, exact 2,842-parameter endpoint inventories, HBT VCE screens
and original broad final-level screens passed independently. No stimulus is
unrun. The dip's large VREF excursion and remaining IPTAT deviation must not
be hidden by the broad endpoint screen; real downstream consequences and an
allocated recovery/settling-error test remain **not run**.

The independent auditor can verify finite saved output and original endpoint
screens separately from an unresolved initialization warning; it never changes
the original failed attempt to passed. It checks exact source/runtime/deck
identity, vector names, strictly increasing time, all 2,842 endpoint parameters
and all 301 HBT external VCE values. The original broad final-level screen is
0.9 < VREF < 1.2 V; HBT |VCE| <= 1.6 V is reported separately. Neither is an
allocated settling-error or lifetime criterion. MOS external extrema are
recorded without inventing a new model-voltage acceptance limit.

Pre-transient parameter readback, final native RC, real downstream loads,
startup-before-EN and full model/lifetime acceptance are **not run**. Statistical
yield is **not applicable** to these mismatch-disabled fixtures. No measured
silicon result is reported.

## Reproduction

`run_586_stress_required.py --case dip|r4|load --output <fresh directory>
--image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`
runs each original 300 s bounded child on one allocated CPU in `flow/run.sh`.
`audit_586_required_stress.py --run <dip> --run <r4> --run <load>
--output <fresh audit.json>` reopens the saved evidence without rerunning SPICE.

Built against ngspice 46 and IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. Every run checks actual ngspice version,
PDK COMMIT and all installed model/OSDI hashes against the qualified harness.
Exact executed runner snapshots, command receipts, compressed raw waves and
original/public hashes are retained in
`bgr586-stress-required-evidence-20260923-r1`. No simulator rerun or warning
waiver was used for the independent saved-output audit.
