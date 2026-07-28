# Adjacent-bit correlation versus sampling rate

How correlated is one output bit with the next, and does that get worse as you clock the
p-bit faster? The answer decides whether the fastest clock is free.

Seven rates from 1.0 to 5.0 GS/s, ten 500 ns segments each — **70 runs, 95,000 bits**.

## Result

| f_s (GS/s) | Nyquist | bits | r₁ | std. error |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 0.50 GHz | 5,000 | +0.0353 | 0.0150 |
| 1.5 | 0.75 GHz | 7,500 | +0.0288 | 0.0086 |
| 2.0 | 1.00 GHz | 10,000 | +0.0192 | 0.0131 |
| 2.5 | 1.25 GHz | 12,500 | +0.0253 | 0.0072 |
| 3.0 | 1.50 GHz | 15,000 | +0.0299 | 0.0055 |
| 4.0 | 2.00 GHz | 20,000 | +0.0363 | 0.0047 |
| **5.0** | 2.50 GHz | 25,000 | **+0.0596** | 0.0060 |

**Flat from 1 to 4 GS/s, then a step at 5.**

Over 1.0–4.0 the value runs 0.0353 → 0.0363, a factor of **1.03**, with scatter across
those six rates of 0.0058 against a mean standard error of 0.0090 — the variation is
*smaller than the error bars*, so no rate dependence is detectable there.

At 5.0 GS/s the value is 0.0596 against a mean of 0.0291 for every rate below it: an
excess of **+0.0305, 3.5σ**. That step is real. **The top of the range is not free.**

## What this replaces, and why the earlier answer was wrong

An earlier version of this measurement showed r₁ rising monotonically by **1.79×** across
1.0–4.0 GS/s, and we reasoned from it. That rise was an artefact of our own stimulus.

The noise source is a sum of 1,000 tones standing in for physical noise. It carried a
guard that pushed tone frequencies away from multiples of the clock, added to avoid
aliasing. That guard carves a comb of gaps in the spectrum, and a comb of gaps in
frequency transforms to a comb in lag — imprinting deterministic structure on the
bitstream at lags 50–200, plus a **negative** contribution at lag 1 whose magnitude
*shrinks* as the clock speeds up. A shrinking negative offset manufactures an apparent
rise in a quantity that is actually flat.

A second defect compounded it: a rewrite hardcoded the tone band to 2.5 GHz, which is
Nyquist for 5 GS/s **and no other rate**, so every slower rate was driven with 20–80% of
its tones above its own Nyquist, folding back at rate-dependent positions.

The data here is from a generator that scales the band with the clock (`10 MHz …
f_clk/2`) and contains **no exclusion guard**. See `generate_rate_map.py`.

### The correction was predicted before it was measured

The artefact's contribution was computed from the tone list alone — aliasing is automatic
when you evaluate `cos(2πfkT)` at the sampling instants — and published before this sweep
existed:

| | predicted | measured |
| --- | ---: | ---: |
| 1.0 GS/s | +0.0331 | +0.0353 |
| 3.0 GS/s | +0.0338 | +0.0299 |
| 5.0 GS/s | +0.0627 | +0.0596 |
| jump, 1–4 mean → 5.0 | **+0.0295** | **+0.0305** |

Correlation predicted-to-measured across all seven rates: **+0.953**. The prediction
anticipated both the flatness below 4 GS/s and the step at 5.

## What it means for the architecture

r₁ sits near **0.029** from 1 to 4 GS/s and roughly doubles at 5 GS/s.

Whitening remains mandatory at every rate. XOR whitening yields f_s/2 regardless of input
correlation, so the argument for clocking fast survives — but it should be made knowing
that the raw stream at 5 GS/s is materially worse than at 4, not on the assumption that
the top of the range costs nothing.

**On the 0.0140 figure quoted elsewhere in this repository:** it is not a threshold
published by anyone. It follows from PTG.2.3's min-entropy requirement (H∞ ≥ 0.98) under
a first-order Markov model *we* supplied — 2^-0.98 = 0.506980 and P(bit = previous) =
0.5 + r/2 give r ≤ 0.01396. Neither AIS-31 nor NIST SP 800-90B states a correlation
limit. And the assumption does not err in our favour: memory beyond lag 1 raises the
worst-case conditional probability for the same r₁, so the true limit is *tighter*. Treat
it as a floor.

## Honest limits

- **These are simulated bits, not measured silicon.**
- **The stimulus is synthetic.** ngspice's native `trnoise` does not currently run on this
  circuit; a 1,000-tone sum is a stand-in, and this note exists partly because that
  stand-in has already injected one artefact we had to find and remove. Treat any
  structure beyond lag 1 in this data with suspicion until it is reproduced with a
  physical noise source.
- **The stimulus amplitude was never calibrated, and an independent source disagrees.**
  `V_branch_rms = 0.001288` appears as a bare constant in every generator script with no
  derivation. A physically calibrated source — ngspice `trnoise` at an amplitude derived
  from a `.noise` analysis of the VBIC model at the actual bias — produces **3.2× less
  amplifier output** (28.8 mV rms against 92.3 mV) and, at 5 GS/s, gives
  **r₁ = −0.0164 ± 0.0097** against the +0.0596 ± 0.0060 reported above. Opposite sign,
  6.7σ apart, on 4,995 bits with the comparator verified balanced (latch mean within
  ±7 mV, P(1) = 0.506).

  That is not yet a contradiction, because the two sources are at different noise
  amplitudes and r₁ plausibly depends on the ratio of noise to the deterministic
  disturbances reaching the comparator. It is, however, an open question directly
  affecting every number in this table, and the resolving experiment — match the
  amplitudes and re-compare — has not been run. **Read this table as measured under one
  stimulus whose amplitude has no stated physical basis.**

- **No entropy claim is made here.** 500 ns yields 500–2,500 bits per segment; SP 800-90B
  estimators want ≥10⁶ samples, which needs a 1 ms transient — not achievable in SPICE.
  The standard practice is to extract physical parameters in simulation and generate the
  megabit stream from a stochastic model. r₁ is a circuit measurement; min-entropy is not.

## Contents

```
generate_rate_map.py                     deterministic deck generator, all 7 rates
run/bits_{rate}_seg{1..10}.txt           70 extracted bitstreams
run/ngspice_{rate}_seg{1..10}.log        70 logs, including operating points
run/tb_p1_{rate}_seg1.spice              7 decks, one per rate
```

**Nine of ten decks per rate are omitted** — each is 1.9 MB of which 98% is the PWL tone
table, and all regenerate byte-identically from `generate_rate_map.py` and the seed. The
included deck per rate lets you verify the generator reproduces it before trusting it for
the rest. This is a deliberate departure from our rule that a bitstream travels with its
own deck, flagged rather than quietly taken.

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2
installation.
