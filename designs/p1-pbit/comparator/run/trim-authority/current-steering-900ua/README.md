# Current-steering trim: 900 uA static experiment

This package changes only the shared steering-tail current from the retained
780 uA experiment to **900 uA**. It uses the same 27 °C typical-model static
comparator front end, ideal fixed tail, explicit trim-base voltages, and
collector-differential zero-crossing method.

An independent recount of the three raw files gives:

| code | `TRIM_P` / `TRIM_N` | input zero crossing | authority from midpoint | total VCC current | collector common mode |
| --- | --- | ---: | ---: | ---: | ---: |
| minimum | 0.900 / 1.100 V | -47.601736336458 mV | **-47.612464669422 mV** | 2.854669533717 mA | 2.092740388047 V |
| midpoint | 1.000 / 1.000 V | +0.010728332964 mV | 0 | 2.856638770000 mA | 2.092459395268 V |
| maximum | 1.100 / 0.900 V | +47.605174633233 mV | **+47.594446300269 mV** | 2.854669560880 mA | 2.092740384179 V |

Each raw has 601 rows and 14 columns, all 8,414 values finite, strictly
increasing input coordinates, identical repeated scale columns, and exactly
one collector-differential crossing. The native log records three completed
601-row analyses and no NaN, thermal, resistor-voltage, convergence-recovery,
parser-error, abort, or failure token.

The limiting nominal authority is **47.594446300269 mV**. Conditional on the
separate warned 199-point offset sample standard deviation of
7.586947466704 mV, that is **6.273200982232 standard deviations** and
**2.072761500045 mV** beyond the arithmetic six-standard-deviation target.

That comparison does not close an engineering gate. It combines a nominal,
typical-model, ideal-tail steering experiment with a separate HBT-mismatch
campaign whose physical-model logs retain a self-heating warning and one
unknown point. It does not establish a physical current source, digital code
mapping, local resolution, mismatch, dynamic behavior, temperature or process
corners, yield, architecture selection, or signoff.

## Evidence ladder

[`current_steering_900ua_evidence_ladder_v3.tsv`](current_steering_900ua_evidence_ladder_v3.tsv)
keeps five evidence levels separate: this ideal-tail authority experiment, the
2.25 µm physical unit, the loaded weight-8 cell, the loaded 31-unit
major-carry slice, and the current full-array boundary. Every published path
and SHA-256 resolves at its cited commit; the first four rows separately label
the native executed deck and the sanitized public deck.

The final row records the boundary as it existed when V3 was published: it
binds the retained model-valid self-heating-on 780 µA-era full-array
diagnostic, whose finite raw accompanies a thermal NaN/heat-sink warning, and
explicitly records that no 900 µA full-array artifact existed at that commit.
V3 remains an immutable provenance snapshot rather than being silently
rewritten.

A later
[model-valid full-array code-0 diagnostic](../current-steering-unit-cell/base-driver-dc/full-array-self-heating/model-valid-2x8/900ua-code0/README.md)
now provides a complete 900 µA-scale deck, native log, and raw file. Its 1,201
rows are finite and yield one collector crossing, but the thermal NaN/heat-sink
warning recurs. The current full-array engineering status therefore remains
**UNKNOWN**; specification status is **NOT EVALUATED**. Nominal subarray
evidence is not promoted into a full-array conclusion.

The TSV is 7,331 bytes with SHA-256
`91c1e291ac65b54a514a925ac13b8c722295fb828b19aad3a7a1ce0184533fd2`.

## Artifact identity and reproduction

The exact executed deck was 2,877 bytes with SHA-256
`bb747af21d7b133ebaaf30061918a82f51602b7bf6c5b5e1677b08ae588d8c16`.
The public deck has SHA-256
`d4991eefe6460b4a139c86c7fec7bf7a5138145fbd9898087cd71e274edd008f`;
it differs only by replacing machine-specific model, include, OSDI, and
output paths with `$PDK_ROOT` and repository-relative paths. The native log
and all three raw files are byte-identical to the executed artifacts.

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_current_steering_900u.cir > log_current_steering_900u.log
```

The deck runs all three code points and writes the three
`raw_900u_steer_*.txt` files.
