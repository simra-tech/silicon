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

Convergence time scales with noise, as that mechanism requires. From twenty-five seeded runs:

| σ_n | 23.0 mV | 45.5 mV | 90.0 mV |
| --- | ---: | ---: | ---: |
| crossing cycle | 12,524 ± 1,489 | 23,560 ± 5,137 | 45,119 ± 11,263 |

Ratios 1 : 1.88 : 3.60 against noise ratios 1 : 1.98 : 3.91 — linear within the scatter.

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

The prediction moves by 3.9× across the sweep and the single-run measurements do not track it.
The baseline agreement was not evidence — that is the condition at which the expression's
coefficient was calibrated. (These six single-run spans are retained for provenance; the
noise-scaling subsection below supersedes them with twenty-five seeded runs, which do find a real
but much weaker noise dependence.)

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

### The band does scale with noise — an earlier version of this page said it did not

**This page previously stated that convergence time scales with σ_n while the settled width does
not. That was wrong**, for the same reason the 20-code outlier was wrong: the noise sweep in §1
also ran **one run per condition**, measured with the span. Twenty-five seeded runs
(`p1_25run_noise_powerlaw_campaign_results.csv`):

| σ_n (mV) | n | σ_code (LSB) | N_cross (cycles) |
| ---: | ---: | ---: | ---: |
| 23.0 | 10 | 2.121 ± 0.308 | 12,524 ± 1,489 |
| 45.5 | 5 | 2.664 ± 0.131 | 23,560 ± 5,137 |
| 90.0 | 10 | 3.503 ± 0.635 | 45,119 ± 11,263 |

A log–log fit gives **σ_code ∝ σ_n^(0.363 ± 0.049)**. Because there are only three distinct
x-values, the fit was repeated weighting the three group means by their own standard errors
rather than treating 25 points as independent: **0.362 ± 0.053**. The two agree, so the marked
heteroscedasticity between groups (sd 0.31, 0.13, 0.64) does not move the answer.

- **7.5σ from flat.** The dependence is real. The underpowered sweep did not merely fail to detect
  it — it reported the opposite.
- **13.1σ from linear.** The withdrawn σ_dither law had the wrong *exponent*, not a miscalibrated
  coefficient.
- **2.8σ below √σ_n.** A diffusion-versus-restoring-drift balance predicts 0.5.

**The exponent is not settled, and 1/3 is not claimed.** An earlier 15-run fit gave
0.306 ± 0.067 — 2.9σ from 0.5. Ten more runs halved the error and the gap held station at 2.8σ,
because the estimate itself rose to 0.363. An estimate drifting toward the hypothesis it is meant
to exclude, while its error contracts around it, is not converging away from that hypothesis.

#### A window confound was identified, tested, and found null

Above, `settled_std` was computed **from the crossing cycle to the end of the run**. Crossing takes
far longer at high noise, so the 90 mV group was measured over ~55,000 cycles against ~85,000 at
23 mV — the observation window was tied to the variable under study. The argument advanced here
was that a slow random walk observed too briefly under-reports its spread, that the bias would fall
hardest on the high-noise group, and therefore that **correcting it could only push α up toward
0.5**.

**That prediction was wrong.** Re-run at 200,000 cycles with `settled_std` taken over an identical
50,000-cycle window for every run (`p1_25run_fixed_window_powerlaw_campaign_results.csv`):

| σ_n (mV) | n | σ_code, fixed window | σ_code, crossing window |
| ---: | ---: | ---: | ---: |
| 23.0 | 10 | 2.069 ± 0.390 | 2.121 ± 0.308 |
| 45.5 | 5 | 2.644 ± 0.332 | 2.664 ± 0.131 |
| 90.0 | 10 | 3.477 ± 1.031 | 3.503 ± 0.635 |

**α = 0.366 ± 0.075** (weighted three-mean refit: 0.376 ± 0.078), against 0.363 before. All three
group means fell by about 2 %, in the same direction — no differential at all. The confound was
real in structure and **null in effect**: both window lengths were long compared with the walk's
correlation time, so truncation never bit.

**Correcting it cost precision.** The fixed 50,000-cycle window is shorter than the 55,000–85,000
it replaced, so each individual σ estimate is noisier and every group's scatter grew. The error on
α rose from 0.049 to 0.075, and the distance from √σ_n fell from 2.8σ to **1.8σ** — not because
the answer moved, but because our knowledge of it got worse. That is a real trade and it was worth
taking: a clean measurement with honest error bars beats a tighter one that cannot be trusted.

#### Five levels: the power law holds to 90 mV and breaks above it

α is a slope, so the error falls with the *spread* of the x-values, not only their count. Two extra
levels at 11.5 and 180 mV widened the lever arm from 3.9× to 15.7× and halved the error — ten runs
buying what roughly forty replicates at the existing points would have. Forty-five runs, five
levels, same fixed 50,000-cycle window, zero runs crossing after cycle 150,000
(`p1_45run_5level_noise_campaign_results.csv`):

| σ_n (mV) | n | σ_code (LSB) | N_cross |
| ---: | ---: | ---: | ---: |
| 11.5 | 10 | 1.527 ± 0.178 | 8,254 |
| 23.0 | 10 | 2.069 ± 0.390 | 12,524 |
| 45.5 | 5 | 2.644 ± 0.332 | 23,560 |
| 90.0 | 10 | 3.477 ± 1.031 | 45,119 |
| 180.0 | 10 | 3.176 ± 0.433 | 76,702 |

**A single power law over all five levels is rejected.** σ_code rises monotonically to 90 mV and
then falls. Weighted by the group standard errors, that fit gives **χ² = 15.4 on 3 dof, p ≈ 0.0015**.
The exponent it returns (0.275 ± 0.020) is not a measurement — it is where a straight line lands
when the data curves away from it.

**Over 11.5 – 90 mV, an eightfold range, the power law is excellent:**

    σ_code ∝ σ_n^(0.400 ± 0.038)      χ² = 0.16 on 2 dof

Dropping the 90 mV point instead of the 180 mV one does not rescue the five-level fit (χ² = 10.1),
so the departure is specifically at the top of the sweep and not general curvature.

- **10σ+ from flat** — the noise dependence is certain.
- **The withdrawn σ_dither law (α = 1) stays comprehensively dead.**
- **1.8σ above 1/3, 2.6σ below 1/2.** Still between them. **Neither exponent is derived from
  anything, and no mechanism is offered** — including for the flattening. A curve that rises and
  levels invites explanation, and this page has already withdrawn three mechanisms that were sound
  as arguments and absent from the data.

**Open, and what would settle it:** one more level at 360 mV — if σ_code stays flat the saturation
is real and worth explaining; if it resumes climbing, the 180 mV point was a fluctuation. Also ten
more seeds at 90 mV, whose group sd of 1.031 is 2–3× every other level (0.18, 0.39, 0.33, 0.43) and
which is one of the two points defining the departure.

Convergence time scales close to linearly with σ_n across all five levels — 8.3k, 12.5k, 23.6k,
45.1k, 76.7k cycles for a 15.7× noise range.

## 4. Not claimed

- **No silicon.** Schematic-level design; no layout, DRC, LVS or PEX.
- **Not a circuit simulation.** See the header. The loop dynamics are modelled, not simulated.
- **No certification.** Nothing here has been assessed against AIS-31, SP 800-90B or any other
  standard by anyone.
- **The band width has no working theory.** Over 11.5–90 mV it follows σ_n^(0.400 ± 0.038) with an
  excellent fit; above 90 mV it departs from that law. Nothing derives the exponent, nothing
  explains the departure, and no mechanism is proposed for either.

## Contents

```
run_dither_scaling_campaign.py           6-run sweep: 3 noise levels, 3 offsets
p1_dither_scaling_campaign_results.csv   its results, including M_target per run
run_closed_loop_route2_experiment.py     single 100k-cycle step response
p1_route2_closed_loop_trajectory.csv     its trajectory, clock_cycle,dac_code
run_10run_dither_scatter_test.py         10 seeded repeats, 5 at 10 mV and 5 at 20 mV
p1_dither_scatter_campaign_results.csv   its results, including settled_std per run
run_15run_noise_sweep_campaign.py        15 seeded runs, 5 each at 23.0, 45.5 and 90.0 mV
p1_15run_noise_sweep_campaign_results.csv  its results
run_25run_noise_powerlaw_campaign.py     25 seeded runs, endpoints extended to 10 each
p1_25run_noise_powerlaw_campaign_results.csv  its results; supersedes the 15-run fit
run_25run_fixed_window_campaign.py       same 25, 200k cycles, identical 50k measuring window
p1_25run_fixed_window_powerlaw_campaign_results.csv  its results; the window confound test
run_45run_5level_noise_campaign.py       45 runs over 5 noise levels, 11.5 to 180 mV
p1_45run_5level_noise_campaign_results.csv  its results; supersedes all earlier fits
```

The scripts write their outputs beside themselves and need only `numpy`. Verdicts in the
step-response script are computed against stated tolerances and can print `FAIL`; an earlier
version printed its conclusions as string literals and reported success on three runs that
measured three different things.
