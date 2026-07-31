# Top V3 deterministic transient-smoke attempt 1

This package retains the first parseable transient waveform for the
source-backed Top V3 hierarchy. It contains the public testbench deck, the
complete ngspice log, the binary raw plot, and directly parsed waveform
metrics.

## Result boundary

- ngspice 46 completed the forced-interactive command with exit code 0 in
  7.40 s.
- The raw file contains one real `Transient Analysis` plot with 10 variables
  and 10,605 strictly increasing time points from 0 to 10 ns.
- All 106,050 scalar values are finite.
- `clk_out_div` has 100 numerical midpoint crossings over 10 ns, consistent
  with a roughly 200 ps cadence.
- `clk_out_div` ranges from -0.157558412649 V at 13.28 ps to
  +1.403177207446 V at 112.5 ps. These extrema remain open observations.
- `pbit_raw` and `pbit_out` remain quiescent near 0.791 V and 3.37 mV with
  0.56575 mV and 0.08817 mV peak-to-peak ripple. No logic-state label is
  assigned.
- The log retains the temperature-limiting NaN warning and reports completed
  dynamic gmin stepping.

This establishes successful execution and a parseable deterministic waveform.
Electrical status remains **not evaluated**. The deck has no stochastic noise
stimulus, and this package establishes no logic-threshold validity, propagation
path acceptance, bit statistics, correlation, PVT, DRC, LVS, PEX, signoff, or
tape-out readiness.

The preceding nominal operating-point package is
[`../nominal-op-v3/`](../nominal-op-v3/).

## Artifact identity

The executed private deck had SHA-256
`05f78e7e136a770c8583a7aed69b6a5e81683f22fe0e1c5623d1579a9cb94a34`.
The complete log has SHA-256
`da72544aff84a664b216917cff5c339266eae01652f4197d188984cd375feffc`.
The binary raw file has SHA-256
`9c3be452913c6dbb7163b4e930ea1d41cedbddd9831b21ff84d140d688e4d21f`.

For publication, the deck's absolute runtime paths were replaced with
`$PDK_ROOT` and the adjacent published
`source-backed-v3/p1_top_hier.spice`. No source, stimulus, vector, analysis, or
control command changed.

## Files

| File | Purpose |
| --- | --- |
| `tb_p1_top_v3_tran_smoke.public.cir` | path-sanitized executable deck |
| `log_tb_p1_top_v3_tran_smoke.log` | complete execution log |
| `raw_tb_p1_top_v3_tran_smoke.raw` | 10-vector binary transient plot |
| `WAVEFORM-SUMMARY.tsv` | directly parsed ranges, endpoints, and crossings |
| `SOURCE-IDENTITIES.tsv` | frozen and publication artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Reproduce

From this directory, set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run:

```sh
ngspice -i -o log_reproduced.log tb_p1_top_v3_tran_smoke.public.cir
```

The control section writes `raw_tb_p1_top_v3_tran_smoke.raw` and quits. Move
the retained published raw file first if it must not be overwritten. Compare
reproduced evidence by plot identity, vector names, waveform metrics, and
warnings; timestamps and runtime paths are not electrical content.
