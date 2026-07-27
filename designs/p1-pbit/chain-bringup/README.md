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
| stage 1 | behavioural `trnoise` + RC | behavioural VCVS | post-processed | complete |
| swap 1 | **`P1_NOISE_GEN`, transistors** | behavioural VCVS | post-processed | complete |
| swap 2 | **`P1_NOISE_GEN`** | **`P1_NOISE_AMP`, transistors** | post-processed | complete |

The decision is done in post-processing in all three: the differential output is
sampled every 200 ps and compared against a threshold. No clocked comparator is
instantiated, so no clock exists in these decks.

Behavioural blocks are calibrated to measurements taken from the transistor
blocks themselves — 36.42 nV/√Hz differential from the generator's `.noise` run,
11.97 V/V and a 31.29 GHz pole from the preamplifier's AC run.

## Measured bit statistics

1,000 sampled bits per run. The 1σ detection floor for a correlation estimate at
N = 1000 is 1/√N = **0.0316**, so any |r| below that is unresolvable, not zero.

| statistic | stage 1 | swap 1 | swap 2 | expected |
| --- | ---: | ---: | ---: | ---: |
| P(bit = 1) | 0.4830 | 0.4680 | 0.5210 | 0.5 ± 0.0316 |
| r[1] | +0.0340 | −0.0213 | −0.0088 | 0 ± 0.0316 |
| r[2] | −0.0552 | −0.0002 | −0.0158 | 0 ± 0.0316 |
| r[3] | **−0.0964** | +0.0088 | −0.0007 | 0 ± 0.0316 |
| r[4] | +0.0091 | +0.0037 | −0.0359 | 0 ± 0.0316 |
| longest run | 9 | 9 | **8** | ≈ 10 |

**A transistor-level HBT noise generator feeding a transistor-level HBT
preamplifier produces bits with a longest run of 8 against an expectation near
10, and no correlation resolvable above the floor.**

### The one number that is not clean

Stage 1's r[3] = −0.0964 is **3.05σ** outside the floor. It is the largest
deviation in the table and the only one outside it. It does not appear in either
swap, and across four lags a 3σ outlier arrives about 1% of the time, so it is
probably a finite-sample fluctuation — but it is recorded here as *unexplained*
rather than negligible, and the remedy is more bits.

### What these numbers do not establish

1,000 bits bounds serial correlation to roughly ±3%; it does not measure it
precisely. Qualification against NIST SP 800-90B needs 10⁶ samples plus a
1000 × 1000 restart matrix, and AIS-31 T4 needs 40,200 bits over lags 3–100.
None of that has been run. These are bring-up statistics, not a randomness claim.

## Files

Every result is paired with the deck that produced it and the simulator log that
proves it ran. A bit file without both is not evidence.

```
run/tb_p1_stage1_behavioral.spice     ngspice_stage1_behavioral.log     pbit_stream_stage1_behavioral.csv
run/tb_p1_swap1_real_noise_gen.spice  ngspice_swap1_real_noise_gen.log  pbit_stream_swap1_real_noise_gen.csv
run/tb_p1_swap2_real_preamp.spice     ngspice_swap2_real_preamp.log     pbit_stream_swap2_real_preamp.csv
```

Reproduce with `ngspice -b <deck>` after setting `$PDK_ROOT` to an IHP SG13G2
installation.

## Swap 3 is not here

Replacing the post-processed decision with the transistor comparator and its
5 GS/s clock is not published, because it does not yet work. The chain completes
200 ns, but the output is the pattern `1100` repeating — 99.9% of samples are
identical to the sample four places earlier, r[2] = −0.998, r[4] = +0.998,
longest run 3. That is a periodic waveform with no entropy in it, not a bitstream,
and it is under investigation.
