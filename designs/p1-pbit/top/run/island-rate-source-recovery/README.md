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
| `pe-d560.cir` | `0a392730…` | island-harness deck head: the retained n=8 sample deck, instantiated the comparator as 13-port `XCOMP` |
| `pe-fwcs.cir` | `bab04da3…` | reconstructed island source: deck head + reviewed `p1_comparator`/isolation-buffer includes |

The two `pe-*.cir` files were the last `/tmp`-resident reconstruction assets. They are
now git-backed here so G-12 done-when #1 does not depend on the host `/tmp` surviving
another handover (the exact H-1340 failure). They are byte-identical to the retained deck
head and reconstructed source; copy and re-hash rather than trusting a filename.

Their `.include`/`.lib` lines carry the container run paths, which map onto this
directory: `/tmp/C169-final.spice` is byte-identical to
`C169-SOURCE-coarse-dac-v7-merged.spice` (`97938952…`) and
`/volume/user/workspace/2026-08-03_p1-cml-div2-cml-div4-c11-iso-buffer/C156-ISOBUF-PBIT_OUT.spice`
resolves to `C156-ISOBUF-PBIT_OUT.spice` (`81c708e1…`).

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

The deck head (`pe-d560.cir` in this directory, sha256 `0a392730…`) instantiates the comparator
as a 13-port `XCOMP` and names seven internal nodes in its `.nodeset`. The surviving
`C169-SOURCE-coarse-dac-v7-merged.spice` `p1_comparator` subckt matches the same 13
ports in the exact `XCOMP` order (PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N
TRIM_P TRIM_N VCC_HBT VDD VSS CODE), and all seven `.nodeset` nodes (`c_p1_comp`,
`c_p2_comp`, `c_p`, `c_n`, `e_track`, `ef_p`, `ef_n`) are present.

**H-1343 resolved (2026-08-21): the l=483u comparator is unrecoverable, and the
VEDP/VEDN force-biases are inert — drop them, do not rewire.** The deck head
force-biases two comparator-internal nodes that no surviving source contains:

```
VEDP xcomp.e_dac_p 0 DC 0.687
VEDN xcomp.e_dac_n 0 DC 0.687
```

`e_dac_p` / `e_dac_n` appear zero times in either surviving l=5.4u build, which
instead degenerates each DAC cell individually (`e_dacu1..e_dacu150`, `e_dacb0`,
`e_dacb1`, each with its own resistor to `VSS`). The `e_dac_p`/`e_dac_n` tokens that
do appear in the repository belong to the bare 9-port core comparator
(`chain-bringup/bit-autocorrelation`), not this 14-port trim-array comparator.
Full-repo search is conclusive on the loss: `git log --all -S '483u' -- '*.spice'
'*.cir'` is empty across every commit and branch, so the l=483u trim comparator
(audit `a55534db…`) survives nowhere. The two VEDP/VEDN sources are proven inert by
the native run: the post-swap container's `s1t1.log` node dump shows `vedp#branch = 0`
and `vedn#branch = 0` — zero current, change nothing. Drop those two lines; do not
rewire, because the l=5.4u build has no shared tail node to rewire to.

**The environmental blocker (H-1342) is resolved (H-1349).** The post-swap DSH
container's ngspice-46 loads the IHP PSP103 model via OSDI (native `psp-probe2.log`:
"PSP103VA models … loaded with OSDI", level 104) and completes a code-540 transient
(`s1t1.log`, 1,840 rows, "ngspice-46 done"). No OpenVAF rebuild is needed in this
container; a rebuild recipe is staged read-only in the container
(`.dsh-context/osdi-rebuild-plan.md`) should reproducibility ever require it.

## Open decision (G-12) — narrowed to one path

The n=20 island-rate tightening (`mb9`–`mb20`) was launched 2026-08-20 08:55Z,
was never collected, and its source died with the handover. The two options are no
longer symmetric:

- **(a) rebuild l=483u — INFEASIBLE.** Its one differentiating feature (the shared
  `e_dac_p`/`e_dac_n` topology) is specified by no surviving source, and the H-1344
  rebuild checklist is itself lost, so a "rebuild" would be a new, unverifiable
  netlist, not the lost one.
- **(b) re-baseline on the l=5.4u v7-merged build above — RECOMMENDED.** Drop the two
  inert VEDP/VEDN lines (proven behavior-neutral) and re-run n=8 and n=20 together to
  restore comparability.

The recommended path is still gated on operator sign-off, and on a `--nomismatch` run
reproducing the known 541-543 island before any mismatch draw is counted. The 5.75x
scaling recommendation is unchanged by either path — it rests on dead codes and
monotonicity, not on the island rate.

## 2026-08-21 — done-when #2 hit a bounded negative (see `l54u-crossing-probe/`)

Before the island can be reproduced, the l=5.4u build's code-540 crossing must be
located. A three-deck native probe (`l54u-crossing-probe/`) found **no pbit crossing
in [-200, +200] mV**: `pbit_raw_core` stays LOW (6.4e-8..8.6e-8 V) at every point while
the comparator core `c_p`/`c_n` latches and stays single-signed. The l=483u build's
code-543 crossing (-38.645 mV) lies inside that band, so the l=5.4u build does NOT share
the l=483u trim origin. This is a bounded negative (absence outside ±200 mV is not
measured), and it puts the comparability premise of option (b) back in question — the
operator's sign-off on (b) was still absent as of this sweep. 5.75x unchanged.
