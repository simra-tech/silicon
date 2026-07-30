# Clock kickback, isolated as clocked minus clock-frozen

Kickback is the part of the input differential that the clock puts there. You
cannot read it off a clocked run directly, because the input differential in a
clocked run also contains a **static** term: in track mode the input pair draws
base current through the 120 Ω source resistors, and that costs real millivolts of
signal before any clock edge happens.

So the measurement is a difference of two runs that are identical except for the
clock, with the baseline frozen **in the same phase as the sample**:

| deck | clock | applied input | what it gives |
| --- | --- | --- | --- |
| `kick_A_clocked_10mv` | 5 GS/s, 0 → 1.2 V, 20 ps edges | +10 mV | the total, static plus kickback |
| `kick_B_frozen_track_10mv` | held at CLK_P = 1.2 V (track) | +10 mV | the static baseline for a track-phase sample |
| `kick_D_frozen_latch_10mv` | held at CLK_P = 0 V (latch) | +10 mV | the static baseline for a latch-phase sample |
| `kick_C_clocked_0mv` | 5 GS/s | **0 mV** | shows why the symmetric case cannot measure this |

## Result

| | clocked | frozen, same phase | kickback |
| --- | --- | --- | --- |
| end of latch phase, 500 / 700 / 900 ps | 10.0213 / 10.0208 / 10.0204 mV | 10.00000 mV | **+21.3 / +20.8 / +20.4 µV** |
| end of track phase, 800 / 1000 ps | 9.94441 / 9.94461 mV | 9.94144 mV | **+3.0 / +3.2 µV** |

Repeatable to about 1 µV across three consecutive cycles, so it is deterministic
rather than noise-like — which means a static trim removes it, if it needed
removing. Against 38.98 mV_rms of noise at the comparator input, 20.4 µV is a bit
probability bias of

    ΔP = (1/√(2π)) · 20.4 µV / 38.98 mV = 0.021 %

against a 1% budget, so it does not.

## The two things this measurement separates out

**Static differential attenuation is not kickback.** Frozen in track the input
differential is 9.94144 mV, not 10 mV — 58.6 µV lost across the 120 Ω source
resistors to input-pair base current. Frozen in latch it is 10.00000 mV exactly,
because the track pair is off and no base current flows. That 0.586% is a **gain
error, not an offset**: it scales with the signal, so it does not bias the bit. A
clocked run that does not subtract this baseline attributes all of it to the clock.

**Peak excursion during an edge is not the sampled value.** `diff_max` / `diff_min`
in run A are **+23.8 mV / −5.1 mV** — the differential genuinely swings that far
while an edge is happening. By the sampling instants it has decayed to the tens of
microvolts above. Peak matters for compression and for what the preamplifier has
to recover from; only the sampled value biases the bit.

## Why the 0 mV run is here

`kick_C_clocked_0mv` applies **equal** inputs and reports a sampled differential of
28 µV and −0.08 µV at the two instants — near zero. That is not evidence that
kickback is small. In a netlist with no mismatch enabled the two halves are
identical, so a clock disturbance that arrives on both sides cancels in the
difference **by construction**. The measurement returns approximately zero however
large the kickback is; it has no failure path. Its `diff_max` / `diff_min` of
±14 mV show the disturbance is there.

Kickback is only observable differentially once the two halves carry different
currents, which is why every measurement above applies a real input.

## Reproducing

```
ngspice -b kick_A_clocked_10mv.cir
ngspice -b kick_B_frozen_track_10mv.cir
ngspice -b kick_D_frozen_latch_10mv.cir
ngspice -b kick_C_clocked_0mv.cir
```

`$PDK_ROOT` is the IHP SG13G2 PDK root. Sampling instants follow the clock
definition — see `../clocked-both-polarities/README.md` for the derivation of
900 ps and 1000 ps.
