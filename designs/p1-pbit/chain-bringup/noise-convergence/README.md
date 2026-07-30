# The chain will not integrate a discontinuous input, and that is why the bitstream run aborted

The first attempt to run amplifier and comparator together with a live noise source
aborted with a timestep collapse:

```
doAnalyses: TRAN:  Timestep too small; time = 1e-10, timestep = 2.5e-24:
  trouble with xcomp.xqclk_latch:npn13g2_nx_vbic-instance
```

That message names a transistor, which invites the conclusion that the transistor is
the problem. It is not. Six runs, each changing one thing:

| deck | input at the amplifier | result |
| --- | --- | --- |
| `chain_dc` | DC 1.440 V, no signal | **converges** |
| `chain_noise` | `TRNOISE(3.0818m 10p 0 0)` | **aborts**, t = 100 ps, at `xqclk_latch` |
| `chain_pwl` | PWL, same samples **held** for each 10 ps step | **aborts**, t = 30 ps, at `xq1` |
| `chain_sin` | smooth 5 GHz sine, same 3.0818 mV amplitude | **converges** |
| `chain_sin_small` | smooth 5 GHz sine, 30 µV | **converges** |
| `chain_pwlramp` | PWL, same samples, **interpolated** between them | **converges** |

Read down that column and the cause is not ambiguous. It is not the solver options —
the comparator alone converges under `method=gear reltol=1e-3` with a 10 ps print
step. It is not the topology — DC converges. It is not the randomness — a
*deterministic* held-step PWL aborts just the same. It is not the amplitude — a
smooth waveform of identical amplitude converges. And it is not the noise interval:
NT of 5, 10, 20 and 50 ps all abort, on varying devices and at varying times.

**What breaks it is a discontinuity in the input value.** `TRNOISE` behaves as a
piecewise-constant source — a genuine step every NT — and the evidence is that
substituting a hand-built held-step PWL reproduces the abort while the same samples
linearly interpolated do not. A regenerative latch differentiates its way through
that step and the timestep controller collapses.

## The fix is also the more physical choice

Interpolating between noise samples band-limits the source to roughly 1/(2·NT). That
is not an approximation forced on us by the solver: real thermal noise arriving at
this amplifier is **already** band-limited, by the amplifier's own 5.26 GHz
bandwidth. A mathematically discontinuous input is *less* faithful to the physics
than a band-limited one, not more.

It buys a second thing that matters more than convergence. A PWL source built from a
seeded generator is **reproducible** — the same bitstream can be counted twice and
give the same answer. `TRNOISE` reseeds on every invocation, so rms repeats to about
1% but individual bits and peaks do not. Validating a counted P(bit=1) against a
predicted one needs a bitstream that stays put while you argue about it.

## Set an explicit maximum timestep

`tran 10p 100n` does not integrate in 10 ps steps. The first argument is the print
interval; the internal maximum step defaults to (tstop − tstart)/50, which for a
100 ns run is **2 ns** — ten complete clock periods per step, over a 200 ps clock
with 20 ps edges. That is why the earlier attempts reported 32 to 55 total timesteps
for 100 ns: 100 ns / 2 ns ≈ 50. The steps were real.

Pass the fourth argument: `tran 2p 100n 0 2p`. On this circuit, dropping from a 2 ps
maximum step to the default cost 9 µV on a 20 µV kickback measurement — the accuracy
is not incidental.

## The chain resolves

With convergence in hand, the first end-to-end result. Sampling a 5 GHz sine with a
5 GS/s clock is coherent — every sample lands at the same phase, so the sampled
differential is constant and the bit is a static decision rather than a random one.
That makes it a clean test of whether the comparator follows the amplifier:

| amplifier input | amplifier output swing | `PBIT_RAW` sampled |
| --- | --- | --- |
| 3.0818 mV at 5 GHz | 2.038 … 2.165 V | **84 µV / −54 µV — low** |
| 30 µV at 5 GHz | 2.045 … 2.174 V | **1.19992 … 1.20008 V — high** |
| DC, no signal | 2.045 … 2.174 V | 1.19992 … 1.20008 V — high |

The decision flips with input amplitude, so the amplified signal reaches the
comparator and is resolved. That is the first evidence the two blocks work as a
chain rather than only as parts.

**What this is not.** No bit probability has been counted. A coherently sampled sine
is a static test by construction; the random bitstream needs the interpolated noise
source over thousands of clock edges, and that run has not been done. Nothing here
says anything yet about P(bit=1), autocorrelation, or bias.

## Reproducing

```
ngspice -b chain_dc.cir          # converges
ngspice -b chain_noise.cir       # aborts, as documented above
ngspice -b chain_pwl.cir         # aborts: held steps, deterministic
ngspice -b chain_sin.cir         # converges
ngspice -b chain_pwlramp.cir     # converges: the recommended form
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. The two `pre_osdi` lines inside `.control`
are required — without them the PSP103 MOS models are absent and the netlist is
rejected before any analysis runs. `pwlramp.inc` carries 400 samples at 10 ps from a
seeded Gaussian generator, σ = 3.0818 mV.
