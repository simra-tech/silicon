# Isolation buffer taper — C99/C100

**Status: candidate design change, simulation evidence only. Not a gate result, not signoff,
not tape-out evidence. The P1 gate remains open.**

The `iso_buf_pbit_out` isolation buffer as currently drawn delivers a much narrower and lower
output pulse into a real `sg13g2_IOPadAnalog` bond pad than the project had assumed. This package
records why, what fixes it, and what the fix costs.

## Summary

Driving the real PDK pad cell from the real comparator, 2.2 ns transient, `PBIT_OUT` above 600 mV:

| | as drawn (2 stage) | tapered (4 stage) |
|---|---|---|
| pulse 1 width | 44.50 ps | **138.55 ps** |
| pulse 1 peak | 0.659333 V | **1.190574 V** |
| pulse 2 width | not reached — run aborted at 1.399 ns | 142.13 ps |
| pulse 2 peak | — | 1.197960 V |

## The diagnosis

The buffer is two inverters. Stage 2 was deliberately sized to drive 520 fF in 50 ps and the
arithmetic for that is written into `C11-V2-ISOBUF-PBIT_OUT.spice`. Stage 1 was sized to match the
comparator's own output stage, so that the load the buffer presents to the core stays in family
with the unloaded lineage. Both decisions are individually sound.

Together they leave stage 1 — about 4.83 µm of transistor — driving stage 2's gate, about 43.2 µm.
**A fan-out of 9.** A tapered chain wants 3 to 4. The output stage is not short of drive; it is fed
too slowly to use the drive it has.

That risk is stated in the source file's own header, under a `RISK` heading, with the correct
estimate (~216 fF of stage-2 gate, ~149 ps of stage-1 delay), explicitly labelled as an estimate
pending a run. It was never run until now.

## The change

`C99-TAPER4-ISOBUF-PBIT_OUT.spice`. Four inverter stages so the buffer stays non-inverting:

| stage | geometry | total width |
|---|---|---|
| 1 | `w=2.83u`/`w=2.0u`, `m=1` — **byte-identical to C11-V2** | 4.83 µm |
| 2 | same geometry, `m=2` — added | 9.66 µm |
| 3 | same geometry, `m=4` — added | 19.32 µm |
| 4 | `w=14.4u m=2` / `w=7.2u m=2` — **the C11-V2 output stage, unchanged** | 43.2 µm |

Stage 1 is untouched **on purpose**: it is what the comparator has to drive, and the isolation
property of this buffer depends on it not growing. See "What we tried first and withdrew" below.

## Costs, measured

- **Latency: none measurable.** Output crossing 1.037029 ns tapered against 1.036376 ns as drawn —
  0.65 ps later with two extra gates in the path. Each added stage drives ~2× its own size, the
  ratio at which an inverter is fastest, so the delay is redistributed rather than added.
- **Backaction on the comparator: small but real.** Worst pointwise difference in
  `v(pbit_out_core)` is 62.5 mV, 5.3 % of its swing, at an instant during a transition. The core's
  peak (1.1615 V vs 1.1595 V) and its 0.6 V crossings (within 0.65 ps) are essentially unchanged.
  The likely mechanism is Miller coupling from stage 1's now-unburdened output node back to its own
  input. **That mechanism is a hypothesis; the 62.5 mV is measured.**
- **Area and power:** roughly 29 µm of additional transistor width, plus its switching power. Not
  quantified further here.

## What we tried first and withdrew

The first proposal was to leave the two-stage topology and simply make stage 1 larger. Measured
with a **PWL replay** of the comparator's recorded output, that looked excellent: doubling stage 1
took the pulse from 50.85 ps to 144.18 ps.

It is wrong, and the way it is wrong is worth recording. A replayed waveform cannot respond to
being loaded. Re-run with the live comparator driving:

| stage-1 multiplier | output pulse 1 | comparator peak |
|---|---|---|
| 1 (as drawn) | 44.28 ps | 1.1595 V |
| 2 | 43.44 ps | 0.9997 V |
| 3 | never clears 0.6 V | 0.8445 V |

Doubling stage 1 does not help and tripling it destroys the output, because the added gate is a
load on the comparator and stage 1 gets faster by stealing the signal it exists to pass along.
**That recommendation is withdrawn.**

## Method corrections recorded during this work

1. **PWL replay is only faithful at the load it was recorded at.** The replay used here was
   captured with a 44 fF output load. At 44 fF, replay and live chain agree to 8 fs and 0.27 mV. At
   210 fF the replay overstates the pulse width by about 15 % (50.85 ps replayed vs 44.28 ps live).
   Every replay-derived width in earlier reporting is optimistic by roughly that much.
2. **A hypothesis that the pad's loss term caused the deficit was falsified.** A plain 210 fF
   capacitor reproduces the real pad to within 2 %; adding the measured loss as a parallel resistor
   makes the result *worse* than the pad, not closer. The pad behaves as a plain capacitor about
   five times larger than the 44 fF stand-in the design was drawn against.
3. **The 210 fF lumped stand-in was then checked against the real pad and held.** It predicted
   44.28 ps and 141.89 ps; the real pad gives 44.50 ps and 138.55 ps.

## Corner check added 2026-08-06 — this candidate does not survive `mos_ss`

A partial corner check was run after publication: `cornerMOSlv` moved to `mos_ss` and `mos_ff`,
`cornerHBT` held at `hbt_typ`, on the same full chain into a lumped 210 fF load.

| corner / temperature | max `v(PBIT_OUT)` | pulse 1 above 0.6 V |
|---|---|---|
| `mos_tt` / 27 °C | 0.772905 V | 44.28 ps as drawn, 141.89 ps tapered |
| `mos_tt` / 125 °C | 1.187339 V | works, better than nominal |
| **`mos_ss` / 27 °C** | **0.000013 V** | **never clears — dead** |
| **`mos_ss` / 125 °C** | 0.001849 V as drawn, 0.000051 V tapered | **never clears — dead** |
| `mos_ff` / −40 °C | 1.219988 V as drawn, 1.246055 V tapered | 205.47 ps / 190.90 ps |

**Both buffers fail at the slow corner, tapered and as drawn alike.** Temperature is not the cause:
`mos_tt` at 125 °C works better than nominal, `mos_ss` at 27 °C is dead. Reproduced independently
in two sets of runs.

**Where it breaks, and why.** `v(pbit_raw_core)` — the comparator's decision node — is healthy at
`mos_ss`, keeping 0.539 V of swing. The signal dies across the following inverter, `xcomp.xm9`/
`xm10`: `v(pbit_out_core)` reaches only 24.9 mV.

The mechanism is **not** drive. That node's minimum is **0.658 V at `mos_ss`** against **0.338 V at
nominal** and 0.053 V at `mos_tt`/125 °C. The swing is ample; it sits entirely above the trip point
of the inverter that has to read it. Widening `xm9`/`xm10` would not help. This is a level-shifter
operating-point failure, and the level shifter is the `LS` block named in the deck lineage.

*(An earlier reading of the same data attributed this to undersizing — the same fault as the buffer,
one stage earlier. That reading was wrong and is corrected here. A recently-solved problem is a
dangerous hypothesis; it arrives already believed.)*

### The taper is not corner-neutral — it is corner-harmful

Amended a second time, 2026-08-06. Three independent comparisons, all in the same direction:

| condition | as drawn | tapered | tapered is |
|---|---|---|---|
| `mos_ss` / 125 °C | 0.001849 V | 0.000051 V | **36× worse** |
| `mos_ss` / 27 °C, converter `XM5`/`XM6` `m=4` | 0.001873 V | 0.000035 V | **53× worse** |
| `mos_ss` / 27 °C, converter `m=2` + `R`<sub>fb</sub> `l=37u` | 0.001380 V | 0.000031 V | **45× worse** |

Both are dead at that corner either way, but the four-stage taper is consistently more than an
order of magnitude deader than the two-stage buffer it replaces.

**Mechanism, now tested.** The taper changed two things at once: it added stages, and it made
stage 2 much smaller. Separating them, all at `mos_ss`/27 °C with the `m=4` converter:

| buffer | stages | stage 2 | max `v(PBIT_OUT)` |
|---|---|---|---|
| as drawn | 2 | 43.2 µm | 0.001873 V |
| small stage 2 | 2 | 9.66 µm | **0.003526 V** — slightly *better* |
| taper | 4 | 9.66 µm | 0.000035 V |
| longer taper | 6 | 4.83 µm | **0.000001 V** |

**Stage count is the variable; stage size is not.** Shrinking stage 2 while keeping two stages
improves the result. Going 2 → 4 → 6 stages costs roughly 50× per two stages added.

The reason tapering helps at nominal and hurts here is that a taper assumes every stage receives a
full-swing input and therefore restores the edge. Once the signal stops reaching the rails, each
stage attenuates instead of restoring, and a chain multiplies the loss.

**Consequence for this package:** the taper is a real and measured improvement at `mos_tt` and
`mos_ff`, and it is **actively harmful at `mos_ss`**. It is not a change that helps where it helps
and is neutral elsewhere. Anyone adopting it must treat the slow corner as a hard blocker to be
solved first, not as a place where this change merely fails to assist.

*(The first version of this note said only that the taper "is not sufficient" at the slow corner.
That was technically accurate and practically misleading, and is superseded by the table above.)*

### RETRACTED 2026-08-06 evening — "corner-harmful" is withdrawn

The three comparisons above rank outputs that are all dead. As the note itself says, "both are dead
at that corner either way": the largest number in that table is 1.9 mV and the pin's own stuck
level scores in that range by arithmetic. **Ranking two circuits that both produce nothing, by how
close to nothing they get, is not evidence about either.** The 36×/53×/45× ratios are differences
between non-working variants and carry no design information.

The stage-count table has the same defect. Every value in it is under 4 mV.

A clean measurement was made later the same day, with the buffer lifted out of the chain and driven
from ideal sources at `mos_ss`/125 °C into 210 fF — the method that should have been used here:

| input pulse width | as drawn, max `v(out)` | 4-stage taper, max `v(out)` |
|---|---|---|
| 100 ps | 0.006862 V | 0.003495 V |
| 140 ps | 0.019753 V | **0.674680 V** |
| 200 ps | 0.133800 V | 1.216644 V |
| 300 ps | **0.653118 V** | 1.239985 V |

**Minimum usable input pulse: as drawn 200–300 ps; taper 100–140 ps.** The taper needs roughly half
the input width the as-drawn buffer does — the opposite of "corner-harmful". The earlier ranking was
an artifact of comparing dead outputs at a corner where the converter upstream delivered only ~92 ps,
below the floor of *both* buffers, so neither could work and the comparison could not discriminate.

**What stands from this package:** the pad load measurement, the as-drawn buffer's inadequacy, and
the taper being a real improvement. **What is withdrawn:** that the taper is harmful at `mos_ss`,
and the claim that stage count rather than stage size is the harmful variable. Neither is supported.

### Superseded criterion — read the whole package with this in mind

Every number in this package, including the headline 44.50 → 138.55 ps, is *time above 600 mV*.
Later work established that this criterion is passed more easily by a circuit that merges several
bits into one wide pulse than by one that correctly resolves them, because a merged pulse is both
taller and longer. **The criterion rewards the defect.** It was replaced by decoding the output at
the bit clock and counting bit errors against the transmitted sequence, with the comparator's own
output decoded alongside as a reference.

Under that criterion the output path does not work: it delivers a 64-bit sequence with zero errors
only at 800 ps/bit and only at the three 125 °C corners; at slow silicon and 27 °C it needs
3200 ps/bit; and at `res_wcs`/−40 °C the output does not move at any rate tested. The width and
amplitude figures in this package remain correct as measurements. They are not evidence of function.

## Limitations

- One process corner (`mos_tt`), 27 °C, no mismatch, no statistical spread, no PVT sweep.
- **Neither C100 run completed.** Both abort with the timestep collapsing on the comparator's own
  VBIC device, `q.xcomp.xqs_comp.qnpn13g2`, preceded by a thermal-limiter NaN warning — a different
  failure from the pad-related stiffness. C100-B reached 1.9926 ns, past both output pulses.
  C100-A reached 1.3987 ns, so its second pulse is absent, not zero.
- Solver tolerances are loosened (`reltol=2e-2 abstol=1e-8 vntol=1e-3`); no tighter setting has
  ever completed a 2.2 ns run with this pad. The resulting offset was bounded at ~0.42 mV against a
  default-tolerance reference over the window where one exists, which maps to under 0.7 ps of
  pulse-width uncertainty even at a pessimistic 5× extrapolation.
- **600 mV is an unvalidated proxy.** No one on this board has checked it against what a real probe
  station's receiving instrument requires. Every width in this package is a width above a threshold
  nobody has justified.
- No bond wire, no probe model, no board, no package.

## Files

| file | what it is |
|---|---|
| `C11-V2-ISOBUF-PBIT_OUT.spice` | the buffer as currently drawn |
| `C99-TAPER4-ISOBUF-PBIT_OUT.spice` | the proposed four-stage taper |
| `C99-ASDRAWN-*.cir`, `C99-TAPER4-*.cir` | full chain into a lumped 210 fF load |
| `C100-A-*.cir`, `C100-B-*.cir` | full chain into the real `sg13g2_IOPadAnalog` pad |
| `C100-traces.csv` | `PBIT_OUT` and `pbit_out_core` for both C100 runs, 0.80–1.70 ns |
| `*-run.log` | stderr from every run, **including the aborts** |
| `RAW-SHA256SUMS.txt` | SHA-256 of the four binary raws (not shipped; 5.7–49 MB each) |

The raws are not included because of their size. Their hashes are recorded so a re-run can be
checked against them.

The decks are portable: `$PDK_ROOT` stands for the installed IHP SG13G2 root, the buffer includes
are relative to this directory, and the comparator source is referenced at
`../hybrid-ac-portable-c79/` where it was already published. That file is byte-identical to the one
these runs used **after** the absolute-path comments are scrubbed, which is the convention this
repository already applies to it; no electrical line differs.
