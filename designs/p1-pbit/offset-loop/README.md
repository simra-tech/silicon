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

#### There is no saturation, and σ_code at high noise is not yet a measurement

A sixth level at 360 mV was run, plus ten more seeds at 90 mV — 65 runs total
(`p1_65run_extended_noise_campaign_results.csv`). **The flattening is gone:** 360 mV gives
4.704 ± 1.125 against 4.038 at 180 mV. The curve does not level off, and the apparent saturation
was a fluctuation. No mechanism was proposed for it in the interval, which was the right call.

**But the same run exposes something that undermines every high-noise number on this page.** To
give the 360 mV runs room to converge, the simulation was lengthened from 200,000 to 300,000
cycles, and the fixed measuring window moved with it — from cycles 150,000–200,000 out to
250,000–300,000. The 180 mV group was re-run with **identical seeds 601–610 and identical
settings**:

| window | σ_code at 180 mV |
| --- | ---: |
| cycles 150,000–200,000 | 3.176 |
| cycles 250,000–300,000 | **4.038** |

Eight of ten individual runs rose; paired change +0.862, **t = 2.71**. Same circuit, same noise,
same seeds, later window, **27 % more spread**.

This is the truncation effect proposed earlier on this page, tested at 90 mV and below, found
null, and published as refuted. It was null there because the walk equilibrates quickly at low
noise. It is present at the top of the range — the one region that test did not cover. The
hypothesis was right; the test was run in the wrong place.

#### Two opposite biases, not one — a correction

An earlier version of this section concluded that **every high-noise σ_code is a lower bound**.
That was too simple and is withdrawn. Measuring σ_code over four successive windows for all 65
runs (`p1_65run_multiwindow_equilibration_results.csv`) separates two effects pointing in
opposite directions:

| σ_n (mV) | 100–150k | 150–200k | 200–250k | 250–300k | paired t (w4 vs w1) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11.5 | 1.462 | 1.527 | 1.548 | 1.477 | +0.30 |
| 23.0 | 2.057 | 2.069 | 1.965 | 2.155 | +0.57 |
| 45.5 | 2.562 | 2.644 | 2.885 | 2.698 | +0.62 |
| 90.0 | 3.098 | 3.420 | 3.559 | 3.654 | **+2.26** |
| 180.0 | 3.629 | 3.176 | 4.515 | 4.038 | +0.91 |
| 360.0 | 4.995 | 5.850 | 4.641 | 4.704 | −0.48 |

**≤ 45.5 mV: equilibrated.** All four windows agree within 5 %. Those figures stand.

**90 mV: appeared to be still growing** — a monotonic rise with paired t = +2.26. **This too was
an artefact, and is withdrawn below.**

**180 and 360 mV: unreadable, and biased the other way.** Counting walk-in intrusions per window:

| σ_n | runs intruding into w1 | w2 | w3 | w4 |
| ---: | ---: | ---: | ---: | ---: |
| 180.0 | 2 of 10 | 0 | 0 | 0 |
| 360.0 | **10 of 10** | 4 | 1 | 0 |

The walk-in is a long directed slide, so a window containing it **inflates** σ. That is why 360 mV
appears to *fall* across the windows — contamination washing out, not equilibration. Only its
fourth window is clean.

So the dataset carries **incomplete settling, which deflates late windows, and walk-in
contamination, which inflates early ones**. Absolute windows cannot separate them, and no
exponent should be fitted across the full range until they are separated.

**The fix removes the problem by construction rather than by audit:** define each window relative
to that run's *own* crossing cycle — crossing+50k to +100k, +100k to +150k, and so on — extending
N so every level gets four full windows. Then no window can contain any part of the approach at
any noise level, and comparing windows becomes a clean plateau test.

#### Aligned windows: nothing was drifting, and the exponent is now well determined

Re-measured with every window aligned to its own run's crossing cycle, and N extended per run so
all four windows are full (`p1_65run_relative_window_equilibration_results.csv`):

| σ_n (mV) | c+50–100k | +100–150k | +150–200k | +200–250k | paired t |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 11.5 | 1.560 | 1.435 | 1.532 | 1.537 | −0.28 |
| 23.0 | 1.982 | 2.090 | 2.075 | 1.975 | −0.05 |
| 45.5 | 2.661 | 2.336 | 2.754 | 2.838 | +0.24 |
| 90.0 | 3.456 | 3.492 | 3.414 | 3.512 | **+0.20** |
| 180.0 | 2.879 | 3.506 | 4.479 | 3.897 | +2.00 |
| 360.0 | 4.694 | 5.066 | 4.111 | 4.918 | +0.35 |

**The 90 mV drift is withdrawn.** Its paired t falls from +2.26 to +0.20; the level is flat.

**Why the absolute-window rise was spurious, which is the part worth keeping.** At 90 mV the
twenty runs cross anywhere between 12,000 and 74,500 cycles. An absolute window therefore mixes
runs at different stages of settling, and a later absolute window contains *the same runs, all
further along*. The group average climbs from window to window **even when every individual run is
stationary throughout**. That is why windows are defined relative to crossing here — not merely as
good practice, but because the absolute version manufactures a trend out of dispersion in arrival
times.

**The clean result.** Pooling the four aligned windows per run, over 11.5–90 mV — 45 runs, an
eightfold noise range:

    σ_code ∝ σ_n^(0.403 ± 0.013)      χ² = 0.26 on 2 dof

> **Correction.** An earlier version of this page attached "19.6σ from √σ_n" and "1.4σ from 1/3"
> to this fit. **Those distances belong to a different fit** — the all-six-level regression
> (α = 0.344 ± 0.008) that the same page had *rejected* on its χ² of 32.9 on 4 dof. Numbers were
> taken from a fit declared invalid and hung on a fit declared excellent, which is precisely the
> rule stated earlier on this page. For α = 0.403 ± 0.013 the correct distances are **5.4σ from
> 1/3** and **7.5σ from 1/2**. Superseded by the standardised fit below.

**A departure above 90 mV survives the fix.** Extrapolating the clean law to 180 mV predicts ≈4.59
against an aligned measurement well below it, and adding 180 mV to the fit takes χ² from 0.26 on
2 dof to 24.1 on 3. Its size and shape are corrected below.

#### Eight windows: 180 mV plateaus, and the first window under-reports

180 mV was extended to eight aligned windows and 128 mV was added
(`p1_targeted_180mV_128mV_results.csv`). Across the eight windows 180 mV reads

    2.879  3.506  4.479  3.897  4.028  4.050  3.962  3.691

— rising for three windows, then flat. **It equilibrates.** Windows 4–8 give
**3.926 ± 0.168** with no trend, so the four-window mean of 3.690 quoted above was **biased low**.

**Window 1 is too early, and this is the inverse of the problem it was built to solve.** It runs
from crossing+50k to +100k. That margin is ample against the *approach* — which is what it was
designed for — but not against the *spread-out*: immediately after the register arrives it is
still near where it arrived and has not yet diffused to full band width. Removing contamination
from the start of the measurement introduced a different bias in the same place, pointing the
other way. **All band estimates should therefore begin at crossing+100k**, applied to every level
rather than only where it matters — a rule applied selectively produces levels measured
differently.

#### It is a gradual rollover, not a break at 90 mV

Extrapolating the 11.5–90 mV law upward:

| σ_n (mV) | law predicts | measured | deficit |
| ---: | ---: | ---: | ---: |
| 128 | 3.997 | 3.792 ± 0.192 | **1.1σ** |
| 180 | 4.586 | 3.926 ± 0.168 | **3.9σ** |
| 360 | 6.063 | 4.697 ± 0.159 | **8.6σ** |

The deficit grows *monotonically* rather than appearing at a threshold, and 128 mV is consistent
with the law. **Describing this as a bend at 90 mV was reading a step into a curve**; it is a
gradual rollover that becomes detectable somewhere above 128 mV.

#### Standardised: window 1 dropped everywhere, 128 mV brought to eight windows

Seventy-five runs, seven levels, all band estimates starting at crossing+100k
(`p1_standardized_rw2_plus_results.csv`):

| σ_n (mV) | n | windows | σ_code |
| ---: | ---: | ---: | ---: |
| 11.5 | 10 | 4 | 1.501 ± 0.072 |
| 23.0 | 10 | 4 | 2.047 ± 0.204 |
| 45.5 | 5 | 4 | 2.643 ± 0.491 |
| 90.0 | 20 | 4 | 3.472 ± 0.492 |
| 128.0 | 10 | 8 | 3.583 ± 0.354 |
| 180.0 | 10 | 8 | 3.945 ± 0.417 |
| 360.0 | 10 | 8 | 4.679 ± 0.374 |

**Over 11.5–90 mV:**

    σ_code ∝ σ_n^(0.4095 ± 0.0166)      χ² = 0.62 on 2 dof

**4.6σ above 1/3 and 5.5σ below 1/2 — both simple candidates are excluded.** The exponent is a
value near 0.41 that nothing derives. It should not be described as "approximately a cube root";
that overstates what is known.

**The rollover begins below 128 mV, not above it.** Deficits against the clean law:

| σ_n | law predicts | measured | deficit |
| ---: | ---: | ---: | ---: |
| 128 | 4.011 | 3.583 ± 0.112 | **3.8σ** |
| 180 | 4.612 | 3.945 ± 0.132 | **5.1σ** |
| 360 | 6.126 | 4.679 ± 0.118 | **12.2σ** |

An earlier version called 128 mV consistent with the law at 1.1σ. That was computed with window 1
still included at that level, which pulled it upward. It is not consistent.

#### It reproduces on fresh seeds

The shape of this curve changed three times in three hours, every time because of how the
measuring window was drawn rather than because of the circuit. Before seeking any mechanism,
90 and 180 mV were re-run from **seeds never previously used**
(`p1_stability_confirmation_results.csv`):

| σ_n | fresh seeds | previous | difference |
| ---: | ---: | ---: | ---: |
| 90 mV | 3.505 ± 0.206 | 3.472 ± 0.110 | **0.1σ** |
| 180 mV | 4.184 ± 0.132 | 3.945 ± 0.132 | **1.3σ** |

Both reproduce. This is the first evidence that what is being measured is a property of the loop
rather than of the method.

#### Current pooled values — these supersede every figure above

Fresh runs pooled with the standardised set: 95 runs, seven levels, all estimates from
crossing+100k.

| σ_n (mV) | n | σ_code |
| ---: | ---: | ---: |
| 11.5 | 10 | 1.501 ± 0.023 |
| 23.0 | 10 | 2.047 ± 0.065 |
| 45.5 | 5 | 2.643 ± 0.220 |
| 90.0 | **30** | 3.483 ± 0.098 |
| 128.0 | 10 | 3.583 ± 0.112 |
| 180.0 | **20** | 4.065 ± 0.095 |
| 360.0 | 10 | 4.679 ± 0.118 |

    σ_code ∝ σ_n^(0.4102 ± 0.0153)      χ² = 0.58 on 2 dof   (11.5–90 mV)

**5.0σ above 1/3, 5.9σ below 1/2.** Both simple forms excluded. Deficits against the law:
**3.9σ at 128 mV, 6.0σ at 180, 12.4σ at 360.**

### 4. The exponent is set by the loop, not by the noise

Two hypotheses were tested (`run_hypothesis_tests_nsub_and_offset.py`). One is confirmed, one is
refuted.

**Confirmed: two timescales.** The accumulator advances the trim code only once per `N_sub`
sub-counts, so the loop has an inner and an outer rate. Changing `N_sub` moves the exponent:

| `N_sub` | α (11.5–90 mV) | χ² / 2 dof | σ_code at 90 mV |
| ---: | ---: | ---: | ---: |
| 4 | **0.476 ± 0.011** | 1.15 | 7.971 |
| 16 | 0.410 ± 0.015 | 0.59 | 3.483 |
| 64 | **0.284 ± 0.038** | 5.92 | 1.317 |

The extremes are **4.9σ apart**. The exponent is therefore not a property of the noise process —
it is a property of how often the loop is permitted to move.

**And the direction is physical.** As the divider shrinks, α climbs toward **1/2** — 2.2σ from it
at `N_sub` = 4 — which is the plain random-walk-against-restoring-drift limit. With a small
divider the code moves almost every cycle and behaves as a simple random walk; with a large
divider each code change is the average of many comparator decisions, which suppresses the wander
and flattens the noise dependence. **That is why no simple fraction fitted: the loop sits between
two regimes.** *Caveat: the `N_sub` = 64 fit has χ² = 5.92 on 2 dof, which is poor — 0.284 is
indicative, not measured, pending more seeds.*

**Refuted: the noise-to-offset ratio.** At 90 mV the noise is 2× the 10 mV offset and by 360 mV
it is 36×, so the rollover might have tracked the *ratio*. Holding σ_n at 180 mV and sweeping the
offset over a 16× range:

| offset (mV) | σ_n/offset | σ_code |
| ---: | ---: | ---: |
| 5 | 36.0 | 4.350 ± 0.116 |
| 10 | 18.0 | 4.152 ± 0.104 |
| 20 | 9.0 | 3.868 ± 0.113 |
| 40 | 4.5 | 3.857 ± 0.153 |
| 80 | 2.25 | 4.310 ± 0.158 |

No monotonic trend, and every value sits below the clean law's 4.629 at 180 mV. **The rollover
follows noise alone.** This also independently reconfirms the offset-independence measured earlier
at a different noise level.

**Procedural note, recorded against ourselves:** the predicted directions were asked for *before*
running and were not written into the script. The numbers are unaffected, but these are
demonstrations rather than pre-registered tests, and both interpretations above were formed after
seeing the data.

### The design lever this exposes

`N_sub` is not a law of nature — it is a chosen number, and it sets both the band width and its
noise dependence. The trade curve was then measured against a **pre-registered prediction written
into the script header before execution** (`run_tradecurve_nsub_campaign.py`), ten seeds per
setting at 45.5 mV:

| `N_sub` | settling | σ_code |
| ---: | ---: | ---: |
| 4 | 5,105 ± 401 cycles = **1.02 µs** | 6.110 ± 0.088 |
| 16 | 23,162 ± 1,413 = **4.63 µs** | 2.698 ± 0.051 |
| 64 | 103,729 ± 4,466 = **20.75 µs** | 1.077 ± 0.078 |

**Scoring the two pre-registered predictions:**

- *Convergence time ∝ `N_sub`* — **substantially confirmed.** Measured exponent
  **1.085 ± 0.031**, 2.8σ from the predicted 1.0: slightly steeper than proportional.
- *σ_code ∝ 1/√`N_sub`* — **refuted.** Measured **−0.600 ± 0.015** against a predicted −0.5,
  **6.5σ** away. Averaging more comparator decisions suppresses the wander *faster* than averaging
  independent samples would, consistent with the measured lag-1 correlation of +0.0066: the
  decisions the accumulator sums are not independent.

**The design curve, and where it stops being a single power law.** A fourth point at `N_sub` = 256
was run with the prediction again pre-registered, and with the intervals deliberately widened after
the calibration failure above:

| `N_sub` | settling | σ_code |
| ---: | ---: | ---: |
| 4 | 1.02 µs | 6.110 ± 0.088 |
| 16 | 4.63 µs | 2.698 ± 0.051 |
| 64 | 20.75 µs | 1.077 ± 0.078 |
| **256** | **91.9 µs** | **0.356 ± 0.026** |

**Both widened predictions landed inside their intervals** — the calibration correction took effect
in one round. Settling was predicted at 468,000 cycles and measured **459,671 ± 16,879**: 1.8 % out,
0.5σ.

- **Settling extrapolates cleanly.** Exponent across three successive 4× steps: 1.091, 1.082,
  1.074 — constant.
- **The band does not.** Its exponent steepens monotonically: **−0.590 → −0.662 → −0.799**. Over
  the full 4–256 range the trade exponent is **−0.632**, not the −0.552 fitted from the first
  three points, which is corrected here.

#### The quantisation hypothesis is refuted, and most of the bend was our own window

A quantisation explanation was proposed for the steepening: below one code a standard deviation
stops describing a spread and starts describing a register pinned to one code. It was tested with a
pre-registered prediction — modal-code fraction > 90 % and 2–3 codes at `N_sub` = 256
(`p1_discrete_occupancy_results.csv`).

| `N_sub` | σ_code | codes visited | modal fraction | rounded-Gaussian prediction |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 6.232 | 42.9 | 6.63 % | 6.39 % |
| 16 | 3.091 | 17.8 | 13.40 % | 12.85 % |
| 64 | 1.399 | 7.9 | 29.27 % | 27.92 % |
| 256 | 0.612 | 3.2 | **58.28 %** | **58.62 %** |

**Refuted.** At 256 the register visits 3.2 codes with 58 % modal occupancy, not > 90 %. And the
decisive check: the modal fraction at *every* divider matches what a Gaussian of the measured σ,
rounded to integers, would give — to within half a percentage point. **The code distribution is
fully explained by σ alone; there is no additional pinning.** (Both parties' predictions erred the
same way: 2 of 8 stated intervals hit, and all four modal-fraction predictions were too high.)

#### The larger problem the audit exposed

This audit reports σ_code = **0.612** at `N_sub` = 256. The extrapolation above reports **0.356**
for the same circuit, same 45.5 mV noise, same divider — **72 % apart.**

The cause is the window. The trade-curve and extrapolation scripts average σ computed *within*
separate 50,000-cycle windows; this audit computes one σ across a single **150,000-cycle** span. A
slowly-wandering register covers more ground the longer it is observed — and **the equilibration
time grows with the divider, which is the variable being swept.** So the short-window figures are
biased low, and biased worst exactly where the loop is slowest.

Refitting the band exponent on the consistent 150,000-cycle numbers:

| step | 150k window | 50k windows |
| --- | ---: | ---: |
| 4 → 16 | −0.506 | −0.590 |
| 16 → 64 | −0.572 | −0.662 |
| 64 → 256 | −0.596 | −0.799 |

**Most of the bend reported above is an artefact of the measuring window, not the circuit.** Some
steepening survives. **Band measurements require a window long compared with the loop's own
correlation time, and because that time grows with the divider, no fixed window is valid across a
divider sweep.** Whether even 150,000 cycles suffices at `N_sub` = 256 is itself under test.

#### The measurement has not converged, and no exponent is quotable

`N_sub` = 256 was re-measured over a 450,000-cycle contiguous window
(`p1_contiguous_window_trade_results.csv`):

| window | σ_code at `N_sub` = 256 |
| ---: | ---: |
| 50,000 | 0.3558 |
| 150,000 | 0.6118 ± 0.0565 |
| 450,000 | **0.7410 ± 0.0551** |

**Still climbing.** And the step ratios say what is happening: the first tripling multiplied σ by
**1.72**, against √3 = 1.73 — the signature of a **free random walk with no restoring force acting
inside the observation**. The second tripling gave only 1.21, so confinement has finally begun.
Every number quoted on this page came from somewhere on that transition, not from the confined
limit.

**The general rule.** Compare the window against each setting's *own* settling time, not against a
cycle count:

| `N_sub` | settling | 150k window as a multiple |
| ---: | ---: | ---: |
| 4 | 5,105 | **29.4×** |
| 16 | 23,162 | 6.5× |
| 64 | 103,729 | 1.45× |
| 256 | 459,671 | **0.33×** |

The same window is generous at one end of the sweep and inadequate at the other **by a factor of
ninety**. Of the four trade-curve points, **only the fastest has ever been measured over a clearly
adequate window** — the fitted exponent compares one converged measurement against three
unconverged ones.

> **No band exponent from this page is quotable.** The settling law (§ above) stands: it
> extrapolates cleanly over a 64× divider range and does not depend on the band measurement. The
> band *shrinks* with divider — that much is unambiguous. Its **slope is not established.**

**The fix, and the lesson underneath it.** Specify the window as a multiple of each run's own
crossing cycle. Note the shape of the error: the *start* of the window was made relative to each run
earlier on this page, and the *length* was left fixed in absolute cycles. **Both ends of a
measurement window must be defined relative to the thing being measured, not to the clock.**

#### Resolved: the trade law is an inverse square root

Re-measured with the window running from 2×crossing to 12×crossing for every run — equal
statistical opportunity relative to each setting's own dynamics
(`p1_relative_dynamic_window_trade_results.csv`, five seeds per point):

| `N_sub` | crossing | window span | σ_code |
| ---: | ---: | ---: | ---: |
| 4 | 5,383 | 53,826 | 5.837 ± 0.336 |
| 16 | 22,561 | 225,614 | 2.979 ± 0.064 |
| 64 | 103,639 | 1,036,386 | 1.496 ± 0.039 |
| 256 | 455,729 | 4,557,286 | 0.780 ± 0.024 |

    σ_code ∝ N_sub^(−0.4852 ± 0.0116)      χ² = 0.36 on 2 dof

**1.3σ from exactly −1/2**, and the local slopes are flat: −0.485, −0.497, −0.470. **The bend is
gone.** The band falls as the inverse square root of the divider — what a random walk under a
restoring force predicts, and the simplest answer available. It was there the whole time underneath
the measurement.

The pre-registered exponent interval [−0.480, −0.520] **hit**. The pre-registered absolute value at
`N_sub` = 256, [0.850, 1.150], **missed** — measured 0.780 ± 0.024, 3σ low. The scaling is
understood; the absolute scale is not.

**Cost, corrected:** the concern that this protocol might be unaffordable was wrong. The whole
four-point campaign ran in **under a minute** of wall clock, 46 s of it at `N_sub` = 256.

#### Settled: both exponents are one half

The α = 0.4102 ± 0.0153 reported earlier on this page — presented as excluding both 1/3 and 1/2 at
5σ — used **the same fixed-window protocol**, where the 50,000-cycle window was 6.1× the settling
time at 11.5 mV and 0.36× at 360 mV. Re-measured with windows scaled per run
(`p1_relative_dynamic_noise_results.csv`, six levels, five seeds each):

| σ_n (mV) | crossing | window span | σ_code |
| ---: | ---: | ---: | ---: |
| 11.5 | 7,989 | 79,886 | 1.547 ± 0.053 |
| 23.0 | 11,559 | 115,594 | 2.128 ± 0.117 |
| 45.5 | 23,560 | 235,602 | 2.985 ± 0.194 |
| 90.0 | 41,470 | 414,698 | 4.043 ± 0.187 |
| 180.0 | 83,729 | 837,294 | 5.982 ± 0.216 |
| 360.0 | 141,707 | 1,417,074 | 8.436 ± 0.255 |

    σ_code ∝ σ_n^(0.4939 ± 0.0121)      χ² = 1.16 on 4 dof

**0.5σ from exactly 1/2**, 13.2σ from 1/3. **The rollover is gone** — local slopes 0.460, 0.497,
0.445, 0.565, 0.496, with no trend. And the size of the correction is diagnostic: against the old
fixed-window values it is +3 % at 11.5 mV, +4 % at 23, +13 % at 45.5, +16 % at 90, **+47 % at 180**,
**+80 % at 360** — growing precisely with how slow the loop is at each setting, which is what a
too-short window produces, and accumulating into a fifth of an exponent across the sweep.

### The settled result

| quantity | exponent |
| --- | --- |
| band vs input noise | **+0.4939 ± 0.0121** |
| band vs accumulator divider | **−0.4852 ± 0.0116** |
| convergence time vs divider | **+1.085 ± 0.031** |

Both band exponents are **one half to within half a standard error**, and the design trade follows
exactly: **halving the residual error costs a factor of four in settling time** — not the 3.5
quoted earlier from biased data.

**Withdrawn from this page as artefacts of one defect:** the rollover above 90 mV, the bend in the
trade curve, the saturation, the exponent near 0.41, and the quantisation floor. One artefact, five
costumes — a fixed observation window while the observed process got slower.

### The absolute scale, previously open, now closed by a closed form

The open item below said we predicted how the band *changes* better than we predicted what it *is*.
That is no longer true. Treating the settled trim code as an Ornstein–Uhlenbeck process and
correcting for the lag-one correlation between accumulator steps gives, with **no fitted
parameters**:

    σ_band = π^(1/4) · √σ_n · √(1 + 2·R₁)  /  (2^(3/4) · √N_sub · √A_op · √ΔV_fine)

Substituting σ_n = 45.5 mV, N_sub = 16, A_op = 314.7, ΔV_fine = 0.6118 µV and the measured
√(1 + 2R₁) = 1.00658:

| | value (fine LSB) |
| --- | ---: |
| bare Ornstein–Uhlenbeck | 3.0423 |
| with the lag-one correction | **3.0624** |
| measured, 40 runs pooled | **3.0701 ± 0.0111** |

**+0.25%, or 0.70σ.** The two exponents were already 1/2; this fixes the prefactor as well, so the
band is now predicted rather than described. The correction factor is not a free knob — R₁ was
measured on the accumulator steps before being substituted here.

**Withdrawn: a correction this page made and got wrong.** A previous revision stated that the figure
above "was not a pooled value: it is one seed's Python result on its own", and replaced it with
3.0558 ± 0.0271 at 0.24σ. **That was our error, and the original figure was right.** The campaign CSV
contains 20 seeds per implementation, 40 measurements in total, and pooling all 40 gives 3.0701 ±
0.0111 — the originally reported value, to four decimal places. Our replacement came from five of
those twenty seeds, taken from a separate five-seed diagnostic file, after reading only the first
rows of the campaign CSV. That 3.070180 also happens to be the first row's value is a coincidence,
and we treated the coincidence as proof of a mistake. The agreement is 0.25% and 0.70σ, exactly as
first stated.

**What is deliberately *not* published from this dataset.** The 40 runs are 20 from a Python
implementation and 20 from an independent C reimplementation. They agree on the mean band to 0.4%.
They **disagree on its run-to-run spread by a factor of 2.10** — 1.40% against 2.95%, F = 4.41 on
(19,19) degrees of freedom, two-sided p = 0.0022, 95% interval on the ratio **1.32 to 3.34**. That
disagreement is unexplained after excluding the noise moments, the noise autocorrelation, the crossing
statistics, the accumulator arithmetic, the measurement window, the variance computation itself —
which the two agree on to 1×10⁻¹¹ when handed the same trajectory — and the correlation time of the
trajectories, on which they agree to 0.1%. Until it is resolved, the *mean* of this dataset is offered
and the *spread* is not, and the ± above is the standard error of the pooled mean, not a claim about
reproducibility.

**Which side is anomalous, and the formula that settles it.** The scatter of a sample standard
deviation over a correlated series is governed by the autocorrelation of *x²*, which for a Gaussian
process is ρ(k)² rather than ρ(k), and the expression carries a factor of two:

    rel. sd(σ̂) = √( (1 + 2·Σρ(k)²) / 2N )

An earlier revision of this page used √(τ_int/N) with τ_int = 1 + 2Σρ(k), which fails the
independent-sample check — it gives 1/√N where the classical result is 1/√(2N). With the correct
expression, and the per-seed window lengths averaged as variances rather than as an average N:

| | predicted | observed | ratio |
| --- | ---: | ---: | ---: |
| Python | 2.50% | 1.40% | **0.56×** |
| C reimplementation | 2.51% | 2.95% | **1.17×** |

**The C side matches sampling theory; the Python side is calmer than it permits by a factor of 1.8.**
Two intermediate revisions of this page got this wrong in both directions — first claiming C was the
well-behaved side on a formula that was incorrect, then claiming the two straddled the prediction on
observed values drawn from five of the twenty seeds. Both statements are withdrawn; the table above is
computed from all 20 per side with the corrected formula.

**Note on what "independent reimplementation" means here.** `sim_pbit_loop.c` implements **PCG32** — a
64-bit LCG state with a 32-bit XSH-RR output permutation, two outputs concatenated per double — and
draws normals by **Box–Muller**. NumPy's `default_rng` is PCG64 with ziggurat normals. Both generators
and both transforms are sound, and the LCG step and permutation are canonical, but they are not the
same stream: **the same seed produces different trajectories, with crossing times differing by up to
1.86×.** Every comparison between these two implementations is therefore a comparison of
distributions, never of trajectories, whatever the file names suggest.

### The loop's memory, also predicted from the constants

A second quantity falls out of the same Ornstein–Uhlenbeck treatment, and it is one no revision of
this page previously mentioned: **how long the trim register remembers.** The restoring time constant
is

    τ_corr = σ_n · N_sub / ( √(2/π) · A_op · ΔV_fine )  =  4,751 cycles  ≈  0.95 µs at 5 GS/s

which for an O-U process gives an exactly exponential autocorrelation, and hence a running
integrated time τ_int(M) = 1 + 2·τ_corr·(1 − e^(−M/τ_corr)). Measured against it, with the sample
mean subtracted and the truncation chosen adaptively:

| truncation lag M | theory | Python | C port |
| ---: | ---: | ---: | ---: |
| 100 | 198.9 | 197.2 | 197.2 |
| 500 | 950.2 | 940.9 | 940.4 |
| 1,000 | 1,804.5 | 1,785.1 | 1,783.2 |
| 2,000 | 3,265.7 | 3,222.8 | 3,219.7 |
| 5,000 | 6,185.8 | 6,028.1 | 6,053.0 |
| 20,000 | 9,361.5 | 8,811.0 | 9,240.2 |

**Within 1% over the first two decades of lag, with nothing fitted.** The two implementations agree
with each other to 0.01% at M = 100 and 0.1% at M = 2,000 — so whatever explains their disagreement
over the band's *spread*, it is not a difference in how long their trajectories remember.

Beyond M ≈ 20,000 the estimate stops being trustworthy: Python's running sum *falls*, from 8,811 to
8,086 at M = 50,000, which means the empirical ρ has gone negative and the sum is accumulating noise.
A value read at a fixed large truncation is a measurement of that noise, and an earlier attempt here
read one at a hardcoded 50,000.

**Why this matters beyond the band.** 0.95 µs of memory in the trim register bounds how fast the loop
can respond to anything that changes — temperature drift, supply movement, a re-trim after a mode
switch. No specification of this block has ever stated that number, and it is now derivable from four
constants rather than measurable only by simulation.

### Still open, stated as open

- **The design point.** There is an exact trade curve and **no stated startup-time budget for this
  chip.** The shape of the choice is known; which point to take is not, and that question is not a
  simulation.
- **The band's run-to-run spread**, now narrowed to a specific impossibility — see below.

### The spread is below the noise floor of the instrument measuring it

Two implementations agree on the mean band to 0.4% and on their trajectories' correlation time to
0.1%, and disagree on the band's run-to-run spread by **2.10×** (95% interval 1.32–3.34, p = 0.0022).
Cutting each settled window into 16 disjoint sub-windows of ≈248,500 cycles locates that disagreement
precisely, by testing the estimator *inside* a single run where seed-to-seed variation cannot reach it:

| | within-run scatter | Bartlett benchmark | ratio |
| --- | ---: | ---: | ---: |
| Python | 10.13% | 9.80% | 1.03× |
| C reimplementation | 9.45% | 9.80% | 0.96× |

**The estimator is sound on both sides.** That validated floor scales to the full window — sixteen
times longer, so a quarter the noise — giving a single-run noise floor of **2.45%**. Against it:

| | across-seed scatter | noise floor | |
| --- | ---: | ---: | --- |
| C reimplementation | 2.95% | 2.45% | ordinary; leaves ≈1.55% genuine seed-to-seed spread |
| Python | **1.40%** | 2.45% | **below the floor**, χ²₁₉ = 5.96, one-sided p = 0.0036 |

Twenty independent estimates of one quantity cannot cluster more tightly than the noise of the
instrument that produced them. Something is compressing them, and unlike every previous step this
constrains a mechanism instead of excluding one.

**Candidate, stated as a candidate.** Crossing time and measured band correlate at **−0.49** for
Python (t = −2.36, 18 dof) and **−0.12** for C. The measurement window is *derived from* the crossing
time — it starts at 2×crossing and ends at 162×crossing — so on the Python side the width of the
window is correlated with the quantity the window measures, and those twenty values are not twenty
independent draws under a common noise model. **Whether that accounts for the compression
quantitatively is not shown, and is not claimed.**

This has a shape worth flagging to anyone reusing the method. §3 of this page describes moving *from*
fixed windows *to* crossing-relative ones, to kill a real artefact in which the observation window
stayed fixed while the observed process slowed down — five apparent physics results that were one
defect in five costumes. That fix was correct. It may have introduced this subtler one: **an estimator
whose window depends on the quantity being estimated.** The test is a single fixed window common to
every seed, on the same trajectories, and it is pending.

Excluded so far: the noise moments, the noise autocorrelation, the crossing statistics, the accumulator
arithmetic, the variance computation, the correlation time, and now the single-run estimator itself.

*Calibration note, recorded against the prediction:* all six stated point intervals missed, yet the
underlying picture was substantially right. The intervals were too tight for what was known — a
calibration problem rather than a physics one, and visible only because the numbers were written
down first.

Convergence time, across six levels: 8.3k, 12.5k, 23.6k, 45.1k, 76.7k and ~140k cycles over a
31× noise range.

## 4. Not claimed

- **No silicon.** Schematic-level design; no layout, DRC, LVS or PEX.
- **Not a circuit simulation.** See the header. The loop dynamics are modelled, not simulated.
- **No certification.** Nothing here has been assessed against AIS-31, SP 800-90B or any other
  standard by anyone.
- **The band's run-to-run reproducibility.** The closed form above predicts the band's *value* to
  0.24σ, and both its exponents are 1/2. Its *spread* across seeds is a different matter: two
  independent implementations of the same loop disagree on that spread by a factor of four, and only
  one of them matches sampling statistics. No reproducibility figure is claimed.

  *This bullet previously read "the band width has no working theory" and quoted σ_n^(0.403 ± 0.013),
  a 5.0σ exclusion of 1/3, a 5.9σ exclusion of 1/2 and a rollover above 90 mV. Every one of those
  numbers came from the fixed-observation-window defect described in §3 and was withdrawn there; this
  page went on repeating them here, which is worse than either stating or withdrawing them once.*

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
p1_45run_5level_noise_campaign_results.csv  its results
run_65run_extended_powerlaw_campaign.py  65 runs, 6 levels to 360 mV, 300k cycles
p1_65run_extended_noise_campaign_results.csv  its results; supersedes all earlier fits
run_multiwindow_equilibration_audit.py   sigma_code over four successive windows per run
p1_65run_multiwindow_equilibration_results.csv  its results; the equilibration test
run_relative_window_equilibration_campaign.py  windows aligned to each run's own crossing
p1_65run_relative_window_equilibration_results.csv  its results; supersedes all earlier fits
run_extended_180mV_and_128mV_campaign.py  180 mV to eight aligned windows, plus a 128 mV level
p1_targeted_180mV_128mV_results.csv      its results; the plateau test
run_standardized_rw2_to_rw8_campaign.py  all levels, window 1 dropped, 75 runs
p1_standardized_rw2_plus_results.csv     its results
run_20run_stability_confirmation_test.py  90 and 180 mV from seeds never used before
p1_stability_confirmation_results.csv    its results; pooled with the above for current values
run_hypothesis_tests_nsub_and_offset.py  divider sweep and offset sweep
p1_hypothesis_test1_nsub_sweep_results.csv   divider sweep: N_sub 4 and 64
p1_hypothesis_test2_offset_sweep_results.csv offset sweep at fixed 180 mV noise
run_tradecurve_nsub_campaign.py          trade curve, prediction pre-registered in the header
p1_nsub_tradecurve_results.csv           its results: settling time against band width
run_nsub256_extrapolation_campaign.py    divider 256, prediction pre-registered and widened
p1_nsub256_extrapolation_results.csv     its results: the trade exponent bends
run_discrete_occupancy_audit.py          code occupancy per divider, prediction pre-registered
p1_discrete_occupancy_results.csv        its results: quantisation refuted, window discrepancy found
run_contiguous_window_trade_campaign.py  150k and 450k contiguous windows, prediction pre-registered
p1_contiguous_window_trade_results.csv   its results: the measurement has not converged
run_relative_dynamic_window_trade_campaign.py  window = 10x crossing, per run
p1_relative_dynamic_window_trade_results.csv   its results: the trade law resolves to -1/2
run_relative_dynamic_noise_campaign.py   noise sweep under the same relative-window protocol
p1_relative_dynamic_noise_results.csv    its results: the noise exponent resolves to +1/2
run_pcg64_c_equivalence_audit.py         5 seeds each side, Python and the C port, same generator
p1_pcg64_c_equivalence_results.csv       its results: the 10 runs pooled for the closed-form check
sim_pbit_loop.c                          the C port; build with gcc -O3 -shared -fPIC
run_sokal_adaptive_autocorr_tau_audit.py integrated correlation time, mean-subtracted, Sokal window
p1_sokal_adaptive_autocorr_tau_results.csv  its results: the running sum against truncation lag
run_20seed_and_16subwindow_audit.py      20 seeds a side, each window cut into 16 sub-windows
p1_20seed_and_16subwindow_results.csv    its results: within-run scatter beside the full-window band
```

The scripts write their outputs beside themselves and need only `numpy`. The equivalence audit also
needs `sim_pbit_loop.so` built from `sim_pbit_loop.c` in the same directory. Verdicts in the
step-response script are computed against stated tolerances and can print `FAIL`; an earlier
version printed its conclusions as string literals and reported success on three runs that
measured three different things.
