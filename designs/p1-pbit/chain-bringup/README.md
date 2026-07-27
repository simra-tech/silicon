# Chain bring-up — behavioural reference, then one real block at a time

The three blocks of P1 had never been simulated together successfully. Eight
attempts at the full chain in one step produced nothing usable. This directory
holds the method that worked instead: build every block as an idealised model
first, prove the architecture end to end, then replace the models with transistor
netlists **one block at a time**, checking after each swap that the statistics
survive.

Each swap is then a controlled experiment against a reference that already works,
so a failure localises to one interface rather than to the whole chain.

**State: simulation only. Nothing fabricated, nothing taped out, no layout, no
signoff of any kind is claimed here.**

## What ran

| run | generator | preamplifier | decision | 200 ns |
| --- | --- | --- | --- | --- |
| stage 1 | behavioural noise + RC | behavioural VCVS | post-processed | complete |
| swap 1 | **`P1_NOISE_GEN`, transistors** | behavioural VCVS | post-processed | complete |
| swap 2 | **`P1_NOISE_GEN`** | **`P1_NOISE_AMP`, transistors** | post-processed | complete |
| swap 3 | **`P1_NOISE_GEN`** | **`P1_NOISE_AMP`** | **`P1_COMPARATOR`, clocked at 5 GS/s** | complete |

The decision is done in post-processing in all three: the differential output is
sampled every 200 ps and compared against a threshold. No clocked comparator is
instantiated, so no clock exists in these decks.

Behavioural blocks are calibrated to measurements taken from the transistor
blocks themselves — 36.42 nV/√Hz differential from the generator's `.noise` run,
11.97 V/V and a 31.29 GHz pole from the preamplifier's AC run.

## Measured bit statistics

1,000 sampled bits per run. The 1σ detection floor for a correlation estimate at
N = 1000 is 1/√N = **0.0316**, so any |r| below that is unresolvable, not zero.

| statistic | stage 1 | swap 1 | swap 2 | **swap 3** | expected |
| --- | ---: | ---: | ---: | ---: | ---: |
| P(bit = 1) | 0.4830 | 0.4680 | 0.5210 | **0.4870** | 0.5 ± 0.0316 |
| r[1] | +0.0340 | −0.0213 | −0.0088 | **+0.0003** | 0 ± 0.0316 |
| r[2] | −0.0552 | −0.0002 | −0.0158 | **+0.0134** | 0 ± 0.0316 |
| r[3] | **−0.0964** | +0.0088 | −0.0007 | **−0.0900** | 0 ± 0.0316 |
| r[4] | +0.0091 | +0.0037 | −0.0359 | **−0.0409** | 0 ± 0.0316 |
| longest run | 9 | 9 | 8 | **7** | ≈ 10 |

**The complete transistor chain — HBT noise generator, HBT preamplifier and
clocked CML comparator at 5 GS/s — produces a bitstream with a longest run of 7
against an expectation near 10, and no correlation resolvable above the floor
except the lag-3 entry noted below.**

A direct check for hidden periodicity: the fraction of samples equal to the sample
2, 3, 4 and 8 places earlier is 50.7%, 45.5%, 48.0% and 48.3% — chance in every
case. Earlier iterations of swap 3
reached 99.9% at period 4.

Noise measured at the comparator's latch bases is 90.70 mV rms, 30% of the 300 mV
CML latch swing.

### The one number that is not clean

**r[3] is anomalous in two of the four runs and unexplained.** Stage 1 gives
−0.0964 (3.05σ) and swap 3 gives −0.0900 (2.85σ) — same lag, same sign, similar
magnitude, from configurations sharing almost nothing. Swap 1 and swap 2 show
nothing at that lag.

Two of four could still be chance, and no mechanism is proposed here. It is
recorded as *unexplained* rather than negligible. The resolving measurement is
10,000 bits, which drops the detection floor from 0.0316 to 0.0100: a real −0.09
would stand at 9σ, a fluctuation would shrink toward zero.

### What these numbers do not establish

1,000 bits bounds serial correlation to roughly ±3%; it does not measure it
precisely. Qualification against NIST SP 800-90B needs 10⁶ samples plus a
1000 × 1000 restart matrix, and AIS-31 T4 needs 40,200 bits over lags 3–100.
None of that has been run. These are bring-up statistics, not a randomness claim.

## Files

Every result is paired with the deck that produced it and the simulator log that
proves it ran. A bit file without both is not evidence.

```
run/tb_p1_stage1_behavioral.spice       ngspice_stage1_behavioral.log       pbit_stream_stage1_behavioral.csv
run/tb_p1_swap1_real_noise_gen.spice    ngspice_swap1_real_noise_gen.log    pbit_stream_swap1_real_noise_gen.csv
run/tb_p1_swap2_real_preamp.spice       ngspice_swap2_real_preamp.log       pbit_stream_swap2_real_preamp.csv
run/tb_p1_swap3_real_comparator.spice   ngspice_swap3_real_comparator.log   pbit_stream_swap3_real_comparator.csv
```

The swap-3 log opens with an audit trail listing all 100 noise tone frequencies,
phases and amplitudes, so the excitation can be checked without reading the deck.
All 100 lie between 117.7 MHz and 2.526 GHz and none is within 1% of any integer
division of the 5 GHz sampling clock — verified by parsing the log, not by
trusting the header.

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2
installation.

## How the noise is excited, and why it is not `trnoise`

ngspice's `trnoise` updates on a fixed grid. With a 20 ps step against a 200 ps
clock the two grids are commensurate, and the solver's timestep collapses when a
noise update lands on a clock edge. Moving the step to 23 ps relocated the abort
from 100 ps to 920 ps — which is exactly 40 × 23 ps, and exactly where the fifth
clock falling edge ends. The mechanism is a simulation artifact: real device noise
is continuous and has no update grid, so this failure cannot occur in silicon.

The excitation used here is a sum of 100 tones with random phases, irregular
spacing, spanning the sampled band, evaluated offline and applied as a
piecewise-linear source at 10 ps resolution. It is smooth at the scale of the
underlying bandwidth, so the solver has nothing to trip over, and the sum of many
randomly phased tones is Gaussian to well beyond the precision this measurement
needs.
