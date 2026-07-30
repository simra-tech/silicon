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

## RETRACTED: a combination does solve it, at 3σ

**The paragraph above is wrong and the swing analysis it rests on is wrong.** It assumed the
trim swings symmetrically and is limited by the down-side turning off. That is the behaviour
of a differential pair sharing a tail. **This is not one** — `XQDAC_P` and `XQDAC_N` each
have their own emitter resistor to ground, so they are two independent common-emitter
stages. The down side simply switches off and stops mattering; **the range is bought on the
up side**, where current grows without a turn-off limit.

Sweeping the TRIM differential at R_dac = 820 Ω, V(TRIM) = 0.800 V:

| TRIM differential | c_p − c_n | input-referred trim | P-side current |
| --- | --- | --- | --- |
| 0 | 0 | 0 | **43.4 µA** |
| 50 mV | −9.462 mV | 1.961 mV | 62.2 µA |
| 100 mV | −18.475 mV | 3.830 mV | 83.2 µA |
| 200 mV | −34.416 mV | 7.135 mV | 129.4 µA |
| 300 mV | −48.782 mV | 10.112 mV | 179.2 µA |
| 400 mV | −63.068 mV | 13.073 mV | 231.0 µA |
| 500 mV | −77.608 mV | 16.087 mV | 284.2 µA |
| **600 mV** | **−92.384 mV** | **19.150 mV** | **338.2 µA** |

Input-referred through the measured 4.824 V/V input-pair gain.

**±19.15 mV at ±600 mV of swing — the 3σ target of ±19.38 mV, reached.** And the current
profile is better than the design it replaces: **43.4 µA at mid-code** against the as-built
**415 µA at every code**, with 338 µA only at the extremes where the trim is actually
working hard.

The transfer compresses: 0.0392 mV/mV at small signal falling to 0.0319 over the full range,
about **19% compression end to end**. That is a DAC linearity figure and it has not been
apportioned across codes — worth measuring per code before the ten-bit resolution is
claimed, because 19% of compression against a 1024-step ladder is not obviously benign.

**±40.1 mV (6σ) remains out of reach on this topology.** Extrapolating the same slope needs
about 1.26 V of differential swing and roughly 700 µA at full scale. So the specification
decision still decides the topology — but it now decides between *3σ with a resistor change*
and *6σ with a current-steering DAC*, rather than between a topology change and nothing.

**Why the earlier analysis failed.** It applied the behaviour of a shared-tail differential
pair to a circuit that is two independent stages. That is the same error as the earlier claim
that this pair was "essentially off" at a 1.440 V bias — also reasoned from a shared tail,
also wrong, and also about these same two devices. **Twice now the topology next door has
been substituted for the one actually drawn.** The check that catches it is trivial and was
available both times: look at where the emitters go.

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

## Full scale: the range holds, the peak current does not, and the DNL is normalised wrong

A 16-point linearity sweep of the 820 Ω point was produced independently, driving `TRIM_P`
from 0.800 V to 1.400 V single-ended with `TRIM_N` held. Three things about it, measured
here on the same netlist.

**The range claim holds.** At `TRIM_P` = 1.400 V the collector differential is −171.912 mV,
which referred through the measured 4.824 V/V input-pair gain is **35.63 mV** against the
32.42 mV claimed — within 10%, so ±5σ of the 6.46 mV untrimmed offset is genuinely reachable
at this operating point.

**The peak current is not stated and it is worse than the design being replaced.**

| `TRIM_P` | input-referred trim | P-side current | `c_p` |
| --- | --- | --- | --- |
| 0.800 V, mid-code | 0 | **43.4 µA** | 2.211 V |
| 1.200 V | 22.93 mV | 448.2 µA | 2.096 V |
| 1.300 V | 29.25 mV | 559.8 µA | 2.065 V |
| **1.400 V, full scale** | **35.63 mV** | **672.5 µA** | 2.033 V |

Static current is genuinely 9.6× better than the as-built 415 µA. **Full-scale current is
672.5 µA — 62% worse.** A report that quotes the static figure as a power saving and omits
the peak has described half of the change. Whether the peak matters depends on how often
large trim codes are used, which is a yield question, but it belongs in the table.

**The DNL and INL are normalised to a 16-point LSB, which flatters them by about 64×.**
The reported step sizes grow monotonically across the sweep — 1.571, 1.806, 1.954, 2.054,
2.131, 2.169, 2.212, 2.242, 2.269, 2.293, 2.313, 2.331 mV — a **48% increase end to end**,
which is the expected convexity of a base-driven bipolar stage. Normalised to the *average
of those coarse steps*, that appears as DNL of −0.273 … +0.078 LSB and peak INL of
+0.598 LSB, which reads as an excellent converter.

But the ladder being claimed is **10 bits**, so its LSB is 32 mV / 1023 ≈ **31.3 µV**, not
the ~2.13 mV coarse step. Restated in the units of the converter it is supposed to be:

    peak INL ≈ 0.598 × 2.13 mV / 31.3 µV ≈ 41 LSB

**Forty-one LSB of integral nonlinearity on a 10-bit ladder.** That is not necessarily
disqualifying — a trim needs monotonicity and fine local steps near the correction point far
more than it needs absolute accuracy across full scale, and the transfer is monotonic
throughout. But it must be stated in the converter's own units, and the acceptance criterion
should be **local step size near the trim point and monotonicity**, not INL against full
scale. As it stands the 48% step-size variation means the effective trim resolution is half
as fine at one end of the range as the other.

## The interface bias moves with the trim code, and it is mostly differential

Worth recording because the alarming reading of it is wrong. Across the trim range the
CML→CMOS load nodes move a long way:

| `TRIM_P` | `cml_out_p` | `cml_out_n` | differential | common mode |
| --- | --- | --- | --- | --- |
| 0.800 V | 0.6336 V | 0.6336 V | 0 | 0.634 V |
| 0.840 V | 0.6060 V | 0.6364 V | −30.3 mV | 0.621 V |
| 1.100 V | 0.3809 V | 0.6597 V | −278.8 mV | 0.520 V |
| 1.400 V | 0.1516 V | 0.6892 V | −537.6 mV | **0.420 V** |

Measuring `cml_out_p` alone suggests the node is being driven 448 mV below the trip
point and the interface destroyed. Measuring both shows it is **mostly differential** — which
is exactly what a trim is for. A large applied trim *should* bias the comparator hard toward
one output; that is what correcting a large offset means.

What is real is the **common-mode droop: 214 mV across the range**, which reduces the
headroom the signal has at large trim codes. That is second-order rather than fatal, and it is
recorded with its number rather than as an alarm. It is also an argument for a current-steering
trim, which redistributes a fixed total current and leaves the collector common mode
unchanged — a property this base-driven version does not have.

## Current-steering candidate: the first reproducible static result

A fixed-tail current-steering candidate has now been measured with one retained deck and log at
three explicit base-voltage pairs. The complete package is in
[`current-steering-670ua/`](current-steering-670ua/).

At a 670 uA steering tail, the collector-differential zero crossing moves **-34.593 mV** and
**+34.607 mV** relative to midpoint. Total VCC current changes by 1.467 uA and collector common
mode by about 0.209 mV across the three points. The fixed-current premise is therefore supported
for this static experiment, but the authority is not enough: both endpoints remain about 5.49 mV
inside the specified ±40.10 mV range.

This does not select the current-steering architecture. It establishes one static candidate at
one tail current and one corner. Code transfer, local step size, mismatch, dynamic behavior and
full-chain headroom remain unmeasured.

The immediately preceding one-deck attempt is retained in
[`failed-unified-stimulus/`](failed-unified-stimulus/). Its dependent sources generated the wrong
trim voltages and its log contains a parser error; it is evidence of a failed stimulus, not of the
candidate's authority.

Scaling only the fixed tail from 670 uA to **780 uA** produces **-40.722 mV** and
**+40.677 mV** of endpoint authority relative to midpoint. That clears the nominal ±40.10 mV
static requirement at the tested 27 °C typical condition. The complete package is in
[`current-steering-780ua/`](current-steering-780ua/).

The 780 uA pair is the current front-runner, not a selected architecture. A follow-up
[`33-point analog-control sweep`](current-steering-780ua-33point/) is strictly monotonic at its
sampled points, but its adjacent threshold steps range from **46.412 uV to 7.172 mV**, a roughly
154.5:1 variation. The correct median step is **1.450 mV**. That sweep drives ideal analog base
voltages; it does not establish a physically implemented digital code transfer or zero missing
codes. A realizable code mapping, corner and mismatch behavior, and dynamic integration with the
comparator remain open.
