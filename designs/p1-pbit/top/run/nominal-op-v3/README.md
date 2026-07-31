# Top V3 nominal operating-point attempt 2

This package retains the first parseable nominal operating-point dataset for
the source-backed Top V3 hierarchy. It contains the public testbench deck, the
complete ngspice log, the binary raw plot, and a direct raw-value summary.

## Result boundary

- ngspice 46 completed the interactive command with exit code 0 in 0.36 s.
- The raw file contains one real `Operating Point` plot with 398 variables and
  one point: 398 finite scalar values and zero non-finite values.
- The complete log reports one data row and names the retained raw file.
- Dynamic gmin stepping started and completed.
- The log retains this model warning:
  `The temperature limiting function received NaN.`
- The nominal testbench leaves `PBIT_OUT`, `PBIT_RAW`, and `CLK_OUT_DIV`
  unloaded. Its `IE` current-sink node settles at -0.3974311876486 V.

This establishes successful execution and a parseable raw dataset. Electrical
status remains **not evaluated** while the thermal warning, the negative `IE`
bias, and internal-node plausibility are reviewed. It does not establish
transient behavior, noise statistics, correlation, power closure, PVT, DRC,
LVS, PEX, signoff, or tape-out readiness.

## Artifact identity

The executed private deck had SHA-256
`a90cb297b1b2d010bf314abe8f855aa686b7e7c220d8ceb42b72743321b81889`.
The complete log has SHA-256
`ff400eb7bb37d44a3651731420306dd2e6aaa13b0b30c7a7e0a65f49dd993e32`.
The binary raw file has SHA-256
`48df8f04a44983892e8b04fab4ff42663e6d1a6e4d46a71180c728beeb2f619d`.

For publication, nine absolute runtime paths in the deck were rewritten:
six model-library paths and two OSDI paths now begin with `$PDK_ROOT`, and the
top-netlist include points to the adjacent published
`source-backed-v3/p1_top_hier.spice`. No source, stimulus, device, analysis, or
control command changed. The source-backed netlist itself is path-sanitized;
its README records the frozen original and public hashes.

## Files

| File | Purpose |
| --- | --- |
| `tb_p1_top_v3_dc_op_v3.public.cir` | path-sanitized executable deck |
| `log_tb_p1_top_v3_dc_op_attempt2.log` | complete execution log |
| `raw_tb_p1_top_v3_dc_op_attempt2.raw` | one-point binary raw plot |
| `RAW-SUMMARY.tsv` | directly parsed plot counts, top ports, and supply currents |
| `SOURCE-IDENTITIES.tsv` | frozen and publication artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Reproduce

From this directory, set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run:

```sh
ngspice -i -o log_reproduced.log tb_p1_top_v3_dc_op_v3.public.cir
```

The control section writes `raw_tb_p1_top_v3_dc_op_attempt2.raw` and quits.
Move the retained published raw file first if it must not be overwritten.
Compare reproduced evidence by plot identity, variable names, values,
warnings, and topology; timestamps and runtime paths are not electrical
content.
