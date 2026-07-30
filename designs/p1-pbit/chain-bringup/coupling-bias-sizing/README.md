# Coupling bias sizing: ρ₁ is a function of sampling phase, and that is what picks the resistor

> ## RETRACTION — the window widths and the ±35 ps spec on this page are withdrawn
>
> **The 40 ps / 70 ps window widths below, and the ±35 ps clock alignment budget derived from
> them, are not supported by the data that produced them.** They come from classifying each
> sampling phase as pass or fail against a fixed |ρ₁| < 0.050 threshold. At the sample count of
> that sweep — **N = 291 bits per phase** — the standard error on a lag-1 autocorrelation is
> 1/√N = **0.0586**. The threshold sits at **0.85 standard errors**, i.e. *below the noise*.
> The window edges being reported are the shape of the noise, not a property of the circuit.
>
> **What survives:** the central finding of this page — that ρ₁ varies from ≈0.00 to ≈0.49 with
> sampling phase, roughly twenty times the difference between resistor values — is unaffected.
> Those large ρ₁ values are 6–8 standard errors from zero and are real. The choice of 13.02 kΩ
> also stands, on settling time.
>
> **What does not:** any window *edge*, any window *width*, and the alignment budget computed
> from one. To place an edge, the threshold must sit at 2–3 se, needing **≈1,600–3,600 bits per
> phase** (a 320–720 ns transient) against the 291 used here.
>
> **The general form**, which is the part worth keeping: with se = 0.059 you can detect strong
> correlation easily and you cannot certify its absence. **Proving a bitstream independent needs
> far more samples than proving it dependent** — and independence is this chip's entire product.
> Every "statistically independent" claim in this repository was made at a sample count that
> cannot support it.
>
> A pass/fail column turned a resolution limit into a specification. Tables below now report
> ρ₁ without one.

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

| L (`rppd`) | R_bias | ρ₁ min | ρ₁ max | spread | ~~window \|ρ₁\| < 0.05~~ (withdrawn) |
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

## ~~What actually picks the resistor: the width of the usable window~~ — WITHDRAWN

> **This whole section is withdrawn.** Its argument is that the window width is the robust
> quantity. It is not: at N = 291 the |ρ₁| < 0.05 test sits at 0.85 standard errors, so the
> widths in the last column are noise structure. The section is kept because the reasoning
> error is the instructive part — it replaced a fragile point-value comparison with something
> that *looked* robust and was measured at the same inadequate resolution. See the retraction
> at the top and the corner data below.

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

**That open question has since been answered, and it broke the section above.** The corner
measurement is below.

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

## The corner measurement, and why it withdrew the section above

The open question — does the usable sampling window narrow at temperature? — was answered by a
two-corner phase sweep at 13.02 kΩ, run with `CLK_P` exported so the bitstream could be
recounted against the real clock edges rather than a guessed phase. Both corners use the same
noise seed. Recounted here with [`count_phase_pvt.py`](count_phase_pvt.py); full data in
[`pvt-phase-sweep.csv`](pvt-phase-sweep.csv).

**N = 190 bits per phase, so se(ρ₁) = 1/√N = 0.0725.** Every number below is reported against
that, because it is the whole story.

| sampling phase | 27 °C ρ₁ | z | −40 °C ρ₁ | z |
| --- | --- | --- | --- | --- |
| 0–10 ps | +0.0242 | +0.33 | −0.0804 | −1.11 |
| 20–30 ps | +0.0231 | +0.32 | −0.0418 … +0.1423 | −0.58 … +1.96 |
| 40–50 ps | +0.0429 | +0.59 | **+0.2379 … +0.1699** | **+3.28 … +2.34** |
| 60–80 ps | +0.0626 … +0.1442 | +0.86 … +1.99 | +0.0242 … −0.0804 | +0.33 … −1.11 |
| 90–160 ps | **+0.1829 … +0.4505** | **+2.52 … +6.21** | −0.0804 … −0.0858 | −1.11 … −1.18 |
| 170–190 ps | +0.0994 … +0.0184 | +1.37 … +0.25 | −0.0858 | −1.18 |

### What is resolvable, and what is not

**Resolvable:** both corners have a genuinely correlated region, and *they sit at different
phases*. At 27 °C it is 90–160 ps, reaching ρ₁ = +0.45 at z = 6.2. At −40 °C it is 40–50 ps,
reaching +0.24 at z = 3.3. Those are real; a z of 6 is not noise.

**Not resolvable:** where the correlation *stops*. Every phase outside those bands sits within
about 1.2 standard errors of zero, and a |ρ₁| < 0.05 pass/fail test on data with se = 0.0725
is a test at 0.69 se — it partitions noise. The window edges, and any alignment budget computed
from their spacing, are not measurements.

A concrete illustration from the cold file: **phases 100 through 190 return the bit-for-bit
identical pattern** — one pattern, ten phases. That is the output sitting fully settled across
half the clock period, which is the signature of a *wide* safe window. A pass/fail test scored
that same span as failing, because the settled pattern happens to have ρ₁ = −0.0858.

### The asymmetry that matters for this chip

> With se = 0.0725 you can detect strong correlation trivially and you cannot certify its
> absence. **Establishing that a bitstream is independent requires far more samples than
> establishing that it is not** — and independence is this chip's entire product.

That is not a subtlety about this sweep; it applies to every ρ₁ figure in this repository. The
counted-bitstream, autocorrelation and PVT pages all report independence at sample counts
between 190 and 500, where se runs 0.045 to 0.073. Those runs are sufficient to have *detected*
the ρ₁ = 0.777 interface problem and to have confirmed the feedback fix removed most of it.
They are **not** sufficient to support the phrase "statistically independent" without a stated
error bar, and that phrase should be read as "no correlation detected at this resolution".

### There is also a stimulus-resolution limit

The generating deck ([`sweep_sampling_phase_pvt.py`](sweep_sampling_phase_pvt.py)) builds the
noise as a PWL with **`dt = 20 ps`**, while the phase axis is swept in 10 ps steps. The
stimulus cannot distinguish two phases inside one 20 ps segment, and the data shows it
directly — at 27 °C, phases 0/10, 20/30 and 40/50 return *bit-for-bit identical* patterns.
Those are not two agreeing measurements; they are one measurement printed twice.

**So the phase axis has a hard 20 ps resolution independent of sample count.** This is a second
and sufficient reason a ±10 ps alignment figure cannot come from this deck.

### What would settle it

Both limits have to be fixed together, since each defeats a fix to the other alone:

| limit | current | needed |
| --- | --- | --- |
| statistical | N = 190, se = 0.073 | N ≈ 3,600 (720 ns transient) for the 0.05 threshold to sit at 3 se |
| stimulus | noise PWL `dt` = 20 ps | `dt` = 2 ps, matching the timestep |

Both corners converge at a 5 ps maximum timestep, so a 720 ns run is ~144,000 points and well
inside what has already been written. Only the hot corner needs 2 ps.

**Until then the sampler alignment budget is unspecified.** What can be said is that phases
40–50 ps and 90–160 ps are measurably bad and should be avoided, which is a constraint on the
clock path even without a number attached to it.

## Files

- [`pvt-phase-sweep.csv`](pvt-phase-sweep.csv) — ρ₁, se and z at 20 phases × 2 corners
- [`count_phase_pvt.py`](count_phase_pvt.py) — the recount, aligned to `v(clk_p)` rising edges
- [`sweep_sampling_phase_pvt.py`](sweep_sampling_phase_pvt.py) — the generating deck
- [`pvt-raw-headers.txt`](pvt-raw-headers.txt) — headers of the two corner raw files
