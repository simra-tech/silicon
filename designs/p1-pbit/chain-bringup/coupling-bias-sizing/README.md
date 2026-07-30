# Coupling bias sizing: ρ₁ is a function of sampling phase, and that is what picks the resistor

The interstage coupling network sets how long the chain takes to settle. At the original
**50 kΩ** bias (`XRB2_1`/`XRB2_2`, `rppd` 192 µm) settling takes ~100 ns, which makes every
corner measurement expensive and, under the 40 ns memory ceiling documented in
[`../pvt-convergence/`](../pvt-convergence/), sometimes impossible. Smaller bias resistors
settle faster. The question was how small.

**The answer is 50 µm / 13.02 kΩ — but not for the reason it first appeared, and the reasoning
matters more than the number.**

## The trap: ρ₁ moves more with sampling phase than with the resistor

A five-point sweep produced a clean-looking ranking: lag-1 correlation of **+0.0067** at 50 µm
against **+0.0330** at 192 µm, suggesting 50 µm as the winner by a factor of five.

That ranking does not survive scrutiny. Re-counting the bits from the same raw files while
sweeping the **sampling instant** across one 200 ps clock period:

| L (`rppd`) | R_bias | ρ₁ min | ρ₁ max | spread | phase window with \|ρ₁\| < 0.05 |
| --- | --- | --- | --- | --- | --- |
| 192 µm | 49.99 kΩ | +0.0000 | +0.4728 | 0.473 | **40 ps** |
| 100 µm | 26.04 kΩ | +0.0008 | +0.4892 | 0.488 | **40 ps** |
| **50 µm** | **13.02 kΩ** | +0.0014 | +0.4881 | 0.487 | **70 ps** |
| 30 µm | 7.81 kΩ | −0.0262 | +0.4716 | 0.498 | **70 ps** |
| 19 µm | 4.95 kΩ | −0.0118 | +0.4469 | 0.459 | **70 ps** |

Full per-phase data in [`phase-sweep.csv`](phase-sweep.csv) (5 configurations × 20 phases).

**The spread within any single configuration is ≈0.48. The difference between configurations
that the original ranking rested on is 0.026 — roughly twenty times smaller.** A ρ₁ value
quoted without its sampling instant carries almost no information about the circuit.

The mechanism is not subtle: sampling near the clock edge catches the output mid-transition,
so consecutive samples both reflect the same unresolved edge and correlate for that reason
alone. It is a measurement artefact, not circuit memory — but it is indistinguishable from
circuit memory in a single number.

> This page's author generated the contradiction and then the resolution. An independent
> recount of the same files gave ρ₁ = +0.2386 where the sweep reported +0.0330, which looked
> like a discrepancy in the sweep. It was not: the recount sampled at an arbitrary phase. The
> sweep's numbers reproduce at the phase it used. **The disagreement was entirely in the
> measuring method**, and testing that before reporting it is the only reason this page says
> what it says.

## What actually picks the resistor: the width of the usable window

The last column is the robust quantity. The sampling window over which the bits are
statistically independent (|ρ₁| < 0.05) **steps from 40 ps to 70 ps between 100 µm and 50 µm,
and does not widen further below it.**

That is a step change with a knee, not a point-value comparison inside a noise band, and it
survives the phase sensitivity rather than being produced by it. **50 µm / 13.02 kΩ is the
knee**, and it happens to be the same resistor the point-value ranking chose.

### It converts into a spec the block did not have

A 70 ps window out of a 200 ps period is a **clock-to-data alignment budget of about ±35 ps**
for the sampling circuit. At 192 µm it would have been ±20 ps. This is a real constraint on
the clock distribution path and belongs in the block specification; it was invisible while ρ₁
was being reported as one number per configuration.

**Open:** the window was measured at 27 °C only. If it narrows with temperature, the alignment
budget is set by the corner rather than by typical, and 70 ps at 27 °C would be the optimistic
figure. That measurement has been requested and is not yet done.

## Provenance, and one thing that does not check out

The five raw files are genuine: distinct sizes, sequential timestamps ~55 s apart, and titles
carrying the resistor value each was run at — headers reproduced in
[`raw-headers.txt`](raw-headers.txt). Each holds 30,001 points at 2 ps (60 ns). All numbers on
this page were recounted from them with [`count_phase.py`](count_phase.py).

Two caveats are recorded rather than smoothed over:

1. **The raw files contain no clock.** Their variable list is `time`, `v(pbit_out)`, `v(in_p)`,
   `v(in_n)`. With no clock signal the bitstream cannot be independently reconstructed — the
   sampling phase has to be *guessed*, which is precisely what produced the false discrepancy
   above. An export that cannot be independently recounted is not checkable. Adding `CLK_P` to
   the write list has been requested.
2. **The verification harness cited in the originating report does not exist.** That report
   listed `sweep_rbias_settling_and_correlation.py` and an ad-hoc runner
   `hermes-verify-rbias-*.py` under *"Verification Status: PASS (100% Convergence & Exact
   Resistor Scaling Verified)"*. Neither file is present anywhere on the filesystem. The
   underlying data is real and was independently confirmed here — so in this instance the
   claim happened to be true — but **the stated evidence for it was not evidence.** A PASS
   from a harness that cannot be produced on request is not a check, whatever the result
   turns out to be.

## Files

- [`phase-sweep.csv`](phase-sweep.csv) — ρ₁ and P(1) at 20 sampling phases × 5 resistor values
- [`count_phase.py`](count_phase.py) — the recount: parses the raw files, samples at a given
  phase, reports P(1) and ρ₁
- [`raw-headers.txt`](raw-headers.txt) — headers of the five source raw files
