# The amplifier rectifies its own noise, and that sets a bias floor no trim can reach

This is the most consequential result in this repository, and it retracts a published
claim of ours. The short version: **the amplifier's differential output has a DC mean
proportional to the noise amplitude it is amplifying.** Referred to its input, that
mean is 0.80 × σ. It is therefore not an offset you can outrun by raising the noise,
because it rises with the noise.

## The measurement

Same chain — `p1_noise_amp` into `p1_comparator`, clocked at 5 GS/s — driven by a
seeded band-limited PWL noise source. `amp_avg` is the time average of
`v(NOISE_AMP_P) − v(NOISE_AMP_N)` over 2 … 20 ns. The input is zero-mean in every run
(`in_avg` = 0.47 µV).

| deck | input σ | `amp_avg` | `amp_avg` / σ |
| --- | --- | --- | --- |
| `chain_nonoise2` | **DC, no noise** | **−4.3 µV** | — |
| `chain_lo` | 0.3082 mV | +3.166 mV | 10.28 |
| `chain_mid` | 1.000 mV | +10.29 mV | 10.29 |
| `chain_diff` | 3.0818 mV | +31.74 mV | 10.30 |
| `chain_truediff` | 3.0818 mV, applied **differentially** | +31.73 mV | 10.30 |

Five things fall out of that table.

**It is a nonlinearity, and this is not an inference.** A linear time-invariant system
cannot produce a DC output from a zero-mean input — no combination of gain, bandwidth,
pole mismatch or asymmetric time constants can. The mean is +31.74 mV from an input
whose mean is 0.47 µV, so the mechanism is necessarily nonlinear.

**It is not headroom clipping.** The ratio is constant to three digits across a factor
of ten in amplitude, from output peaks of ±35 mV to ±141 mV, against 330 mV of
collector headroom. Compression against a rail would show up as a ratio that grows
with amplitude. This one does not move.

**It requires a varying input.** With DC in, the differential mean at the sampling
instants is −1.5 … −2.7 µV and `amp_avg` is −4.3 µV. The clock is not doing it either:
that DC run has the comparator clocking at 5 GS/s throughout.

**It is not an artefact of single-ended drive.** Driving the noise differentially,
+σ/2 on one input and −σ/2 on the other from the same seed, gives +31.73 mV against
+31.74 mV. Identical to four digits.

**The size is suggestive but does not settle the shape.** 10.30 divided by
√(2/π) = 0.7979 is **12.9**, the amplifier's small-signal gain, so the mean is
numerically equal to gain × E|v_in| — the form a full-wave rectifier would give. Treat
that as a coincidence worth chasing rather than an identification: a simple
two-slope model, gain G₊ for positive inputs and G₋ for negative, fits the peak
asymmetry (below) but then predicts a mean of about 10 mV rather than the 32 mV
measured. The size and the linearity are measurements; the mechanism is not.

## Confirmed on the amplifier alone, with no comparator in the circuit

The runs above all include the comparator, so the mean could in principle have been
something the two blocks did to each other. It is not. `aa_pwl20ns` / `aa_pwl_lo` are
the amplifier by itself — no comparator, no clock anywhere in the deck:

| input σ | `amp_avg` | output range | peak ratio |
| --- | --- | --- | --- |
| 3.0818 mV | **+31.876 mV** | +141.8 / −75.0 mV | 1.89 |
| 0.3082 mV | **+3.186 mV** | +14.2 / −7.53 mV | 1.89 |

31.876 / 3.186 = **10.005** for a tenfold change in input: linear to four digits.

This version of the measurement is the stronger one, and it kills the last two
alternative explanations outright. There is **no clock in the deck**, so nothing
synchronous can be contributing. And at the low amplitude the output swings **±14 mV
against 330 mV of headroom** — three orders of magnitude clear of any rail — while the
mean is still exactly 10.34 × σ. Whatever produces this is present at small signal.

The **peak asymmetry is scale-invariant**: +1.89:1 at both amplitudes, four digits
apart. A large-signal effect would grow with amplitude. A fixed asymmetry between the
two halves of the amplifier would not, and this does not.

## Why it matters more than its size suggests

Referred back to the input, the offset is E|v_in| = 0.7979 σ. So the
signal-to-offset ratio the bit actually sees is

    SOR = σ / (0.7979 σ) = 1.25

independent of amplitude. The specification needs **SOR ≥ 39.89** for the bias to stay
within 1%. This is short by a factor of **32**, and — the part that matters — *raising
the noise does not help*, because the offset is a fixed fraction of it.

Measured at the decision instants over twenty consecutive clock periods, the
differential arriving at the comparator is positive in **19 of 20**: −5.0, +37.9,
+41.9, +67.3, +41.6, +60.0, +63.1, +41.9, +14.5, +61.5, +107.6, +83.1, +18.7, +80.3,
+52.2, +33.6, +22.2, +4.0, +13.5, +72.9 mV. Mean +45.9 mV against a spread of about
27 mV — roughly 1.7σ off centre. The comparator resolves every one of them correctly;
it is being handed a biased signal, not misreading a fair one.

That is the explanation for a bitstream that comes back all zeros. **The comparator is
not at fault and neither is the sampling.** The 10-bit trim cannot correct it either:
the trim subtracts a fixed voltage, and this offset moves with the noise amplitude.

## What this retracts

The preamplifier page states, in its specification table, **"noise amplitude, upper —
no binding upper bound"**, on the grounds that 330 mV of collector headroom clears
4.3σ peaks of 132 mV with 2.5× to spare. That reasoning is about clipping, and clipping
is not what binds. **There is a binding constraint on noise amplitude and it is
proportional**, so it cannot be satisfied by choosing an amplitude at all. That row is
withdrawn — see `../../preamplifier/`.

The claim was made on the amplifier measured **alone**, into its own load, looking at
single-ended output swing. The rectified mean is a property of the differential output
under a *varying* input, and no block-level test in this repository looked at that.

## What has not been established

The mechanism inside the stage is **not identified**. The measurement says the transfer
is even-order in the input with the size of a full-wave rectifier; it does not say
which device or which asymmetry produces it. Candidates not yet distinguished: tail
current modulation converting common mode to differential through an asymmetric load,
V_BE nonlinearity in the input pair at these swings, or the second stage's operating
point moving with input amplitude. **Do not size anything on the strength of this page
alone** — it localises the problem to the amplifier and quantifies the consequence.

Also not established: whether the effect survives at lower gain, and whether it is
present in the `noise-generator` → amplifier interface as built rather than with an
ideal source.

## Reproducing

```
ngspice -b chain_nonoise2.cir   # DC control: -4.3 uV
ngspice -b chain_lo.cir         # sigma / 10
ngspice -b chain_mid.cir
ngspice -b chain_diff.cir       # nominal sigma
ngspice -b chain_truediff.cir   # nominal sigma, differential drive
ngspice -b aa_pwl20ns.cir       # amplifier alone, nominal sigma
ngspice -b aa_pwl_lo.cir        # amplifier alone, sigma / 10
```

## If you are building a diagnostic for this, check row one first

A stage-by-stage walk of this effect is the obvious next measurement, and the way to get
it wrong is to write the differential expressions against the wrong reference. Both
inputs here sit at a 1.440 V common mode, so a "differential" reading of **−1440 mV** is
the common mode with a sign flip, not a differential — and every stage below such a row
inherits the error. The check costs nothing: **the input differential mean must come out
near zero, because the input is zero-mean by construction.** In these decks it reads
0.47 µV. If the first row of a stage table is off by the common-mode voltage, stop there.

The second check is the scaling column. A static operating-point difference does not move
when the input amplitude changes; the effect being hunted scales by exactly ten for a
tenfold input change. Any row that reads 1.00× is measuring a bias point, not a signal.

`$PDK_ROOT` is the IHP SG13G2 PDK root. The `pwl_*.inc` files carry the noise samples,
10 ps apart from a seeded Gaussian generator, linearly interpolated — see
`../noise-convergence/` for why a held-step source will not integrate.
