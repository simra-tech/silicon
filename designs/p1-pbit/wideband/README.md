# P1 p-bit under physically calibrated broadband noise

This replaces [`../rate-map/`](../rate-map/), which is withdrawn. That note measured the
p-bit under a synthetic 1,000-tone excitation whose amplitude had no stated derivation and
whose spectrum stopped at f_clk/2. Both mattered. This one uses ngspice `trnoise` at an
amplitude derived from a `.noise` analysis of the VBIC model at the operating bias, flat to
~50 GHz.

234 runs across seven sampling rates, plus a deterministic offset sweep. Decks, logs and
extracted bitstreams for every run.

## 1. Adjacent-bit correlation does not depend on sampling rate

Every rate below is measured from **all** segments present in `rate-map/`, by one method, in
one pass. The segment counts in this table and the file counts in the directory are the same
numbers — see the correction note at the end of this section for why that needed saying.

| f_s (GS/s) | segments | bits | r₁ | P(1) |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 50 | 9,900 | +0.0103 ± 0.0130 | 0.5065 |
| 1.5 | 34 | 10,166 | +0.0033 ± 0.0090 | 0.4923 |
| 2.0 | 25 | 9,950 | +0.0042 ± 0.0107 | 0.5105 |
| 2.5 | 25 | 12,450 | +0.0149 ± 0.0100 | 0.5017 |
| 3.0 | 25 | 14,975 | −0.0075 ± 0.0092 | 0.5006 |
| 4.0 | 25 | 19,950 | +0.0075 ± 0.0069 | 0.5011 |
| 5.0 | 50 | 49,900 | +0.0081 ± 0.0039 | 0.4966 |

**Combined over all seven rates: r₁ = +0.0066 ± 0.0027** — 2.4σ from zero, χ² = 3.47 on 6 dof. Every value is
taken at a sampling phase of 0.9 T; see §1.1, which is not a footnote.

**No rate dependence is detectable.** The pooled value is 0.47× the derived limit of 0.0140.
At 2.4σ it is a weak positive hint rather than a detection: read |r₁| ≲ 0.01 as an upper
bound, not a null.

The 5.0 GS/s series is now contiguous 1–50. An earlier version of this note had to flag a
gap — segments 11–20 were missing — and those runs have since been done. 234 bitstreams, 234
logs, and the per-rate counts in the table are the file counts in the directory.

## 1.1. The sampling phase changes the answer more than the circuit does

r₁ is extracted by sampling the latch differential once per clock period. *Where* inside the
period was, until now, unstated in this note and unswept in the code that produced it. It
dominates the result.

**Which node, equally.** Everything in this note is measured on `v(xcomp.c_p) − v(xcomp.c_n)`,
the collectors of the cross-coupled latch pair. That was also unstated, and it matters as much
as the phase — see §1.3.

At 1.0 GS/s, sweeping the sampling instant across one period — same files, same circuit:

| phase | 0.1 T | 0.2 T | 0.3 T | 0.4 T | ≥ 0.5 T |
| ---: | ---: | ---: | ---: | ---: | ---: |
| r₁ | +0.0166 | −0.0162 | −0.0014 | −0.0061 | +0.0103 |

A swing of **0.033**, more than twice the 0.0140 limit this design is sized against, from a
choice nobody had written down.

**There is a plateau, and it has a physical cause.** Fine scan at 5.0 GS/s over 40 segments:

| phase | 0.50 T | 0.60 T | 0.65 T | 0.70 T … 0.99 T |
| ---: | ---: | ---: | ---: | ---: |
| r₁ | +0.0172 | +0.0087 | +0.0091 | +0.0090 (flat to 4 dp) |

The comparator is a regenerative latch. Before regeneration completes, the output node is
still moving, and a node still moving retains a trace of the previous decision — which the
arithmetic then reports as correlation. **Pre-plateau values measure the settling, not the
bitstream.** Every number in this note is taken at 0.9 T, inside the plateau at every rate.

### Where the plateau boundary comes from — and a caveat withdrawn

An earlier version of this section suggested the plateau might be an artefact of decks that
scale the clock waveform with the sampling rate, and warned that silicon's fixed slew would
shrink the settled window as the clock speeds up. **That was wrong, and it was published
without checking the decks it was a claim about.** They read:

```
1.0 GS/s   VCLK_P clk_p 0 PULSE(0.775 0.925 0p 20p 20p 400.0p 1000.0p)
5.0 GS/s   VCLK_P clk_p 0 PULSE(0.775 0.925 0p 20p 20p  80.0p  200.0p)
```

Rise and fall are **20 ps at every rate** — already fixed, already what silicon does. What is
held constant is the *duty cycle* at 40 %, which is an ordinary design choice one would also
make in hardware.

That explains the boundary exactly. The clock's falling edge completes at 20 ps + pulse width,
and the plateau opens essentially there:

| f_s | period | falling edge done | plateau opens |
| ---: | ---: | ---: | ---: |
| 1.0 GS/s | 1000 ps | 440 ps | ~500 ps |
| 2.0 GS/s | 500 ps | 240 ps | ~250 ps |
| 5.0 GS/s | 200 ps | 120 ps | ~120 ps |

### Inside the plateau, the choice does not matter at all

§1.1 shows the phase dominating the answer, which raises the obvious question of how much the
published figures depend on having picked 0.9 T. The answer is: not at all. Pooled r₁ over 50
segments, scanned across the whole settled region:

| 5.0 GS/s (plateau opens 0.61 T) | 0.65 T | 0.70 T | 0.80 T | 0.90 T | 0.99 T |
| --- | ---: | ---: | ---: | ---: | ---: |
| pooled r₁ | +0.0082 | +0.0081 | +0.0081 | +0.0081 | +0.0081 |

| 1.0 GS/s (plateau opens 0.44 T) | 0.50 T | 0.60 T | 0.80 T | 0.90 T | 0.99 T |
| --- | ---: | ---: | ---: | ---: | ---: |
| pooled r₁ | +0.0103 | +0.0103 | +0.0103 | +0.0103 | +0.0103 |

Identical to four decimal places across the entire plateau, at both the best- and worst-resolved
rates, with the standard error unchanged too. So the two halves of §1.1 are both true and not in
tension: **outside** the settled region the sampling instant changes the answer by more than
twice the design limit; **inside** it, every choice gives the same number. 0.9 T is not a tuned
value, it is an arbitrary point in a flat region — which is what makes quoting it honest rather
than merely reproducible.

**The rule is not a fraction of the period at all: sample after the latch clock edge has
completed.** Regeneration after that is fast — tens of ps at most, within the resolution of
these scans. It looked like a fixed fraction only because the duty cycle is fixed.

**There is a rate ceiling, and it is above where we run.** The settled window needs
0.6 T > 20 ps + t_regen. With regeneration in the tens of ps that puts the ceiling somewhere
around 7.5–15 GS/s — worth pinning down before anyone designs past 5, but not a constraint on
the results here. Measuring t_regen directly is the outstanding item.

### Correction to the previous version of this table

The version published on 2026-07-28 reported combined r₁ = +0.0060 ± 0.0046 over three
rates. Two things were wrong with it, neither affecting the conclusion:

- **Its per-rate segment counts did not match the files shipped beside it.** The table
  accounted for 139 segments; the directory contained 169. The table had been computed while
  the sweep was still running and the harvest was taken later, so each described a different
  moment. A reader who recounted the directory would have found more data than the table
  claimed to use, with no way to tell which was authoritative.
- **Its 5.0 GS/s row pooled a repeat set that is not part of this family.** That row read
  +0.0079 ± 0.0061; the 10 segments actually present here read +0.0150 ± 0.0077.

Both are now fixed by re-measuring every rate from the files as they stand. 5.0 GS/s has since
been taken from 10 segments to 50, which is why its row moved from +0.0150 ± 0.0077 to
+0.0081 ± 0.0039 and why the pooled error fell from ±0.0034 to ±0.0027.

**The withdrawn note reported +0.0192 to +0.0596 across the same rates, every value
positive, rising 1.79× with clock rate.** That rise, and most of that magnitude, was the
stimulus. Two defects produced it: a guard excluding tones near clock submultiples carved a
comb of spectral gaps (a comb in frequency is a comb in lag), and the band stopped at
Nyquist. Band-limiting is not cosmetic — imposing a 2.5 GHz limit on *this* source reverses
the sign of r₁, from −0.04 to +0.13.

**Read this as an upper bound, not a null.** |r₁| ≲ 0.01 is what the data supports.

## 2. Offset sensitivity — the number that constrains the design

Two gains, and they differ by fifty times. Quoting either alone is misleading.

| | method | gain |
| --- | --- | ---: |
| **static** | `.op`, unclocked, no regeneration | **−6.29 V/V** |
| **operational** | transient, latch running at 5 GS/s | **+307 V/V** |

The static figure describes the preamplifier. The operational figure describes the machine:
a regenerative latch resolves rail-to-rail once a small offset decides which way it topples,
so its effective gain dominates. An `.op` analysis cannot see this and understates the
sensitivity by the latch's own gain.

Consequently:

| input offset | output bias |
| ---: | ---: |
| **12.8 µV** | **1 %** |
| 128 µV | 10 % |

**Bias costs entropy directly, so this is a specification limit rather than a
characterisation curiosity.** The mismatch figure this section previously quoted —
σ_VOS = 6.46 mV, attributed here to a 200-sample Monte Carlo against the PDK mismatch model —
**is reported, not verified, and this note stated its provenance more confidently than the
evidence supports.**

Auditing it: no Monte Carlo artefacts exist on disk — no outputs, no logs, no generating
script. The only deck referencing mismatch selects `cornerHBT.lib hbt_typ_mismatch`, which is a
corner-library choice rather than a 200-sample sweep. The design specification it came from
labels the row *Specified*, which is more careful than the sentence that appeared here. The
figure may well be right and the run may have happened without leaving artefacts; what is
certain is that **it cannot be substantiated from this repository, and it should not have been
written as a measurement.**

The qualitative conclusion does not depend on it. Bipolar pair mismatch of *any* plausible
magnitude — hundreds of microvolts upward — is one to three orders above the 12.8 µV that costs
a percent of duty cycle, so **offset compensation is not optional for this design** regardless.
What does depend on the number is the *trim range*, which is sized in σ: until σ_VOS is measured
with a run that leaves artefacts, treat range decisions derived from 6.46 mV as provisional.

### How much residual offset is allowed

The 12.8 µV figure states a sensitivity, not a budget. The budget follows from the same
min-entropy assumption used elsewhere in this repository: H∞ ≥ 0.98 means P(1) ≤ 0.506980,
so the duty-cycle error allowed is **0.698 %**, i.e. a residual input offset of **8.9 µV**.

| residual duty error | H∞ per bit | |
| ---: | ---: | :--- |
| 0.031 % | 0.99911 | |
| 0.177 % | 0.99490 | |
| 0.382 % | 0.98908 | |
| 0.698 % | 0.98000 | **budget** |
| 3.06 % | 0.91458 | fails |

Two consequences for any compensation scheme:

- A **digital trim DAC** is limited by half an LSB. Over a ±40 mV correction range, 10 bits
  leaves 39.2 µV → 3.06 % duty error, which fails; 12 bits fails at 0.765 %; **13 bits is
  the minimum** and 14 gives margin.
- A **continuous servo** is limited by its own sampling floor, not by its amplifier gain. A
  servo nulls the duty error it measures, and over N averaged bits an unbiased source still
  shows a fluctuation of 0.5/√N which the servo cannot distinguish from real offset and so
  injects back. At 5 GS/s a 16 µs time constant averages 8×10⁴ bits and injects 0.177 % —
  inside budget, but six times larger than an amplifier-gain estimate would suggest. Driving
  that floor to 0.031 % needs 2.6×10⁶ bits, a 306 Hz loop, and ~520 pF of integrating
  capacitance, which is more die area than the signal path it protects.

**This budget shares its allowance with correlation.** r₁ = +0.0066 already consumes part of
the same 0.98, so the full 0.698 % is not available for bias alone. And because it rests on
the first-order Markov assumption *we* supplied (see §3), it is a floor.

## 3. What is *not* claimed

- **No entropy figure.** 200 ns yields 200–1,000 bits per run; SP 800-90B estimators want
  ≥10⁶ samples, needing a ~1 ms transient — unreachable in any SPICE. The defensible route
  is to extract physical parameters here and drive a stochastic model. r₁ is a circuit
  measurement; min-entropy is not.
- **No correlation "limit" is cited as a standard.** The 0.0140 figure used elsewhere in
  this repository follows from PTG.2.2's H∞ ≥ 0.98 under a first-order Markov model *we*
  supplied. Neither AIS-31 nor NIST SP 800-90B publishes a correlation limit, and since the
  assumption does not err in our favour, 0.0140 is a floor.
- **No claim that XOR whitening solves correlation.** It does not: for adjacent bits,
  P(X ⊕ X′ = 1) = (1 − r₁)/2, so correlation becomes *bias*. XOR cannot create entropy and
  is not a vetted conditioner for full-entropy claims.
- **Simulated bits, not silicon.** No layout, DRC, LVS or PEX.

## 4. Method notes worth carrying

- **Completeness is the transient end time, not the file size.** `trnoise` uses adaptive
  stepping, so complete runs differ by hundreds of bytes; a size test flags them as
  truncated.
- **Do not gate segments on their own output.** An earlier version discarded runs whose
  latch mean sat far from zero. That mean carries ~8 mV of sampling error at this window
  length (the latch differential is 221 mV rms), so the gate was selecting on noise. Both
  gated and ungated figures are reported above; they agree.
- **Precision comes from pooling, not from grinding one rate.** Per-rate ±0.005 needs ~110
  segments; pooling seven rates reaches ±0.0027 with what is here.
- **Measure the files you publish, and publish the count you measured.** A table computed
  while a sweep is still running, shipped next to a harvest taken later, disagrees with its
  own directory — and the reader cannot tell which is authoritative. The first version of
  this note did exactly that. Re-measuring from the shipped files costs minutes and is the
  only way the two can be checked against each other.
- **Sweep every free parameter in the extraction before trusting a number from it.** The
  sampling phase (§1.1) was a free parameter sitting in plain sight in the analysis code, and
  it moved r₁ by more than twice the design limit. It is the fourth time in this project that
  a result turned out to depend on a measurement choice rather than on the circuit — after the
  synthetic stimulus, the clock-submultiple guard, and the noise bandwidth. The parameters
  that cost the most are the ones so obvious they read as apparatus rather than as choices.
- **Extending a low-N point tests the error bar, not just the precision.** When 2.5, 3.0 and
  4.0 GS/s went from 10 segments to 25, all three moved *within* their old error bars. Other
  measurements in this project did not, and in each of those cases the error bar was
  concealing a systematic rather than reporting noise. The check is cheap and it does not
  require having guessed what the systematic might be.

## Contents

```
generate_rate_map.py                       deterministic deck generator
rate-map/bits_{rate}_seg{n}.txt            234 extracted bitstreams
rate-map/ngspice_{rate}_seg{n}.log         234 logs, one per bitstream
rate-map/tb_p1_{rate}_seg1.spice           7 decks, one per rate
offset/bits_dcgain_{0..500}uv.txt          bit-level offset sweep
offset/{tb_p1,ngspice}_dcgain_*            its decks and logs
offset/{tb_p1,ngspice,pbit_op}_offset_*    the static .op sweep
```

Decks other than the per-rate representative are omitted: each is ~1.9 MB of PWL-free
netlist plus generated content and all regenerate from `generate_rate_map.py` and the seed.
Flagged rather than quietly taken.

## Reproducibility — what these decks do and do not give you

Run `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2 installation. **You will
not get the bitstreams shipped here.** You will get different ones, drawn from the same
distribution.

The decks carry no seed. Two production decks for the same rate — say `tb_p1_5.0g_seg1` and
`_seg2` — are byte-identical apart from a comment line and their output filenames: same
circuit, same `TRNOISE(3.357827e-04 2.0p 0 0)`, no `rndseed` anywhere. Their outputs have
different checksums. ngspice reseeds its noise generator per process.

That cuts both ways and both halves matter:

- **It is why the statistics are valid.** Each segment is an independent realisation, which is
  what pooling and the quoted standard errors require. Had ngspice used one fixed default
  seed, all 50 segments at 5.0 GS/s would have been the same run repeated and every error bar
  in this note would have been meaningless.
- **It is why the bits are not reproducible.** A deck here specifies a *distribution*, not a
  realisation. Reproducing a specific bitstream would need `set rndseed` in a `.control`
  block, which these decks do not have.

So: the statistical results reproduce, run to run and by anyone. The individual bitstreams do
not, and are shipped as the record of what was actually measured rather than as something you
can regenerate. Checked by diffing the decks and their outputs, not assumed.

## 1.2. The edge-completion model, tested against a prediction made first

§1.1 proposes that the settled plateau opens when the clock finishes returning low, at
`delay + t_rise + pulse_width + t_fall`. That was inferred from the production decks, which is
weak evidence — the model was fitted to the same data it explains.

So a prediction was recorded before the measurement existed: build a deck differing from
production **only** in the clock, with a 50 % duty cycle instead of 40 %, and the plateau should
move from 440 ps to **525 ps** at 1.0 GS/s.

The deck was derived from `tb_p1_ac_wb10_1.0g_seg1.spice` by substituting the two `VCLK` lines
and the output paths, and verified by diff that nothing else changed. Both decks were then
scanned at 2 ps steps, one segment each, like for like:

| deck | t_rise / pulse / t_fall | predicted | measured | error |
| --- | ---: | ---: | ---: | ---: |
| production | 20 / 400 / 20 ps | 440 ps | **438 ps** | 2 ps |
| 50 % duty | 25 / 475 / 25 ps | 525 ps | **518 ps** | 7 ps |
| **shift** | | **+85 ps** | **+80 ps** | 5 ps |

**The model holds.** Both boundaries land within 7 ps of prediction on a 2 ps grid, and the
predicted shift is right to 6 %.

**Then it was tested again by someone else.** The Design Engineer independently rebuilt the
50 % duty experiment with its own generator — deriving each deck from the production file and
printing the production-vs-variant diff as an audit — and used 20 ps edges where the deck above
used 25 ps. Different author, different tooling, different edge rate:

| f_s | production pulse | variant pulse | predicted | measured | error |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1.0 | 400.0 ps | 480.0 ps | 520.0 ps | 524 ps | +4.0 |
| 1.5 | 266.7 ps | 313.3 ps | 353.3 ps | 353 ps | −0.3 |
| 2.0 | 200.0 ps | 230.0 ps | 270.0 ps | 272 ps | +2.0 |
| 2.5 | 160.0 ps | 180.0 ps | 220.0 ps | 216 ps | −4.0 |
| 3.0 | 133.3 ps | 146.7 ps | 186.7 ps | 188 ps | +1.3 |
| 4.0 | 100.0 ps | 105.0 ps | 145.0 ps | 149 ps | +4.0 |

**Mean +1.17 ps, spread 3.02 ps**, over six clock configurations none of which appear in the
production set. Artefacts in `duty-cycle/` are `*_clk50_*`.

### How precise is a single-segment boundary? Less than the scan grid suggests

Every boundary quoted above comes from **one segment**, scanned on a 2 ps grid — which invites
the reading that they are good to ~2 ps. They are not, and an accidental duplicate exposed it:
two decks with byte-identical clock lines gave 524 ps and 532 ps. Since ngspice reseeds its
noise per run (see *Reproducibility*), each segment carries its own realisation and the boundary
inherits that scatter.

Measured directly — all 10 segments of one configuration (20 / 480 / 20 ps at 1.0 GS/s):

```
524  516  518  524  528  512  526  516  520  516      mean 520.0   sd 5.2   s.e.m. 1.7 ps
```

**So the per-segment boundary is good to about ±5 ps, not ±2**, and the individual errors in the
tables above — mostly 0 to 4 ps — sit comfortably inside that. They should be read as consistent
with the model, not as evidence of a few-ps bias in either direction.

**Averaged properly, the agreement is exact.** The model predicts 20 + 480 + 20 = **520.0 ps**;
the 10-segment mean is **520.0 ± 1.7 ps**, a deviation of 0.0σ. The single-segment tables
understate the model's accuracy while overstating each measurement's precision — the two errors
happen to point in opposite directions, which is exactly why neither was visible without
measuring the estimator itself.

**5.0 GS/s is excluded from that table, and the reason is worth stating.** Production sets the
pulse width to 0.4 T; the rebuild sets it so that pulse + rise is 0.5 T. At T = 200 ps those
coincide — both give 80.0 ps — so the 5.0 GS/s "variant" deck is the production clock exactly.
It is not a duty-cycle point. It is an **accidental null-change control**, and it passed:
production measured 122 ps, the rebuild measured 122 ps. Same clock, independently derived deck,
separately run, separately extracted, identical answer. That tests the pipeline rather than the
model, which is worth having and was not planned.

**This is the confirmation that counts.** The seven production rates and the hand-derived deck
above were all measured by the same person who proposed the model, from decks built the same
way. These three were not. A model that only survives tests run by its author has not been
tested.

### Across all seven rates — and a correction to what this section first said

The two points above were then extended to every rate already on disk, same method, 2 ps steps,
`c_p − c_n`, one segment each:

| f_s | t_rise / pulse / t_fall | predicted | measured | error |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 20 / 400 / 20 ps | 440.0 ps | 438 ps | −2.0 |
| 1.5 | 20 / 266.7 / 20 ps | 306.7 ps | 308 ps | +1.3 |
| 2.0 | 20 / 200 / 20 ps | 240.0 ps | 246 ps | +6.0 |
| 2.5 | 20 / 160 / 20 ps | 200.0 ps | 198 ps | −2.0 |
| 3.0 | 20 / 133.3 / 20 ps | 173.3 ps | 173 ps | −0.3 |
| 4.0 | 20 / 100 / 20 ps | 140.0 ps | 139 ps | −1.0 |
| 5.0 | 20 / 80 / 20 ps | 120.0 ps | 122 ps | +2.0 |

**Mean error +0.6 ps, spread 2.8 ps**, over boundaries spanning 120 to 440 ps — a 3.7× range of
the quantity being predicted, across a 5× range of clock rate.

**This corrects an earlier version of this section.** From the first two points it reported that
both measurements sat *early* — 2 ps and 7 ps — and offered a mechanism: that the latch commits
once the clock has fallen far enough to cut off the track path rather than at the end of the
transition. With seven points the mean deviation is +0.6 ps and the residuals scatter both ways.
**There is no systematic early commit**; the pattern was two points and an invented explanation
for it. The single −7 ps point sits about 2.5σ out on the observed scatter and does not
establish a trend. The model needs no correction term: the boundary is
`t_rise + pulse_width + t_fall`.

This puts the rate ceiling of §1.1 on firmer ground: the settled window needs
`T − (t_rise + pulse_width + t_fall)` to remain positive with margin for regeneration, and the
model that predicts that boundary has now been tested out of sample rather than fitted.

```
duty-cycle/tb_dutyexp_1.0g_50pct.spice     the derived deck (clock lines only)
duty-cycle/ngspice_dutyexp_1.0g_50pct.log  its run log
duty-cycle/bits_dutyexp_1.0g_50pct.txt     199 bits extracted at 0.9 T
duty-cycle/{tb,ngspice,bits}_clk50_{1.0..5.0}g_seg1.*
                                           the independent rebuild, 20 ps edges
```

The raw transient (97 MB) is not shipped; the deck regenerates it in ~120 s.

## 1.3. Which node you sample changes the answer, and one node carries nothing

The comparator has more than one pair of nodes that could reasonably be called its output. All
results here use `c_p − c_n`, the collectors of the cross-coupled latch pair. A downstream pair,
`b_latch_p − b_latch_n`, is also written by the production decks. Scanning both over a full
period at 2 ps steps, **from the same run**:

| node pair | production (edge completes 440 ps) | 50 % duty (edge completes 525 ps) |
| --- | ---: | ---: |
| `c_p − c_n` | **438 ps** | **518 ps** |
| `b_latch_p − b_latch_n` | **994 ps** | **992 ps** |

Two separate points, and the second is the important one.

**`c_p − c_n` tracks the clock edge; `b_latch` does not settle inside the period.** 994 ps of a
1000 ps period leaves no usable sampling window at all.

**`b_latch` carries no information about the boundary.** Shift the clock edge by 85 ps and the
`c` boundary moves by 80 ps — that is the measurement. The `b_latch` boundary moves by −2 ps.
It is not a noisier version of the same signal; it is insensitive to the quantity under study,
so a dataset recording only that node cannot answer this question at any sample count.

So a correlation figure from this circuit needs **three** things stated to be reproducible: the
sampling phase (§1.1), the node pair, and the deck. Two of the three were missing from the
first version of this note. Both were found the same way — by sweeping a parameter that had
been treated as part of the apparatus rather than as a choice.
