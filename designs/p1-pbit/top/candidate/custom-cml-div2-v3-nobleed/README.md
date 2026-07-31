# Custom CML divide-by-2 candidate V3 no-bleed experiment

This directory preserves one controlled topology experiment derived from
[`custom-cml-div2-v2`](../custom-cml-div2-v2/). It is not an adopted or validated
divider implementation.

## Exact change

Candidate V3 removes the four `XRBLEED_TRACK_*` and `XRBLEED_LATCH_*`
instances that connected each data-pair emitter node directly to its tail node
in parallel with the clock-steering HBT. A two-source manifest in the linked
operating-point package accounts for all 90 V2 physical lines:

- 86 lines are `IDENTICAL`;
- 4 lines are `ONLY_BASE`; and
- there are no target-only or modified lines.

The source identities are:

- V2 SHA-256:
  `64226d8548e664d3a26247817926b1f5bfc5a0cf0552d342861b21c03ef78652`;
- V3 SHA-256:
  `d5900dae655f376e6c2aeeebe18d7753f3c36c73283ca859586e57f25dcedd52`.

No model, device dimension, bias, supply, load, clock phase, reset, initial
condition, or node-set changed in this candidate.

## Evidence boundary

The complete nominal operating-point package is
[`run/custom-cml-div2-op-nobleed-v1`](../../run/custom-cml-div2-op-nobleed-v1/).
At its static clock phase, the active master clock-HBT collector current is
`1.95433260614587745 mA`, or `99.80387017499068%` of the master tail-HBT
collector current. The corresponding V2 ratio was approximately `0.1365%`.

That redistribution is a static operating-point observation only. The native
log retains the temperature-limiter NaN and heat-sink warning. Two active clock
HBTs and both tail HBTs remain below the cited `0.40 V` VCE model range. The
differential outputs are equal within approximately `0.108 pV` at this point,
so the operating point does not establish division, startup, restoration,
frequency capability, or any specification result.

Engineering status remains **unknown**. Signoff and tape-out readiness are not
claimed.
