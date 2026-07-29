# P1 p-bit under physically calibrated broadband noise

This replaces [`../rate-map/`](../rate-map/), which is withdrawn. That note measured the
p-bit under a synthetic 1,000-tone excitation whose amplitude had no stated derivation and
whose spectrum stopped at f_clk/2. Both mattered. This one uses ngspice `trnoise` at an
amplitude derived from a `.noise` analysis of the VBIC model at the operating bias, flat to
~50 GHz.

224 runs across seven sampling rates, plus a deterministic offset sweep. Decks, logs and
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
| 5.0 | 40 | 39,920 | +0.0090 ± 0.0047 | 0.4957 |

**Combined over all seven rates: r₁ = +0.0066 ± 0.0029** — 2.2σ from zero. Every value is
taken at a sampling phase of 0.9 T; see §1.1, which is not a footnote.

**No rate dependence is detectable.** The pooled value is 0.47× the derived limit of 0.0140.
At 2.2σ it is a weak positive hint rather than a detection: read |r₁| ≲ 0.01 as an upper
bound, not a null.

At 5.0 GS/s the segments are numbered 1–10 and 21–50; 11–20 were never produced. 40 files,
40 logs, and the table says 40. Flagged rather than renumbered.

## 1.1. The sampling phase changes the answer more than the circuit does

r₁ is extracted by sampling the latch differential once per clock period. *Where* inside the
period was, until now, unstated in this note and unswept in the code that produced it. It
dominates the result.

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
been taken from 10 segments to 40, which is why its row moved from +0.0150 ± 0.0077 to
+0.0090 ± 0.0047 and why the pooled error fell from ±0.0034 to ±0.0029.

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
characterisation curiosity.** Offset from mismatch between nominally identical bipolar
devices of this size is **σ_VOS = 6.46 mV**, from a 200-sample Monte Carlo against the PDK
mismatch model — five hundred times the offset that costs a percent of duty cycle, i.e. an
uncompensated part is not slightly biased but stuck at a rail. **Offset compensation is not
optional for this design.**

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
  segments; pooling seven rates reaches ±0.0029 with what is here.
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
rate-map/bits_{rate}_seg{n}.txt            224 extracted bitstreams
rate-map/ngspice_{rate}_seg{n}.log         224 logs, one per bitstream
rate-map/tb_p1_{rate}_seg1.spice           7 decks, one per rate
offset/bits_dcgain_{0..500}uv.txt          bit-level offset sweep
offset/{tb_p1,ngspice}_dcgain_*            its decks and logs
offset/{tb_p1,ngspice,pbit_op}_offset_*    the static .op sweep
```

Decks other than the per-rate representative are omitted: each is ~1.9 MB of PWL-free
netlist plus generated content and all regenerate from `generate_rate_map.py` and the seed.
Flagged rather than quietly taken.

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2 installation.
