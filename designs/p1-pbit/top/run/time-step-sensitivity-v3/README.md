# Top V3 transient time-step sensitivity attempt 1

This package compares the first 2 ns of the published deterministic Top V3
[transient-smoke waveform](../transient-smoke-v3/) against one otherwise
identical run with the maximum time step reduced from 1.0 ps to 0.5 ps.

## Result boundary

- ngspice 46 completed the forced-interactive command with exit code 0 in
  3.10 s.
- The new raw file contains one real `Transient Analysis` plot with 10
  variables and 4,125 strictly increasing time points from 0 to 2 ns.
- All 41,250 scalar values are finite.
- The new `clk_out_div` minimum is -0.157849764392 V and its maximum is
  +1.403456624690 V.
- Relative to the 1.0 ps baseline over the same window, those extrema move by
  -0.291352 mV and +0.279417 mV.
- After linearly interpolating the 0.5 ps waveform onto every baseline
  timestamp, `clk_out_div` differs by at most 1.09426 mV, with 0.33597 mV RMS
  difference.
- Both waveforms have 20 numerical midpoint crossings in the 2 ns window.
- The temperature-limiting NaN warning remains in the new log.

This establishes a controlled numerical comparison. It does not define a
convergence tolerance or show electrical acceptance. The output overshoot and
undershoot remain open observations, and the current harness leaves
`CLK_OUT_DIV` externally unloaded. This package makes no logic-threshold,
propagation-path, stochastic, correlation, PVT, signoff, or tape-out-readiness
claim.

## Artifact identity

The executed private deck had SHA-256
`b97cc87ea18f8f875c4f87a72cbabc714eae8a276cf22961b8150703faed8707`.
The complete log has SHA-256
`b0161f1c8d9eb2b7d3a5af8e2a4f0177130a587c02701fd22f1f99f514587366`.
The binary raw file has SHA-256
`65f843c78791a3ffe1a6d6341449c25c48f162fdf71ba2e62b8728130bfb82d6`.

For publication, the deck's absolute runtime paths were replaced with
`$PDK_ROOT` and the adjacent published
`source-backed-v3/p1_top_hier.spice`. No source, stimulus, vector, analysis, or
control command changed.

## Files

| File | Purpose |
| --- | --- |
| `tb_p1_top_v3_tran_step_0p5p.public.cir` | path-sanitized sensitivity deck |
| `log_tb_p1_top_v3_tran_step_0p5p.log` | complete execution log |
| `raw_tb_p1_top_v3_tran_step_0p5p.raw` | 0.5 ps maximum-step raw plot |
| `COMPARISON-SUMMARY.tsv` | direct baseline/new extrema and interpolation deltas |
| `SOURCE-IDENTITIES.tsv` | frozen and publication artifact identities |
| `PUBLISHED-HASHES.sha256` | hashes of every published technical file |

## Reproduce

From this directory, set `PDK_ROOT` to the `ihp-sg13g2` PDK root and run:

```sh
ngspice -i -o log_reproduced.log tb_p1_top_v3_tran_step_0p5p.public.cir
```

The control section writes `raw_tb_p1_top_v3_tran_step_0p5p.raw` and quits.
Move the retained published raw file first if it must not be overwritten.
Compare against the first 2 ns of the baseline raw in
`../transient-smoke-v3/`.
