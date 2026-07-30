# Trim authority, and why moving the trim bias trades against it

The trim pair was found drawing **415 µA per side** — 21% of the comparator's 1.96 mA
tail — because `TRIM_P` / `TRIM_N` sit at 1.440 V while the comparator's input common
mode is 2.139 V. See
[`../../../chain-bringup/bit-autocorrelation/`](../../../chain-bringup/bit-autocorrelation/)
for how that surfaced.

Re-biasing `TRIM` to **0.810 V** was proposed to remove that parasitic load. It does
remove it. It also costs 30% of the trim's authority and leaves too little headroom
below, and both of those follow from one relation that is worth writing down.

## Measured, at DC

| TRIM common mode | trim current per side | Δ(c_p − c_n) per 20 mV of TRIM differential | `c_p` |
| --- | --- | --- | --- |
| **1.440 V**, as built | **415.0 µA** | −3.510 mV → 0.1755 V/V | 2.10299 V |
| **0.810 V**, proposed | **35.07 µA** | −2.459 mV → 0.1230 V/V | 2.21140 V |

The proposal works on its own terms: the static current falls **11.8×** and `c_p` rises
108 mV, recovering the collector headroom the trim was eating.

Note the measured current is **35.07 µA**, not the 20.0 µA the derivation predicted — the
V_BE assumed at that current was 0.780 V and the device settles elsewhere. A 75% error in
a current that sets a bias point is worth knowing about before it propagates.

## Referred to the input, which is the only form that can be compared to the spec

The input pair's gain to the same collectors, measured the same way: 2 mV differential in
gives **+9.648 mV** out, so **4.824 V/V**. (The trim's sign is opposite, as a trim should
be.) Dividing:

| TRIM common mode | input-referred authority | TRIM differential swing for ±40.1 mV | TRIM_P range |
| --- | --- | --- | --- |
| 1.440 V | 0.0364 mV/mV | **±1.10 V** | 0.89 … 1.99 V |
| 0.810 V | 0.0255 mV/mV | **±1.57 V** | **0.02 … 1.60 V** |

The specification asks for **±40.1 mV** of input-referred trim over 10 bits, at
78.32 µV/code.

At the as-built bias that needs ±1.10 V of differential swing on TRIM — large, but it
sits comfortably inside the 2.5 V rail, and the per-code step is 2.15 mV. **At the
proposed bias it needs ±1.57 V, which puts the bottom of the range at 24 mV** — the trim
device is fully off there, so the lower half of the range is unusable and grossly
nonlinear. The proposal does not restore full trim authority; it reduces it.

## The relation that governs it

The trim pair is an emitter-degenerated stage, so its authority is

    A_trim = R_C / (R_dac + 1/g_m),   g_m = I_trim / V_T

with R_C = 288 Ω and R_dac = 1.474 kΩ. That predicts:

| | 1/g_m | predicted A_trim | measured |
| --- | --- | --- | --- |
| 415 µA | 62 Ω | 0.188 | 0.1755 |
| 35 µA | 739 Ω | 0.130 | 0.1230 |

Both within 7%, so the relation holds. **At 415 µA the stage is degeneration-limited** —
authority ≈ R_C/R_dac = 0.195, nearly independent of current, which is why cutting the
current 11.8× costs only 1.43× of authority. But at 35 µA the 1/g_m term dominates and
further current reduction attacks authority directly.

**So current and authority trade, and the bias voltage alone cannot separate them.** What
separates them is **R_dac**: reducing it restores authority at a given current, and the
bias voltage is then set to whatever produces that current. Two requirements, two knobs.

Sizing them is not done here. What is established: the single-knob fix does not work, the
relation above is the one to size against, and the trim's static current and its authority
cannot both be chosen freely.

## What is not established

The ±40.1 mV specification itself has not been re-examined against the offset it exists to
correct. The published untrimmed offset σ is 6.46 mV, so ±40.1 mV is roughly ±6σ. Whether
that margin is needed, and whether a smaller range with proportionally finer steps would
serve better, is a specification question nobody has revisited since the range was chosen —
and it is worth asking before sizing R_dac, because a smaller range costs less authority.

## Reproducing

```
ngspice -b t_asbuilt_0.cir        # TRIM at 1.440 V, no differential
ngspice -b t_asbuilt_0.020.cir    # TRIM at 1.440 V, 20 mV differential
ngspice -b t_proposed_0.cir       # TRIM at 0.810 V
ngspice -b t_proposed_0.020.cir
ngspice -b ig_0.cir               # input-pair gain reference
ngspice -b ig_0.002.cir
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. All runs are `.op` with the clock frozen in the
track phase; the trim and input-pair transfers are differences between adjacent runs.
