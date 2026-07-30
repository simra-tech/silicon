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

## Confirmed independently, from small-signal bandwidth

Everything above infers the interface time constant from *bitstream statistics* — the
rate at which ρ decays. That is indirect. Measuring the same thing as a **frequency
response**, with the clock frozen in track so the signal path is continuous, agrees:

| node | −3 dB bandwidth | τ = 1/(2πf) | in clock periods (200 ps) |
| --- | --- | --- | --- |
| CML collectors, `c_p − c_n` | **32.88 GHz** | 4.8 ps | 0.02 |
| CMOS load, with 38.3 fF damping | **196.6 MHz** | **810 ps** | **4.05** |
| CMOS load, damping removed | **425.4 MHz** | 374 ps | 1.87 |

Three things line up, and none of them was fitted to the others.

**The latch node is 32.9 GHz — 6.6× the clock rate.** That is why its collectors come
back uncorrelated: it settles in a fiftieth of a clock period. The latch is not the
bottleneck by two orders of magnitude.

**The interface is 196.6 MHz, 167× slower than the node feeding it**, and its τ of
810 ps is **four clock periods** — which is the correlation length measured from the
bitstream, where ρ falls through 1/e around lag 4 to 5. A statistical measurement and a
small-signal measurement, taken by different means, giving the same number.

**And the damping capacitors account for about half the node capacitance.** Removing
them takes the pole from 196.6 to 425.4 MHz — a factor of 2.16 — and takes ρ₁ from
0.777 to 0.424, a factor of 1.83. The correlation tracks τ, which is the relationship
the mechanism predicts.

### The specification the redesign has to hit

For the bits to be usably independent, τ must be small against the clock period rather
than several times it. Taking ρ₁ ≤ 0.05 as the target — roughly τ ≤ 200 ps / 3 — the
interface pole needs to be **≳ 2.4 GHz**.

That is **12× beyond where the node sits even with the capacitors removed**, so no
amount of adjusting the damping reaches it. It is a topology change, and this is the
number it has to clear.

## And clearing it is not sufficient — the first candidate clears it and does not work

The obvious topology fix is to replace the pMOS current-mirror load with resistors:
1.03 kΩ (`rppd`, 3.7 µm at w = 1 µm) in place of the mirror, no tail device, damping
capacitors gone. `p1_comparator_cand1.spice`, measured on the same harness:

| | interface gain | pole | τ | clock periods |
| --- | --- | --- | --- | --- |
| baseline: mirror + 38.3 fF damping | **23.37 dB** | 196.6 MHz | 810 ps | 4.05 |
| baseline, damping removed | 23.37 dB | 425.4 MHz | 374 ps | 1.87 |
| **resistive load** | **4.01 dB** | **4.545 GHz** | **35 ps** | **0.18** |

The pole moves by a factor of **23** and comfortably clears 2.4 GHz. Then the transient:

```
PBIT_RAW over the sampled window: min 1.1999 V   max 1.2001 V
N = 501   P(bit=1) = 1.0000
```

**Pinned at the rail. Every one of 501 samples is a one.** The autocorrelation cannot
even be computed — there is no variance to correlate. A fast interface that never
decides is worse than a slow one that does.

**The 19.4 dB it gave up was load-bearing.** The mirror's high output impedance is what
provides the gain that carries the CML swing across the CMOS inverter's 0.600 V trip
point — and that same high impedance is what makes the node slow. Gain and bandwidth
here are *the same parameter*: g_m·R and 1/(RC) move in opposite directions on the same
R. You cannot swap the mirror for a resistor and keep the decision.

### The specification, restated as gain-bandwidth

| | gain | pole | gain × pole |
| --- | --- | --- | --- |
| baseline | 14.7× | 196.6 MHz | **2.9 GHz** |
| resistive load | 1.59× | 4.545 GHz | 7.2 GHz |

The resistive load actually *improves* gain-bandwidth by 2.5× — it simply spends all of
it on bandwidth and keeps none for the decision. So the real target is both at once:
enough gain to cross the trip point from the available CML swing, **and** a pole above
2.4 GHz.

Taking ~12 dB (4×) as a working guess at the gain the decision needs, the interface
requires **GBW ≳ 10 GHz** where it has 2.9 GHz — a factor of about 3.4. That is bought
with transconductance, which means current or device width, or with a topology whose
gain does not come from a single R·C: a cascode, a regenerative CMOS stage, or a
self-biased converter with feedback.

**The 12 dB figure is a guess and is the next thing to measure**, not a specification.
The honest form of it: sweep the interface gain and find the smallest value that still
resolves the CML swing to a full rail, then the pole target and the gain target together
fix the GBW the topology must deliver.

## The gain-bandwidth target was also incomplete: the resistor sets the bias too

The sweep was run. It does not find a working resistor value, and the reason is a third
constraint neither of the two previous specifications named.

| load | gain | pole | GBW | resolves? | P(bit=1) | ρ₁ | overshoot |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mirror, 38.3 fF damping | 23.37 dB | 196.6 MHz | 2.9 GHz | **yes** | 0.473 | +0.777 | 69 mV |
| 1.03 kΩ | 4.01 dB | 4.545 GHz | 7.2 GHz | **no** | 1.0000 | — | — |
| 2.00 kΩ | 9.23 dB | 3.440 GHz | 9.9 GHz | — | — | — | — |
| 3.00 kΩ | 12.21 dB | 2.756 GHz | **11.2 GHz** | **no** | 1.0000 | — | — |
| 4.88 kΩ | 15.42 dB | 2.026 GHz | 12.0 GHz | yes, barely | **0.956** | +0.669 | 89 mV |

**3.00 kΩ has 4.08× of gain and a 2.756 GHz pole — it clears both previous targets and
does not resolve.** So the ~4× gain guess above is wrong, and gain-bandwidth was not the
binding quantity either.

### What actually decides it

The DC level of the load node, against the CMOS inverter's measured 0.600 V trip point:

| load | `cml_out_p` DC | above trip point | resolves? |
| --- | --- | --- | --- |
| mirror | **0.6649 V** | **+65 mV** | yes |
| 4.88 kΩ | 0.8269 V | +227 mV | yes, barely |
| 3.00 kΩ | 0.9545 V | +355 mV | no |
| 2.00 kΩ | 1.0302 V | +430 mV | — |
| 1.03 kΩ | 1.1091 V | +509 mV | no |

Monotonic, and it predicts the resolve column exactly: the two that work are the two
closest to the trip point. As R_L falls the node rides up toward V_DD because there is
less I·R drop, and at 1.03 kΩ it sits **509 mV above** the point where the inverter
switches. No amount of signal swing crosses that.

**So a single load resistor sets gain, bandwidth *and* bias — three jobs on one degree of
freedom.** That is precisely what the current mirror was buying: it holds the node at
0.665 V, 65 mV from the trip point, *independently* of its small-signal impedance. Its
high impedance is a side effect of being a current source, and the slowness is the price.

### The requirement, third attempt

Three constraints, and they need three degrees of freedom:

1. **bias** — the load node must sit within roughly 100 mV of the 0.600 V trip point;
2. **pole** — above ~2.4 GHz, so τ is a fraction of the 200 ps clock period;
3. **gain** — enough to carry the CML swing across the trip point once centred.

A resistor gives one. The topologies that give more: a resistive load with a **separate
bias current source**; a **cascode**, which decouples the impedance seen by the signal
from the DC drop; or **AC-coupling into a self-biased inverter with a feedback resistor**,
which centres itself at its own trip point regardless of the preceding node's DC level.

That last one is what `cml_cmos_cand2` in the designer's own file gestures at — it puts an
`rppd` feedback resistor from `raw_inv` back to `cml_out_p`. That instinct attacks exactly
the term that kills the resistive load, and it is the more promising of their two
candidates for a reason neither of us had measured when they were drawn.

**Three specifications for this node, each incomplete, each corrected by measurement**: a
pole target that omitted gain, a gain-bandwidth target that omitted bias, and now a
three-way constraint. The pattern is not that the analysis was careless but that the
enumeration was — asking "what are all the jobs this node does" is mechanical, and doing
it once at the start would have been cheaper than three rounds of simulation.

## Unresolved: two independent sweeps disagree at 4.0 kΩ

A second sweep of the same load resistance was run independently. **It agrees on the shape
and contradicts this one on the answer**, and the disagreement is recorded here rather than
settled, because it is not yet settled.

Both sweeps find a **two-sided window** — too little load fails one way, too much fails the
other — which is the substantive agreement and neither of us predicted it in advance. But:

| at R_L = 4.0 kΩ | this work | the second sweep |
| --- | --- | --- |
| resolves? | **no — degenerate** | **yes — rail to rail** |
| P(bit=1) | 1.0000 | 0.273 |
| ρ₁ | no variance to measure | 0.357 |
| `PBIT_RAW` swing | 1.1993 … 1.2065 V | 0 … 1.2 V |
| load node DC | **0.8844 V** (+284 mV above trip) | not reported |
| gain quoted | 14.17 dB (chain, amplifier input → `cml_out`) | 41.6 dB (interface, local) |

This work's result is internally consistent: +284 mV above the trip point falls between
3.00 kΩ (+355 mV, fails) and 4.88 kΩ (+227 mV, barely resolves), and it fails, exactly as
the monotonic bias table predicts.

**The gain figures are not directly comparable** — one is chain gain from the amplifier
input, the other a local stage gain — so that difference alone is not evidence of error.

**One number in the second sweep does need explaining, though.** Its gain-bandwidth product
is **319.4 GHz on every row**, across a sixfold range of R, to four significant figures.
That is what you get when gain and pole are both *computed* from g_m·R and 1/(2πRC) with
fixed g_m and C, rather than measured — the product cancels R identically. A measured sweep
should not do that, and this one does not: measured GBW here **rises** with R (7.2 → 9.9 →
11.2 → 12.0 GHz), because the load resistor also sets the branch current, so g_m falls as R
rises and the two terms partly cancel.

**The diagnostic that would localise the disagreement in one number: the DC voltage on
`cml_out_p`.** It is 0.8844 V here at 4.0 kΩ. If it is near 0.600 V in the other deck, that
deck's nMOS is carrying several times more current, and the difference is upstream — in the
`g_p` bias from the emitter-follower divider, which is 0.5200 V here. Everything downstream
follows from that one node, and until the two decks agree on it the sweeps cannot be
compared.

### Resolved: the other deck omits the trim pair

Both numbers came back, and they closed it in one exchange.

| | this deck | the other deck | Δ |
| --- | --- | --- | --- |
| `v(g_p)` | 0.5200 V | 0.5662 V | +46.2 mV |
| `v(cml_out_p)` at 4.0 kΩ | 0.8844 V | 0.7254 V | −159 mV |

The divider ratio is the same in both — 3840/9630 = 0.3988 here, and `v(g_p)/v(ef_p)` =
0.51999/1.30398 = 0.3988 confirms it — so the 46 mV originates further up. Accounting for
every current into the collector node, clock frozen in track:

| into `c_p` | |
| --- | --- |
| input pair `xq1` | 0.9763 mA |
| **trim pair `xqdac_p`** | **0.4150 mA** |
| latch pair `xq3` | 4.5 pA (off, as it should be) |
| follower base `xqef1` | 0.17 µA |
| **total** | **1.3915 mA** |

1.3915 mA × 288 Ω = 0.401 V, so `c_p` = 2.099 V against 2.10299 V measured — closed to 4 mV.
The tail is 1.9598 mA, matching the ideal source the other deck substitutes, so the tail is
not the difference either.

**The difference is the trim pair, which the other deck does not instantiate.** Its 415 µA
per side pulls `c_p` down about 120 mV, which carries through the follower to `g_p` as
46 mV, which is the whole discrepancy. So 4.0 kΩ resolves in a deck without the trim
devices and does not resolve in the block as drawn. **The working point is an artefact of a
missing device.**

## The trim pair is mis-biased, and this corrects our own earlier claim

The number that closed the dispute is also a defect in its own right.

`TRIM_P` and `TRIM_N` are held at **1.440 V**. The amplifier's real output common mode —
and therefore the comparator's input common mode — is **2.139 V**, 699 mV higher. So the
trim devices sit with their bases 699 mV below the signal pair's and are hard on, drawing
**415 µA per side: 21% of the 1.96 mA tail**, and loading the collectors by 120 mV.

We previously described this pair as "essentially off" at this operating point. That was
wrong, and it matters in two ways beyond the bias shift:

- the trim's transconductance is set by 415 µA rather than by a small designed injection, so
  the volt-per-code of the 10-bit DAC is not the step size the ±40.1 mV range assumed;
- the loading is a function of the trim code, so changing the code moves the collector
  operating point as well as the offset it is supposed to inject.

**The trim reference needs to track the input common mode** rather than sit at a fixed
1.440 V. Nothing here says what it should be set to — that follows from the injection
current the trim is meant to provide, which has not been re-derived since the amplifier's
output common mode was measured at 2.139 V.


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
