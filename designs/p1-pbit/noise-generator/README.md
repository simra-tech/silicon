# P1_NOISE_GEN — HBT noise generator

The entropy source for the P1 p-bit: a differential pair of `npn13G2` HBTs on a
shared tail current source, 1 mA per branch into a collector load drawn for 1 kΩ —
1059 Ω once the model's contact end resistance is included, see
[`layout/README.md`](layout/README.md) —
with the noise taken differentially across the two collectors. Every simulated result
below already used 1059 Ω, because ngspice evaluates the full model card.

This is the first block of P1 to exist as a circuit rather than as a paragraph.

## Schematic-backed hierarchy source

[`source-backed-v1/`](source-backed-v1/) publishes the current Xschem source,
retained raw and ordered symbols, one-instance hierarchy, generated netlist,
and normalized generation evidence. It establishes source-to-netlist binding
only; it does not supersede or extend the electrical results below.

## Measured

| Quantity | Value | How |
| --- | --- | --- |
| Differential output noise density | **36.42 nV/√Hz** at 1 GHz | `.noise` analysis, `run/ngspice_stdout.out` |
| Input-referred noise density | 2.382 nV/√Hz | same run, `inoise_spectrum` |
| Differential gain | 15.3 (23.7 dB) | ratio of the two above |
| Bias point | I<sub>C</sub> = 1.0 mA per branch, R<sub>C</sub> = 1.0 kΩ | `tb_p1_noise_gen.spice` |

Read `onoise_spectrum` directly. `.noise v(raw_p, raw_n)` already reports the
**differential** density — applying a further √2 is a mistake we made and had to
retract.

## Where the noise comes from

Shot noise from the collector current plus thermal noise of the load resistor
account for 25.96 nV/√Hz differential. The measurement is 40% above that.

The excess is not mysterious. Referred to the input it is 1.670 nV/√Hz, which is
the thermal noise of a **168 Ω** resistor. The device model carries 137.7 Ω of
base resistance (`rbi` + `rbp` + `rbx`) and 28.5 Ω of emitter resistance:
**166.2 Ω**. Two independent routes to the same number.

**This is therefore not a pure shot-noise source.** Roughly 40% of the noise
amplitude comes from parasitic series resistance inside the transistor. That is
not a problem — more noise is the product here — but it scales differently with
bias current than shot noise does, and any later re-biasing has to account for
both mechanisms rather than one.

## Not run

| Check | State |
| --- | --- |
| Per-device noise contribution breakdown | **Not available.** ngspice does not emit an itemised per-device table for this OSDI/VBIC subcircuit configuration. The attribution above is derived from the input-referred excess, not read from the simulator. |
| Transient behaviour, autocorrelation, P(bit=1) | **Not run.** No transient simulation of the assembled chain exists. |
| Layout, extraction, post-layout noise | **Not run.** No layout exists. |
| Silicon measurement | **Not done.** Nothing has been fabricated. |

## Files

- `p1_noise_gen.sch` — xschem schematic
- `p1_noise_gen.spice` — extracted subcircuit netlist
- `run/tb_p1_noise_gen.spice` — the noise-analysis deck, including the bias sources
- `run/ngspice_stdout.out` — raw simulator output, columns `onoise_spectrum` then `inoise_spectrum`
