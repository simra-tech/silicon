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

## Sizing it: R_dac buys authority back, and does not buy swing range

Rearranging, with x the voltage across R_dac (so I_trim = x/R_dac and
g_m = I_trim/V_T):

    A_trim = R_C / (R_dac + V_T·R_dac/x)   →   I_trim = A_trim·(x + V_T)/R_C

So for a required authority, the current depends only on **x**, not on R_dac. Reduce
R_dac and raise nothing else, and authority comes back at a fraction of the current.
Measured, sweeping both:

| R_dac | V(TRIM) | I_trim | Δ(c_p−c_n) per 20 mV | authority | relation predicts |
| --- | --- | --- | --- | --- | --- |
| 1474 Ω, as built | 1.440 V | 415.0 µA | −3.510 mV | 0.1755 | 0.188 |
| 1474 Ω, proposed | 0.810 V | 35.07 µA | −2.459 mV | 0.1230 | 0.130 |
| **820 Ω** | 0.780 V | 30.5 µA | −3.230 mV | 0.1615 | — |
| **820 Ω** | **0.800 V** | **43.4 µA** | −3.811 mV | **0.1906** | 0.203 |
| **300 Ω** | 0.780 V | 45.7 µA | −6.145 mV | 0.3073 | — |
| **300 Ω** | **0.800 V** | **71.8 µA** | −8.018 mV | **0.4009** | 0.436 |

Every prediction within 9%. **R_dac = 820 Ω at V(TRIM) = 0.800 V gives more authority than
the as-built design (0.1906 against 0.1755) at 9.6× less current.** Both requirements at
once, which is what two knobs should deliver.

## But the binding constraint is swing range, not authority — and it does not separate

The trim needs to swing *downward* to inject in one direction, and a bipolar pair with an
emitter resistor to ground has almost none. At the 300 Ω point the emitter node sits at
71.8 µA × 300 Ω = **21.5 mV**, so V_BE = 0.7785 V and the base cannot go below about
0.70 V before the device stops conducting. That is **~100 mV of downward range** against
the ±241 mV the ±40.1 mV specification needs at this authority.

| config | swing needed for ±40.1 mV | downward swing available | works? |
| --- | --- | --- | --- |
| 1474 Ω / 1.440 V, as built | ±550 mV | **~640 mV** | **yes** |
| 1474 Ω / 0.810 V, proposed | ±785 mV | ~10 mV | no |
| 820 Ω / 0.800 V | ±508 mV | ~100 mV | no |
| 300 Ω / 0.800 V | ±241 mV | ~100 mV | no |

**The as-built 1.440 V bias is the only one of the four with enough downward range** — and
the 415 µA everyone wants to remove is exactly what buys it. Since I_trim = x/R_dac and the
downward range is approximately x, **both are proportional to the same voltage**: no choice
of R_dac separates them.

This corrects the framing in the section above. R_dac is a second knob for *authority*. It
is not a second knob for *range*, and range is what binds.

## So the fix is a topology change, and here are the three that work

1. **Steer current instead of driving base voltages.** A DAC that divides a fixed tail
   between the two trim devices needs no base swing at all: the range comes from the
   steering ratio, and the static current is whatever the tail is set to. This is the
   conventional answer and it removes the constraint rather than trading against it.
2. **Lift the emitter reference.** Return R_dac to a voltage above ground rather than to
   VSS, so the emitter node sits high enough to allow downward base swing at low current.
   Costs a reference.
3. **Reduce the range.** ±40.1 mV is ~6σ of the published 6.46 mV untrimmed offset. At ±3σ
   the swing needed halves and the 820 Ω / 0.800 V point comes within reach. **This is a
   specification decision, not a circuit one, and it is the cheapest of the three if the
   margin is genuinely not needed.**

None of these is sized here. What is established is that the first two are the only
circuit-level escapes, that the third is the cheapest, and that no combination of R_dac and
bias voltage solves it — which is worth knowing before more of them are simulated.

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
