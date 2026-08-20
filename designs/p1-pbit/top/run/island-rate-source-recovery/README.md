# Island-rate source recovery — the surviving l=5.4u lineage

This directory preserves the surviving comparator/DAC source lineage after the
2026-08-20 runtime handover destroyed the island harness's `/tmp`-resident
netlists. Every file is identity-stated by SHA-256 below; copy and re-hash
rather than trusting a filename.

## What is here

| file | sha256 (first 16) | role |
| --- | --- | --- |
| `C169-SOURCE-coarse-dac-v7-merged.spice` | `97938952…` | l=5.4u full-top source; the surviving re-baseline candidate |
| `C169-SOURCE-coarse-dac.spice` | `cff25fb5…` | l=5.4u full-top source; earlier, non-merged |
| `C169-gen-standalone.py` | `edc2854c…` | standalone DAC deck generator (emits l=5.4u) |
| `C156-ISOBUF-PBIT_OUT.spice` | `81c708e1…` | PBIT_OUT isolation-buffer include; intact, matches the audit |

## What is NOT here

The island harness's exact trim comparator was the **l=483u** `C169-final.spice`
(audit `a55534db7d2441f0a379321bebadbd7023fb7b32f0ae966c9a55c6f441ab66e6`) —
the corrected-weighting + 5.75x-current build: all DAC element types at l=483u,
unary m=4, binary b1 m=2 / b0 m=1. It survives nowhere: not the container
workspace, not the legacy tarball, not this repository. It is genuinely lost,
and none of the l=5.4u files above reproduces it (H-1341).

## Why this directory exists

H-1340/H-1341: a `/tmp`-resident source that backs a published number is the
single point of failure. The surviving l=5.4u lineage lived only in the Sandboxy
container workspace, which is not git-backed. This is the durable copy, so the
re-baseline path does not depend on the container surviving another handover.

## Structural compatibility (verified 2026-08-20 14:48Z, corrected 15:17Z)

The deck head (`/tmp/pe-d560.cir`, sha256 `0a392730…`) instantiates the comparator
as a 13-port `XCOMP` and names seven internal nodes in its `.nodeset`. The surviving
`C169-SOURCE-coarse-dac-v7-merged.spice` `p1_comparator` subckt matches the same 13
ports in the exact `XCOMP` order (PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N
TRIM_P TRIM_N VCC_HBT VDD VSS CODE), and all seven `.nodeset` nodes (`c_p1_comp`,
`c_p2_comp`, `c_p`, `c_n`, `e_track`, `ef_p`, `ef_n`) are present.

**That match is not complete (H-1343).** The deck head also force-biases two
comparator-internal nodes that no surviving source contains:

```
VEDP xcomp.e_dac_p 0 DC 0.687
VEDN xcomp.e_dac_n 0 DC 0.687
```

`e_dac_p` / `e_dac_n` appear zero times in either surviving l=5.4u build, which
instead degenerates each DAC cell individually (`e_dacu1..e_dacu150`, `e_dacb0`,
`e_dacb1`, each with its own resistor to `VSS`). ngspice silently accepts a source
on a non-existent subckt-internal node (no error, no warning), so a naive
reconstruction would run with that bias disconnected. Path (b) is therefore clean at
the ports and `.nodeset` nodes only, not mechanically clean overall — the two
VEDP/VEDN targets must be reconstructed or re-derived before any run is trusted.
The device length is still l=5.4u rather than l=483u, which is exactly why
re-baselining (not substitution) is required for comparability with the published
n=8 l=483u sample.

**A second blocker is environmental (H-1342).** The post-handover container's
ngspice-46 has PSP (level 103) not compiled in — the IHP SG13G2 MOS models
(`sg13g2_hv_*_psp`, `sg13g2_lv_*_psp`, type `psp103va`) report "Unknown model type"
and cannot load, so no comparator/island deck simulates in the current container at
all. This blocks both the l=5.4u re-baseline and a rebuilt l=483u comparator, until
a PSP-capable ngspice is present.

## Open decision (G-12)

The n=20 island-rate tightening (`mb9`–`mb20`) was launched 2026-08-20 08:55Z,
was never collected, and its source died with the handover. Re-running requires
operator sign-off to either:

- **(a)** rebuild l=483u from the documented recipe, or
- **(b)** re-baseline the island-rate sample on the l=5.4u v7-merged build above
  (re-running n=8 and n=20 together to restore comparability).

Both paths are gated on a `--nomismatch` run reproducing the known 541-543
island before any mismatch draw is counted, and that validation itself is blocked
until a PSP-capable ngspice is present (H-1342). The 5.75x scaling recommendation is
unchanged by either path — it rests on dead codes and monotonicity, not on the
island rate.
