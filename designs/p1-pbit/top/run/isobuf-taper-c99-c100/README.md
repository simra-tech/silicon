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
