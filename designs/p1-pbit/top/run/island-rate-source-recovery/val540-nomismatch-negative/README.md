# val540 `--nomismatch` validation — the l=5.4u build does not reproduce the l=483u island (2026-08-22)

G-12 done-when #2 requires a `--nomismatch` run reproducing the known 541-543
nominal LOW island before any mismatch draw is counted. This directory holds that
validation (`val540.cir`, codes 540-543) and the two follow-on code-540 crossing
probes it triggered (`probe540.cir`, `probe540b.cir`). All three ran in container
`sandboxy-dfae180cb900847d`, ngspice-46, PSP via OSDI from the PDK `.spiceinit`.

## The result, bounded

**The island does NOT reproduce. The l=5.4u build is flat LOW across the entire
l=483u crossing region and does not share the l=483u trim origin.**

| deck | sweep | result |
| --- | --- | --- |
| `val540.cir` | codes 540-543, 25 band pts + 2 anchors each (109 markers) | every marker `v(pbit_raw_core)` ≈ 8.4e-8…8.6e-8 V = LOW; 0 HIGH, no island |
| `probe540.cir` | code 540, −45…+5 mV differential, 2.5 mV steps (21 pts) | LOW (8.42e-8…8.61e-8 V) at every point |
| `probe540b.cir` | code 540, +7.5…+50 mV differential, 2.5 mV steps (18 pts) | LOW (8.02e-8…8.62e-8 V) at every point |

`v(pbit_out_core)` is HIGH (1.2 V) at every point — the two comparator outputs are
complementary (`PBIT_OUT = NOT(PBIT_RAW)`) and both are constant across the whole
swept region. The highest band value seen anywhere is 8.62e-8 V, far below the
deck's 0.6 V HIGH threshold.

The known l=483u island was 0.20 / 0.35 / 0.60 mV at codes 541 / 542 / 543 inside
the HIGH region below the crossing (code-543 crossing at −38.645 mV). None of it
appears here.

## Why `val540.cir` reports flat LOW (deck mechanics, not a bug)

The deck first bisects for a code-540 crossing in `[−39, −37] mV`
(`blo=−39, bhi=−37`, 7 steps). Because the l=5.4u build has no crossing there, the
bisection **bottoms out at its left bracket edge**: `base = −38.9922 mV`
(`OFFSET 540` in `val540_markers.txt`). The 541/542/543 bands are then placed at
`base − 0.21 / −0.42 / −0.63 mV` — the l=483u island's relative offsets — so the
four bands land at −40.29…−39.09 (540), −40.50…−39.30 (541), −40.71…−39.51 (542),
−40.92…−39.72 (543) mV. All sit inside a uniform-LOW region, and the island
detector's "HIGH background" precondition is never met, so no island can be
measured. This is a **wrong-location / band-not-covered condition**, not a clean
"no island" positive over the region the island is actually in.

The two probe decks settle where the crossing actually is: together they cover
−45…+50 mV at 2.5 mV spacing (39 points) and find none. Combined with the earlier
`l54u-crossing-probe/` (±200 mV at 20 mV spacing), the l=5.4u build shows **no
pbit crossing anywhere in ±200 mV**, now confirmed at 2.5 mV resolution inside
−45…+50 mV.

## What this means for the option-(b) re-baseline

Option (b) re-baselines the n=8/n=20 island-rate sample on the surviving l=5.4u
v7-merged build on the premise that it is the trim comparator that produced the
l=483u island logs. That premise is now **measured false**: the l=5.4u build does
not reproduce the l=483u decision crossing in ±200 mV, let alone the island.
Absence outside ±200 mV is NOT measured — this is a bounded negative, not a claim
that the l=5.4u comparator never crosses anywhere. But the comparability premise
of the re-baseline is broken, and the question returns to the operator: either the
lost l=483u source resurfaces, or the island-rate tightening (G-12 done-when #3)
cannot be re-based onto the surviving build. 5.75x is unchanged — it rests on dead
codes and monotonicity, not on the island rate.

## Deck/log identity (sha256)

| file | sha256 | role |
| --- | --- | --- |
| `val540.cir` | `91440822…` | `--nomismatch` validation deck, codes 540-543 |
| `val540.ngspice.log` | `b716dc1b…` | full native ngspice output (109 transients) |
| `val540_markers.txt` | `07ca2788…` | parsed OFFSET/ANCHOR/BAND markers |
| `parse_val540.py` | `4f175818…` | parser for the markers |
| `probe540.cir` | `1b11f5fa…` | code-540 crossing probe, −45…+5 mV |
| `probe540.log` | `39c434d6…` | native log |
| `probe540b.cir` | `5a1c73f4…` | code-540 crossing probe, +7.5…+50 mV |
| `probe540b.log` | `6d2c73a2…` | native log |

The `val540.cir` and `probe540*.cir` decks carry the container run paths for their
`.include`/`.lib` lines. They map onto the parent directory:
`/tmp/C169-final.spice` → `../C169-SOURCE-coarse-dac-v7-merged.spice`
(`97938952…`) and the `C156-ISOBUF-PBIT_OUT.spice` workspace path →
`../C156-ISOBUF-PBIT_OUT.spice` (`81c708e1…`). All three decks retain the two
inert `VEDP`/`VEDN` force-biases (H-1343: `vedp#branch = 0`, `vedn#branch = 0`).

Known deck-documentation defect: `probe540b.cir` copies `probe540.cir`'s header
comment ("Sweep vv = −45 .. +5 mV") while its actual loop sweeps `vv` from +7.5 to
+50 mV (differential, 2.5 mV steps). The native log's `PROBE 540` lines are the
authority; the header comment is stale.

## Run requirement

ngspice must start from `/foss/pdks/ihp-sg13g2/libs.tech/ngspice` with
`PDK_ROOT=/foss/pdks PDK=ihp-sg13g2`, or the IHP PSP models fail to load
('Unknown model type psp103va' / 'model name is not found').
