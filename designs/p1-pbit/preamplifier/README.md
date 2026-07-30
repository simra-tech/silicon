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

## The rebuild on real PDK devices

Everything above was simulated with **ideal SPICE passives** — `RC1_1 VCC c1_n 240`,
`ISET1 e1_common VSS DC 2.0m` — as recorded in [`../README.md`](../README.md). The schematic has
since been rebuilt so that every passive is a drawable `rppd` or `cap_cmim` and both tail
sources are real degenerated HBT mirrors. Deck, log and netlist in
[`rebuild-2p5v/`](rebuild-2p5v/).

| quantity | ideal-passive version (above) | rebuilt on PDK devices |
| --- | ---: | ---: |
| passband gain, ideal drive | 21.54 dB | **21.285 dB** |
| passband gain, driven from the generator | — | **20.953 dB** |
| −3 dB bandwidth, standalone | 31.29 GHz | **19.091 GHz** |
| −3 dB bandwidth, driven from the generator | 5.34 GHz (computed) | **5.258 GHz (simulated)** |
| tail current per stage | 2.0 mA (ideal source) | **1.787 mA** (mirror) |
| total supply current | 4.0 mA | **3.657 mA**, 9.14 mW |

**What made the resistors change value.** An ideal `240` is 240 Ω; the `rppd` you can draw is
its body plus `70 Ω·µm / w` of contact end resistance at the two contacts (see
[`../noise-generator/layout/`](../noise-generator/layout/)). The collector loads are drawn
w = 1.0 µm, l = 0.7115 µm and **measure 255 Ω**; the degeneration is w = 13.333 µm, l = 0.5 µm
and measures 15.0 Ω. Sized against the formula alone they would have come out 28% low.

### The interface pole, now measured rather than computed

The section above derives a 5.34 GHz cascaded corner from 1 kΩ driving ~30 fF, and warns
*"chain the blocks in simulation; do not multiply their standalone responses."* That warning is
now testable against a full AC sweep of the rebuilt amplifier. Taking its own testbench and
changing nothing except a 1059 Ω resistor in series with each input — the noise generator's real
collector load — the corner moves from **19.091 GHz to 5.258 GHz**, a 3.6× reduction, and the
gain falls 0.33 dB.

5.258 GHz back-solves to **28.6 fF** of single-ended input capacitance against the earlier
estimate of ~30 fF. A different device set, different sizing and 2 pF of coupling capacitance
that did not exist before, arriving within 1.5% of a figure this repository published for the
ideal-passive design. **The prediction was independently reproduced, and that is worth more than
either number alone.**

**Carry the loaded figures, not the standalone ones.** 19 GHz beside a 5 GS/s sampler reads as
enormous margin. 5.26 GHz is only just above the rate the comparator is meant to run at, and it
is a constraint rather than a comfort.

### Reproducing it

    ngspice -b tb_p1_noise_amp_ac.cir           # ideal drive:      21.285 dB, 19.091 GHz
    ngspice -b tb_p1_noise_amp_ac_cascade.cir   # 1059 Ω drive:     20.953 dB,  5.258 GHz
    ngspice -b tb_p1_mirror_sweep.cir           # tail vs V_ce

`p1_noise_amp_clean.spice` is the netlist both AC decks include. It is an xschem export of the
schematic with the `**.subckt` / `**.ends` wrapper uncommented — mechanically necessary to
instantiate it, and the device lines are byte-identical to a fresh export. That is stated because
an earlier revision of this block carried a *hand-written* netlist wearing an exporter's header,
and a reference maintained by hand cannot disagree with the schematic it claims to describe.

## Not run

| Check | State |
| --- | --- |
| Corners and temperature on the rebuilt amplifier | **Not run.** Every figure in the rebuild table is `hbt_typ` / `res_typ` / `cap_typ` at 27 °C. `rppd` carries tc1 = +170 ppm/K and the HBT emitter resistance its own, so 20.95 dB against a 20 dB floor has **0.95 dB** of margin that has not been tested against any of it. The operating temperature range is still unspecified for P1, which is what blocks this. |
| Mismatch | **Not run.** No Monte Carlo on the rebuilt schematic. |
| Layout, extraction, post-layout bandwidth | **Not run.** No layout exists for this block. |
| Linearity, compression, supply rejection | **Not run.** |
| Silicon measurement | **Not done.** |
