# The bits are not independent, and the comparator is what makes them dependent

Lag-1 autocorrelation of the output bitstream is **+0.80**. Consecutive bits agree
**90%** of the time. The correlation decays to zero only by about lag 10, so this
chip emits roughly **one independent bit every eight clock periods** — a usable rate
nearer 600 MS/s than the 5 GS/s it is clocked at.

For a probabilistic bit that is a defect of a different kind from bias. A biased
p-bit is still useful once trimmed; a *correlated* one breaks the machine it is meant
to serve, because a p-bit network assumes its samples are independent draws. No trim
code fixes it.

## The measurement that localises it

Two candidate causes, and neither can be distinguished by looking at the bitstream
alone:

1. the noise arriving at the comparator is **already correlated** at the sample rate
   — a bandwidth problem in the amplifier or the source; or
2. the noise is **white** and the comparator is manufacturing the correlation — a
   latch retaining state between decisions.

So sample both in one run: the amplifier's differential output at the decision
instant, and the bit that decision produced. N = 501, from 200 ns onward.

| lag | ρ(bit) | ρ(input sample) |
| --- | --- | --- |
| 1 | **+0.8018** | −0.0590 |
| 2 | **+0.6276** | −0.0272 |
| 3 | **+0.5256** | −0.0607 |
| 4 | **+0.4475** | +0.0034 |
| 5 | **+0.3732** | −0.0824 |
| 6 | +0.3031 | −0.0209 |
| 7 | +0.2132 | −0.0027 |
| 8 | +0.1352 | −0.0153 |

The standard error on ρ at this N is **0.045**, so every input-sample value is
within about two standard errors of zero. **The noise reaching the comparator is
white at the sample rate; the bitstream is not.** The correlation is created between
the input and the output — inside the comparator.

That is the signature of a latch that does not fully erase its previous state. This
topology has no explicit reset device: erasure depends entirely on the track phase
driving the collectors back to a state set by the input, and the track phase is 80 ps
of a 200 ps period. Incomplete erasure leaves each decision biased toward the one
before it, decaying over several cycles — which is the shape in the table.

## The track phase is not why — and the latch is not the culprit at all

Both of those were our hypotheses, and both are wrong. They are recorded because the
measurements that killed them are the ones that found the real answer.

**Lengthening the track phase does nothing.** Taking the clock from 80 ps of track in a
200 ps period to 120 ps — `track120.cir`, everything else identical, same noise file:

| | ρ₁ | ρ₂ | ρ₃ | ρ₄ | ρ₅ |
| --- | --- | --- | --- | --- | --- |
| track 80 ps, as built | +0.802 | +0.628 | +0.526 | +0.447 | +0.373 |
| track 120 ps | **+0.810** | +0.637 | +0.499 | +0.405 | +0.320 |

ρ₁ is unchanged within the standard error of 0.045. Incomplete erasure for want of
settling time is not the mechanism.

**And the latch's own collectors are not correlated.** Sampling three points in the
same run — `nodes.cir`, mid-latch, N = 501:

| node | ρ₁ | ρ₂ | ρ₃ | ρ₄ | ρ₅ |
| --- | --- | --- | --- | --- | --- |
| CML collectors, `c_p − c_n` | **−0.024** | +0.062 | −0.024 | +0.094 | +0.019 |
| CMOS load, `cml_out_p − cml_out_n` | **+0.891** | +0.714 | +0.582 | +0.477 | +0.380 |
| `PBIT_RAW` as bits | +0.777 | +0.635 | +0.517 | +0.439 | +0.356 |

Every CML collector value is within two standard errors of zero. **The comparator's
decision is independent bit to bit.** The correlation appears at the CMOS load nodes
and is inherited by everything after them. The memory is in the **CML → CMOS
interface**, not in the latch.

## The overshoot fix is a large part of the cause

Those load nodes carry two `cap_cmim` damping capacitors, 38.3 fF each, added to cure
86 mV of overshoot. They sit on the output of a pMOS current-mirror load — a
deliberately high-impedance node — so their time constant is of order a nanosecond,
several clock periods. Removing them (`nodamp.cir`, same noise, same clock):

| | ρ₁ bit | ρ₁ CMOS load | P(bit=1) | `PBIT_OUT` peak |
| --- | --- | --- | --- | --- |
| 38.3 fF damping, as built | +0.777 | +0.891 | 0.4731 | 1.269 V (**69 mV** over rail) |
| damping removed | **+0.424** | +0.726 | 0.5788 | 1.301 V (**101 mV** over rail) |

**Bit correlation nearly halves and the overshoot gets worse.** So the damping
capacitors are a major contributor to the memory — and they are not the whole of it,
because the load node is still correlated at 0.726 with them gone. The mirror's own
output resistance against parasitic capacitance is already slow at 5 GS/s.

**This is a real design tension and nobody had seen it.** Damping the overshoot and
decorrelating the bits pull in opposite directions on the same node. It stayed hidden
because overshoot is measured on a *single* edge and correlation requires *consecutive*
ones — the two live on the same node and no measurement looked at both.

So the fix is not "remove the capacitors". It is to make the interface fast enough at
5 GS/s that neither compromise is needed: a lower-impedance load in place of the
current mirror, or a different level-shifting topology between the CML latch and the
CMOS buffer. That is a topology decision, and **nothing here licenses a resize** — what
this establishes is which node to redesign and why.

## Every error bar quoted on P(bit=1) is understated

A counted proportion has standard error √(p(1−p)/N) **only if the samples are
independent**. With this much correlation the variance of the mean is inflated by

    1 + 2·Σ(1 − k/N)·ρ_k  =  7.96

so the true standard error is **2.8× larger** than the shot-noise figure:

| | |
| --- | --- |
| P(bit=1) counted | 0.4731 at N = 501 |
| standard error, assuming independence | 0.0223 |
| standard error, corrected for correlation | **0.0629** |
| z against 0.5, assuming independence | −1.21 |
| z against 0.5, corrected | **−0.43** |

This retroactively resolves an apparent conflict. Two counts of this chip exist:
**0.4731 ± 0.0223** at N = 501 (this run) and **0.4096 ± 0.0127** at N = 1499
(a separate 450 ns run), the second quoted as 7.16σ from 0.5. With the inflation
factor applied, the second becomes roughly ±0.036 and about 2.5σ, and the two
measurements are consistent with each other and marginally with a fair coin. **The
7σ discrepancy was an artefact of assuming independence in a stream that has none.**

An error bar is a claim about the sampling process, not just about the arithmetic,
and it is wrong to quote a shot-noise figure without having checked the assumption
underneath it. That check is one pass over the same data.

## What this says about the earlier bias hunt

Two explanations for a biased bit were tested and neither accounts for a large one:

- the amplifier's differential output mean at the sampling instants is **+0.40 mV**
  against 27.3 mV_rms, which is a bias contribution of 0.6%;
- the comparator's own input-referred offset is about **1 mV** — a nine-point
  differential sweep at the amplifier's 2.139 V common mode puts the decision
  threshold between −2 mV and 0 mV — giving a further ~1.3%.

Neither is anywhere near the nine points that a P(1) of 0.41 would require. With the
correlation correction, no such bias needs explaining.

## Reproducing

```
ngspice -b bitcorr.cir                  # writes bits2.dat: bit and both output nodes
python3 count_correlation.py bits2.dat
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. 300 ns at a 5 ps maximum timestep; the first
200 ns are simulated and discarded for the coupling settling. Sampling convention and
the reason for it are in [`../counted-bitstream/`](../counted-bitstream/).
