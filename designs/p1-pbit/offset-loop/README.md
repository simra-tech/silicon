# Offset correction loop — closed-loop behaviour

> **This is a discrete-time behavioural model, not a circuit simulation.** No `ngspice` process
> produced any number on this page. The model's parameters are taken from SPICE measurements of
> the P1 chain (preamplifier gain, latch gain, noise RMS, trim DAC step), but the loop dynamics
> are simulated in Python. Read every result here as *what a loop with these parameters does*,
> not as *what this circuit does*.

The comparator carries an input offset. A servo cancels it: the comparator's own output bits
drive a 22-bit accumulator, whose top bits drive a trim DAC back into the preamplifier input.
The question is whether that loop actually works, how fast, and how accurately.

**It cannot be answered by counting output bits.** Our precision on output duty cycle is
~0.23 %, and the loop is specified to hold 0.072 %. A bitstream test passes whether the loop
works or not. So the loop is driven directly instead: displace the trim code, apply a step
offset, and record the register cycle by cycle.

## 1. Closed-loop accuracy

Six runs, 100,000 clock cycles each at 5.0 GS/s. For each applied offset the correct null code
is computed independently from the DAC step (`M_target = 131072 − V_step/ΔV_fine`), and the loop
is left to find it.

| σ_n (mV) | offset (mV) | correct null | settled mean | error (LSB) | dither span |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 23.0 | 10.0 | 114,727 | 114,726.70 | 0.30 | 12 |
| 45.5 | 10.0 | 114,727 | 114,728.39 | 1.39 | 14 |
| 90.0 | 10.0 | 114,727 | 114,725.62 | 1.38 | 13 |
| 45.5 | 5.0 | 122,899 | 122,900.48 | 1.48 | 14 |
| 45.5 | 10.0 | 114,727 | 114,727.87 | 0.87 | 13 |
| 45.5 | 20.0 | 98,382 | 98,381.46 | 0.54 | 20 |

**Residual error stays inside 1.5 LSB — under 0.9 µV — across a fourfold range of applied
offset.** This is the first closed-loop accuracy figure for this design.

### An independent cross-check falls out of it

The settled code moves **1,634.60 counts per mV** across the offset sweep (from the settled means
at 5 and 20 mV). The trim DAC step was derived separately, from the preamplifier transfer
function, as 0.6118 µV; 1 / 0.6118 µV = **1,634.52 counts per mV**. The two differ by 0.005 %,
and neither was fitted to the other.

## 2. Convergence

Starting 254 LSB below null with a 10 mV step, the register crosses the null code at **cycle
33,757 — 6.751 µs** at 5.0 GS/s (`p1_route2_closed_loop_trajectory.csv`, 100,000 rows).

**This refutes a τ_servo of 70.4 ns that appeared in an earlier specification.** That figure
assumed the accumulator advances 1 LSB every 16 clock cycles, which is the rate for a comparator
that leans decisively. This comparator sits in 45.5 mV of noise against a 10 mV offset, so its
output is barely biased; the accumulator *drifts* rather than slews. The correct order is
microseconds — still fine for a startup trim, and not a basis for any claim about tracking drift.

Convergence time scales with noise, as that mechanism requires:

| σ_n | 23.0 mV | 45.5 mV | 90.0 mV |
| --- | ---: | ---: | ---: |
| crossing cycle | 12,207 | 22,661 | 53,321 |

Roughly linear in σ_n over a fourfold range.

## 3. The residual band, and a law that did not survive

Once arrived, the loop does not sit on one code. It occupies a band whose within-run standard
deviation is **2.61 counts** (ten seeded runs; spans of 13–20 over 66,000-cycle windows), and its
mean sits a fraction of an LSB off null. **This band is the residual the loop cannot remove, so
it sets the useful resolution of the trim DAC: bits finer than the band buy nothing.** That makes
it the binding constraint on trim sizing, and it appeared in no specification because nobody had
noticed it was binding.

**A proposed scaling law for the band width is withdrawn.** It read

    σ_dither = σ_n / (√(2π) · A_op · A_static · ΔV_fine)

and predicted 14.99 LSB against a measured 16 at the baseline. The sweep above was run to test
it, and refutes it:

| σ_n (mV) | predicted (LSB) | measured (LSB) |
| ---: | ---: | ---: |
| 23.0 | 7.58 | 12 |
| 45.5 | 14.99 | 14 |
| 90.0 | 29.65 | 13 |

The prediction moves by 3.9× across the sweep; the measurement does not move. The baseline
agreement was not evidence — that is the condition at which the expression's coefficient was
calibrated.

### The 20-code span was scatter, and so was the flatness

The campaign above ran **one run per condition**. Ten seeded repeats settle what that could not
(`p1_dither_scatter_campaign_results.csv`, seeds 101–105 and 201–205):

| group | offset | spans | mean ± sd |
| --- | ---: | --- | ---: |
| A | 10 mV | 15, 17, 20, 15, 17 | 16.80 ± 2.05 |
| B | 20 mV | 15, 13, 17, 17, 16 | 15.60 ± 1.67 |

Difference 1.20 against a standard error of 1.18 — **t = 1.01, p = 0.33**. The 20-code span
dissolves.

**The same numbers retire the flatness claim as well.** Pooled scatter across the ten runs is
**1.87 counts**, and the six-run campaign reported 12, 14, 13, 14, 13, 20 from single runs.
Against that scatter those six values are one distribution: the sweep could not have detected a
real effect below roughly 5 counts in either direction. It legitimately killed the σ_dither law,
because that law predicted a 3.9× change which would have been visible. It never established
flatness, and this page previously implied otherwise.

**Use `settled_std`, not the span.** A span is `max − min`: an extreme-value statistic that grows
with observation length and scatters badly, which is why ten runs were needed to say anything.
The within-run standard deviation of the settled code is recorded in the same file and behaves:

| group | settled_std | |
| --- | ---: | ---: |
| A (10 mV) | 2.648 ± 0.374 | |
| B (20 mV) | 2.576 ± 0.322 | t = 0.33 |

**Any dependence of the band on applied offset is bounded below 0.44 counts of σ — under 17 % of
its value.** That is a specification-grade bound, and it came free from a column already on disk.

**What is left open.** Convergence time scales with σ_n and the settled width does not. Any
mechanism proposed for the band has to account for both; one that explains only the width is not
finished.

## 4. Not claimed

- **No silicon.** Schematic-level design; no layout, DRC, LVS or PEX.
- **Not a circuit simulation.** See the header. The loop dynamics are modelled, not simulated.
- **No certification.** Nothing here has been assessed against AIS-31, SP 800-90B or any other
  standard by anyone.
- **The band width has no working theory**, only sixteen measurements.

## Contents

```
run_dither_scaling_campaign.py           6-run sweep: 3 noise levels, 3 offsets
p1_dither_scaling_campaign_results.csv   its results, including M_target per run
run_closed_loop_route2_experiment.py     single 100k-cycle step response
p1_route2_closed_loop_trajectory.csv     its trajectory, clock_cycle,dac_code
run_10run_dither_scatter_test.py         10 seeded repeats, 5 at 10 mV and 5 at 20 mV
p1_dither_scatter_campaign_results.csv   its results, including settled_std per run
```

The scripts write their outputs beside themselves and need only `numpy`. Verdicts in the
step-response script are computed against stated tolerances and can print `FAIL`; an earlier
version printed its conclusions as string literals and reported success on three runs that
measured three different things.
