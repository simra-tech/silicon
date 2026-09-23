# Two hot hard-residual failures: bounded read-only triage

Status: completed simulated-wave comparison; causal isolation **not run**.
The original electrical failures for seeds73023 and73073 remain failed.
No source, model, clock, code, criterion, population, or simulator setting changed.

The original binary room calibration freezes residual soft/hard codes128/143
and138/157 respectively. Both draws give LOW/LOW at25C and LOW/HIGH at125C
for24.5mV, where LOW/LOW is required. Their25.5mV checks give HIGH/HIGH at
both temperatures. All28 leaves per draw completed numerically and their
12 guard checks passed. This triage is not the independent fixed100 audit.

The analyzer reads and hash-verifies eight existing residual waves, their
decks and receipts, and exact11512 before/after vectors. It interpolates
each actual hard-clock crossing and averages the last three cycles.

| Simulated quantity | Seed73023 | Seed73073 |
|---|---:|---:|
| Frozen residual hard code |143|157|
| SENSE paired slope at25C,1ns before edge (V/V) |19.986319|19.969491|
| Same slope at125C (V/V) |19.984803|19.970103|
| Hot−room VPED at24.5mV,1ns before edge (mV) |−3.491756|−1.495592|
| Hot−room ISENSE at same phase (mV) |+3.209215|+7.091494|
| Hot−room hard DAC input at same phase (mV) |−2.189378|−1.555966|
| Hot−room hard differential at same phase (mV) |+3.748086|+5.055847|
| Hot−room hard differential at edge+0.1ns (mV) |+5.490526|+6.796033|
| Additional edge-related thermal motion (mV) |+1.742440|+1.740186|

The paired slope uses the existing24.5/25.5mV runs at matched clock phase.
It includes dynamic loading and is not an isolated DC gain measurement.
The weak slope change contrasts with larger temperature motion of SENSE
output offset and DAC operating point. BGR VREF itself decreases about
2.252/2.600mV; VREF_BUF decreases3.249/2.311mV at the pre-edge phase.
These observations do not uniquely assign causality to any one block.

At edge+0.1ns, hard input differential is−7.475/−8.119mV at room and
−1.985/−1.323mV hot. The regenerative internal branches then resolve the
hot HIGH result. By edge+0.3ns, XP/XQ are6.37/21.93mV and6.65/21.88mV at
room, versus38.19/16.62mV and61.72/11.23mV hot. The eventual HIGH while
the late input differential remains negative demonstrates why a20ns
latched output cannot by itself define static comparator offset.

The exact observational decomposition is
`icmp-vth_hard = (icmp-isense/2)+(isense-vped)/2+vped/2-vth_hard`.
Reconstruction residuals and every term are retained in the JSON. This is
an algebraic identity, not causal attribution. Useful next controlled
quantities are VREF, VREF_BUF, VPED, ISENSE, xt.icmp, xt.vth_hard,
xt.cmp_clk_n and hard XP/XQ/XN/YN during the first0.3ns.

A credible remedy hypothesis is temperature compensation of the combined
SENSE offset/reference-DAC operating point, together with reducing or
matching dynamic input loading. Gain-only correction is not supported by
these two observations. A temperature-aware calibration would change the
calibration method and needs a prospective contract and independent
population testing; it cannot retroactively repair these outcomes.
No remedy or extra probe is authorized by this report. The±0.5mV criterion
and all failed samples remain unchanged.

Reproduce the read-only analysis from the block's`sim` directory:

```sh
python3 analyze_joint586_hot_residual_triage.py --output qualification/NEW_TRIAGE.json
```

Evidence:[joint586-two-hot-residual-triage-20260923.json](joint586-two-hot-residual-triage-20260923.json),
SHA256`9c6e7f8748fcdfe6e183a242ff34877df09ad63e5ad700e2f0d78a6f54f94764`.
The original source hashes, waveform hashes, code pairs, sampling policy
and per-leaf receipts are retained there. Physical model applicability and
full final-layout qualification are not established by this comparison.
