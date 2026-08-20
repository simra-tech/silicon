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

## Open decision (G-12)

The n=20 island-rate tightening (`mb9`–`mb20`) was launched 2026-08-20 08:55Z,
was never collected, and its source died with the handover. Re-running requires
operator sign-off to either:

- **(a)** rebuild l=483u from the documented recipe, or
- **(b)** re-baseline the island-rate sample on the l=5.4u v7-merged build above
  (re-running n=8 and n=20 together to restore comparability).

Both paths are gated on a `--nomismatch` run reproducing the known 541-543
island before any mismatch draw is counted. The 5.75x scaling recommendation is
unchanged by either path — it rests on dead codes and monotonicity, not on the
island rate.
