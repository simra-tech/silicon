# P1_NOISE_AMP — broadband preamplifier

Two-stage degenerated HBT CML pair. Takes the differential noise from
[`../noise-generator/`](../noise-generator/) and lifts it to a level a clocked
comparator can decide on.

## Measured

| Quantity | Value | How |
| --- | --- | --- |
| Passband gain | **21.54 dB** (11.94×) | `run/ngspice_stdout.out`, `gain_db` table |
| Input-referred noise | 2.158 nV/√Hz | same run, `inoise_spectrum` |
| −3 dB bandwidth, standalone | 31.29 GHz | referenced to the passband peak |
| −3 dB bandwidth, **cascaded** | **5.34 GHz** | interface pole, see below |
| DC power | 10.0 mW | 4.0 mA total from 2.5 V |

The 19.92 dB figure at 100 kHz is low-frequency roll-off, not the passband gain.
Reference the −3 dB point to the **peak**, not to the lowest frequency in the
sweep — doing the latter produced a wrong 50 GHz figure we had to retract.

## The interface pole is the real bandwidth limit

The generator's 1 kΩ collector load driving ~30 fF of amplifier input
capacitance forms a low-pass at **5.34 GHz** that neither block shows when
characterised alone. 1/(2πRC) gives 5.31 GHz independently.

**Chain the blocks in simulation; do not multiply their standalone responses.**
Multiplying assumes infinite amplifier input impedance and overstates the
integrated noise by about 55% (55.8 mV against the correct 35.97 mV). That is a
mistake we made and published before catching it.

### Why the 1 kΩ load stays

| R_C | cascaded BW | margin over residual offset | generator power |
| --- | --- | --- | --- |
| **1 kΩ** | **5.34 GHz** | **67:1** | **5.0 mW** |
| 500 Ω | 9.33 GHz | 54:1 | 10.0 mW |
| 250 Ω | — | 37:1 | 20.0 mW |

Shot-noise voltage scales as √R_C at constant I_C·R_C, so shrinking the load
buys bandwidth and sells signal. The decisive point is that 5.34 GHz is already
**2.1× the 2.5 GHz Nyquist limit** of a 5 GS/s sampler: the extra bandwidth is
unusable, and it would cost margin and double the generator power.

## Not run

| Check | State |
| --- | --- |
| Layout, extraction, post-layout bandwidth | **Not run.** No layout exists. |
| Linearity, compression, supply rejection | **Not run.** |
| Silicon measurement | **Not done.** |
