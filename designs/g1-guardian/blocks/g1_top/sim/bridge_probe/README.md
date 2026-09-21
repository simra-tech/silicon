# Clock bridge regression

The original G1_TOP clock ADC used `in_low=0.55`, `in_high=0.65`.
With 1 ns input edges and a 20 ps maximum step, the bridge exposes an
unknown state between zero and one. The Icarus divider responds to both
0→unknown and unknown→1 as rising edges; the DAC output peaks at only
0.32 V instead of completing its transition. This invalidates the earlier
chip-level timing evidence whenever those intermediate events occur.

A separate clock receiver with both thresholds at 0.6 V produces a simulated
4.959501 MHz divider output from a 9.919 MHz input. Data bridges retain their
original unknown-state band. This models a single-threshold receiver, not
metastability or clock noise.

| Check | Status | Evidence |
| --- | --- | --- |
| Original clock receiver | failed (reproduced intentionally) | `band.log`: no valid 0.6 V output crossings, max 0.32 V |
| Single-threshold clock receiver | passed | `threshold.log`: 4.959501 MHz, max 1.2 V |
| Full chip-path timing with corrected receiver | not run to completion | reruns use `_clockfix` tags and preserve original logs |

Reproduce from repository root:

```
flow/run.sh bash designs/g1-guardian/blocks/g1_top/sim/bridge_probe/run.sh
```

Built against ngspice 46 and Icarus Verilog 14.0 in the container pinned in
G1 PLAN.md; version banners in the existing G1_TOP logs establish the tools.
PDK: not applicable to this isolated digital/bridge test (no device models).
No PDK models, rule decks or design RTL were changed.
