# 500 ns transient: does the amplifier clip the noise?

Artefacts behind *Neither edge of the gain window binds* in [`../../README.md`](../../README.md).

```
tb_transient_noise_500ns.cir        the deck
ngspice_transient_noise_500ns.log   its output, unedited
```

Two independent `TRNOISE` sources drive the two inputs through the generator's real source impedance, split as
two 529.5 Ω halves so the differential source impedance is the 1059 Ω the noise generator presents. The
measurement window starts at 5 ns to skip start-up and runs to 500 ns — 247,504 solver rows, about 5,260
independent samples at the amplifier's ~5.3 GHz bandwidth.

    v_rms = 30.672 mV      v_max = +131.72 mV      v_min = −117.85 mV

**Re-running this deck will not reproduce the peaks, and that is not a defect.** It sets no seed, and ngspice
reseeds `trnoise` on every invocation, so each run is a fresh realisation of the same process. Across three runs
of this deck the rms held to **1.2%** (30.36 … 30.74 mV) while the extremes moved **±13%** (128 … 145 mV). The rms
is a property of the circuit; a particular peak is a property of one realisation.

So read the result as a distribution, not as three numbers: largest excursions land at **4.2–4.8σ**, which is
where a Gaussian maximum belongs for this sample count (expected 4.14σ), and the largest seen across runs is
145 mV against **330 mV** of collector headroom. Nothing clipped in any run.

**What the sample count buys.** An earlier 10 ns version of this run carried ~104 samples, where the expected
largest excursion is 3.05σ — too short to have expected a 3.5σ event at all, so it could not test the bound it
was quoted for. P(|x| > 3.5σ) = 4.7 × 10⁻⁴ needs ~2,150 samples, roughly 207 ns. 500 ns is the first length at
which the tails are worth reporting.

Absolute paths are rewritten (`$PDK_ROOT`, `./`), so point `$PDK_ROOT` at an SG13G2 install before running. That
substitution is the only edit; the log is exactly as the simulator wrote it.
