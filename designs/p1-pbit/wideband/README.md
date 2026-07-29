# P1 p-bit under physically calibrated broadband noise

This replaces [`../rate-map/`](../rate-map/), which is withdrawn. That note measured the
p-bit under a synthetic 1,000-tone excitation whose amplitude had no stated derivation and
whose spectrum stopped at f_clk/2. Both mattered. This one uses ngspice `trnoise` at an
amplitude derived from a `.noise` analysis of the VBIC model at the operating bias, flat to
~50 GHz.

169 runs across seven sampling rates, plus a deterministic offset sweep. Decks, logs and
extracted bitstreams for every run.

## 1. Adjacent-bit correlation does not depend on sampling rate

| f_s (GS/s) | segments | bits | r₁ |
| ---: | ---: | ---: | ---: |
| 1.0 | 40 | 7,960 | +0.0081 ± 0.0333 |
| 1.5 | 34 | 10,166 | +0.0033 ± 0.0090 |
| 2.0 | 25 | 9,950 | +0.0042 ± 0.0107 |
| 2.5 | 10 | 4,980 | +0.0133 ± 0.0152 |
| 3.0 | 10 | 5,990 | −0.0010 ± 0.0132 |
| 4.0 | 10 | 7,980 | +0.0078 ± 0.0134 |
| 5.0 | 10 + repeat | 9,990 ×2 | +0.0079 ± 0.0061 |

**Combined over the three best-measured rates: r₁ = +0.0060 ± 0.0046** — 1.3σ from zero,
χ² = 0.22 on 2 dof, so the rates are consistent with a single common value. Fitted slope
against rate: +0.0014 per GS/s.

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
characterisation curiosity.** For scale, offset from mismatch between nominally identical
bipolar devices of this size is typically of order 1 mV — which on this transfer drives the
output most of the way to stuck. **Offset compensation is not optional for this design**;
trimming or a servo is required, and 12.8 µV per percent sets its accuracy target.

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
  segments; pooling three rates reaches ±0.0046 with what is here.

## Contents

```
generate_rate_map.py                       deterministic deck generator
rate-map/bits_{rate}_seg{n}.txt            169 extracted bitstreams
rate-map/ngspice_{rate}_seg{n}.log         169 logs
rate-map/tb_p1_{rate}_seg1.spice           7 decks, one per rate
offset/bits_dcgain_{0..500}uv.txt          bit-level offset sweep
offset/{tb_p1,ngspice}_dcgain_*            its decks and logs
offset/{tb_p1,ngspice,pbit_op}_offset_*    the static .op sweep
```

Decks other than the per-rate representative are omitted: each is ~1.9 MB of PWL-free
netlist plus generated content and all regenerate from `generate_rate_map.py` and the seed.
Flagged rather than quietly taken.

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2 installation.
