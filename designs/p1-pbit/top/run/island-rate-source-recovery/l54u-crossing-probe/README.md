# l=5.4u code-540 crossing probe — bounded negative (2026-08-21)

G-12 done-when #2 requires a `--nomismatch` run reproducing the known 541-543
island before any mismatch draw is counted. Reproducing the island requires
locating the l=5.4u build's code-540 decision crossing first. Three native
ngspice runs (all in container `sandboxy-dfae180cb900847d`, ngspice-46, PSP via
OSDI from the PDK `.spiceinit`) bound that crossing — and find none in ±200 mV.

## The finding, bounded

| probe | sweep | pbit_raw_core result | c_p / c_n |
| --- | --- | --- | --- |
| `pe-diag.cir` | code 540, -60..+60 mV, 10 mV steps (13 pts) | LOW (~8.6e-8 V) at every point | — |
| `pe-iso.cir` | code 540, single point -38.5 mV, VEDP/VEDN dropped | LOW (8.57e-8 V) | c_p latches 0.382 V, c_n 0.244 V |
| `pe-xsrch.cir` | code 540, -200..+200 mV, 20 mV steps (21 pts) | LOW (6.4e-8..8.6e-8 V) at every point | c_p 0.447→1.579 V, c_n 0.219→0.309 V, c_p−c_n always positive (min ~0.135 V at 0 mV) |

**The l=5.4u build's `pbit_raw_core` (the island node) does not cross HIGH/LOW
anywhere in [-200, +200] mV at code 540.** The comparator core `c_p`/`c_n` does
latch and its differential is monotonic and single-signed across the whole band,
but the pbit output that the island harness classifies never flips. The l=483u
build's code-543 crossing (-38.645 mV) lies inside this swept band, so the two
builds do **not** share a trim origin.

## VEDP/VEDN drop is behavior-neutral (re-confirmed)

`pe-iso.cir` is `s1t1.cir` with the two `VEDP`/`VEDN` force-bias lines removed,
run at the same single point (-38.5 mV) that produced `s1t1.log`. Its c_p latches
to 0.382 V and c_n to 0.244 V — identical to s1t1 *with* VEDP/VEDN (c_p 0.381 V,
c_n 0.244 V) — and pbit_raw_core stays LOW. This is native confirmation of H-1343:
the drop changes nothing on the latch, so the LOW pbit is a real l=5.4u property,
not a deck artifact of the drop.

## What this means for the option-(b) re-baseline

Option (b) re-baselines the n=8/n=20 island-rate sample on the l=5.4u v7-merged
build on the assumption that it is the surviving trim comparator. This probe
shows the l=5.4u build's code-540 pbit output does not reproduce the l=483u
decision-crossing behavior in a ±200 mV window. Absence outside ±200 mV is NOT
measured — this is a bounded negative, not a claim that no crossing exists
anywhere. But the comparability premise of the re-baseline is now in question and
goes back to the operator, whose sign-off on (b) was still absent as of this
sweep. 5.75x is unchanged (it rests on dead codes and monotonicity, not the
island rate).

## Deck identity (sha256)

| file | sha256 |
| --- | --- |
| `pe-diag.cir` | `d42f090c…` |
| `pe-iso.cir` | `78d8bdde…` |
| `pe-xsrch.cir` | `382eb163…` |

Run requirement: ngspice must start from `/foss/pdks/ihp-sg13g2/libs.tech/ngspice`
with `PDK_ROOT=/foss/pdks PDK=ihp-sg13g2` or the IHP PSP models fail to load
('Unknown model type psp103va' / 'model name is not found'). The `.include` paths
in the decks are the container run paths and map onto
`../C169-SOURCE-coarse-dac-v7-merged.spice` and `../C156-ISOBUF-PBIT_OUT.spice`.
