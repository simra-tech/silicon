# P1 — SiGe BiCMOS probabilistic bit (p-bit)

A probabilistic bit: a circuit that produces a genuinely random digital bit every
clock edge by amplifying the physical noise of a transistor and slicing it with a
fast comparator. Not a pseudo-random generator — the entropy is device physics.

Target process is the IHP SG13G2 open PDK (0.13 µm SiGe BiCMOS). The die is
probe-pad only: no wire-bonds, no package, everything landed on top-metal GSG and
DC pads for wafer probing.

**State: in specification. Nothing has been fabricated. Nothing has been taped
out. No layout exists. No gate has been signed off, and no foundry signoff is
claimed anywhere in this directory.**

## What the chip is meant to do

| Block | Function | Devices | Area |
| --- | --- | --- | ---: |
| `P1_NOISE_GEN` | Entropy source — forward-biased HBT collector shot noise into a 1 kΩ collector load | `npn13G2` SiGe HBT | 0.03 mm² |
| `P1_NOISE_AMP` | Broadband preamplifier, 20–23 dB, AC-coupled to suppress 1/f | `npn13G2` HBT CML differential pairs | 0.05 mm² |
| `P1_COMPARATOR` | Clocked decision latch, 10-bit offset trim DAC, CMOS output drivers | HBT CML **and** CMOS | 0.04 mm² |
| `P1_NOISE_TEST` | On-die noise monitor — replica source with a 50 Ω GSG breakout, so raw S<sub>v</sub>(f) can be probed independently of the comparator | `npn13G2` HBT | 0.05 mm² |
| `P1_PAD_ARRAY` | Probe pad ring, 100 µm pitch, ESD diodes | TopMetal2 / Metal5 | 0.15 mm² |
| **Total** | | | **0.32 mm²** |

0.32 mm² sits inside the 0.20–0.50 mm² area budget the design is held to.

Full spec and the top-level block diagram:
[`specification/P1_TOP_LEVEL_SPECIFICATION.md`](specification/P1_TOP_LEVEL_SPECIFICATION.md).

## Built against

| Thing | Version | How it was established |
| --- | --- | --- |
| PDK | IHP SG13G2, commit `144f811cdffda49b71d28f64e8a92b697b61cf06` | the `COMMIT` file at the PDK install root |
| ngspice | `ngspice-46` | printed by the simulator at the end of every `ngspice_stdout.out` under `characterisation/runs/` |
| xschem | `3.4.8RC` | the `v {xschem version=...}` header line of every `.sch` file here |
| CACE | `2.9.0` | `cace --version` |

The PDK is unpacked from a release tarball rather than cloned, so it is not a git
checkout — the commit hash above is the one the PDK itself records in its `COMMIT`
file, and is the only revision identifier available. Paths in this directory are
written relative to the design root or as `$PDK_ROOT/ihp-sg13g2/...`; the absolute
paths of the machine the runs happened on have been rewritten out.

## What was actually measured

### 1. HBT comparator input offset — the result that changed the design

A 500-sample Monte Carlo of the HBT differential pair, using the PDK mismatch
model `sg13g2_hbt_mod_mismatch.lib` in the `hbt_typ_mismatch` corner, gives an
input offset standard deviation of

> **σ<sub>VOS</sub> = 6.683 mV** (minimum geometry, N<sub>x</sub> = 1; mean −0.530 mV)

The design had been carrying an assumed σ<sub>VOS</sub> of 1.0 mV. That assumption
sized the comparator trim DAC at ±6 mV (±6σ of the assumed value) with 8 bits of
resolution.

The measured number is 6.7× larger, and that is the single most consequential
thing found so far. Against a ±6 mV trim range, an offset drawn from a normal
distribution with σ = 6.683 mV falls outside the trim range with probability

    2 · (1 − Φ(6 / 6.683)) = 0.369

so roughly **37% of dies would have been untrimmable** — the comparator would have
sat stuck at 0 or 1 and the part would not have been a p-bit at all. Including the
measured mean of −0.530 mV moves the figure to 37.1%; it does not rescue it.

The trim DAC was resized to **±40.1 mV** (±6 × 6.683 mV = ±40.098 mV) and from
**8 bits to 10 bits**, giving 78.4 µV/LSB across the 80.20 mV full span. Ten bits
is what keeps the LSB fine enough that quantisation error stays small against the
noise the comparator is supposed to be resolving.

Two contributors to the 6.683 mV, both traceable to the PDK model cards, are
identified in the specification: emitter series resistance mismatch (the model
carries `re = 7.13 × (4/Nx)` Ω with a 10% area-mismatch sigma, so 28.52 Ω ± 2.85 Ω
at N<sub>x</sub> = 1) and high-injection roll-off (`ikf = 0.009 × (Nx × 0.25)`, so
I<sub>KF</sub> = 2.25 mA, and the 1.0 mA bias sits at 44% of it).

**Caveat, and it is a real one:** the Monte Carlo run directory was not retained.
The value, the corner, the sample count and the model library are recorded in the
specification, and the model parameters above are independently checkable against
the PDK, but there is no run artefact in this repository from which a reader can
re-derive 6.683 mV. It is **not reproducible from this repository**. Re-running the
500-sample Monte Carlo and committing the output would settle it.

### 2. CMOS inverter switching threshold — 27 conditions, fully reproducible

An inverter is **not** the p-bit, and this characterisation is not a p-bit
measurement. The P1 comparator core is HBT CML; CMOS appears only in the output
level-shifter and drivers. The inverter was characterised early as a **CMOS proxy**
— to exercise the xschem → ngspice → CACE flow end to end on this PDK, and to get
a real number for how much a CMOS trip point moves across corner, supply and
temperature, since the CML-to-CMOS output buffer has to switch cleanly across all
of it.

Twenty-seven DC operating points were simulated: two nine-cell process × supply
matrices at 27 °C (baseline PMOS W<sub>p</sub> = 2.0 µm, and nulled
W<sub>p</sub> = 1.414 µm), and one nine-cell process × temperature matrix at 1.20 V.
Every value in those tables is traceable to a run directory committed here. See
[`characterisation/`](characterisation/).

Headline results:

- Baseline sizing (W<sub>p</sub>/W<sub>n</sub> = 2.0/1.0 µm) carries a systematic
  **+18.3 mV** trip-point offset at the typical corner, 1.20 V, 27 °C.
- Resizing the PMOS to 1.414 µm nulls it to **+0.017 mV** at that one point, and
  shrinks the process spread at nominal supply from 11.2 mV to 3.6 mV.
- **It is a point trim, not a global null.** The same sizing drifts to
  **+5.173 mV at −40 °C** and −1.602 mV at +125 °C in the typical corner. Static
  width tuning cancels offset at one operating point; it does not cancel the
  temperature dependence of mobility and threshold voltage.
- Across all nine process × temperature cells the offset envelope is 10.258 mV
  (+5.708 mV at `mos_ff`/−40 °C down to −4.550 mV at `mos_ss`/+125 °C).

This is why the specification calls for ≥150 mV of differential CML swing into the
CMOS buffer: the buffer's own trip point wanders by about 10 mV over PVT, and the
signal driving it has to be large enough that this does not matter.

### 3. Entropy source choice

The entropy source is **forward-biased HBT collector shot noise**
(i²<sub>n,c</sub> = 2qI<sub>C</sub>Δf), not reverse-biased base-emitter avalanche
breakdown. Avalanche is the more common textbook choice and it was rejected for
two reasons:

1. **It is outside the compact model.** Reverse-bias avalanche breakdown is not
   represented in the PDK's VBIC HBT model cards, so nothing about an
   avalanche-based source could be simulated — it would have to be designed blind
   and settled only on silicon.
2. **It is a documented ageing path.** Reverse-biased emitter-base breakdown
   damages the interface and degrades β over time. A drifting β is a drifting
   noise amplitude, which is a drifting P(bit = 1).

Forward-biased collector shot noise is fully modelled, and collector shot noise is
√β = 25.3× larger than base shot noise at the chosen bias, which is what keeps the
required preamplifier gain down to 20–23 dB.

## What is explicitly not verified

Recorded here as *not run* rather than left out, because an unrun check and a
passed check look identical in a summary table and are completely different facts
about a chip.

| Check | State |
| --- | --- |
| Fabrication | **Not done.** Nothing exists in silicon. |
| Layout, DRC, LVS, parasitic extraction | **Not run.** No layout exists. |
| Tape-out / foundry signoff | **Not done, not claimed.** |
| HBT noise spectral density S<sub>v</sub>(f) | **Not simulated and not measured.** The 18.36 nV/√Hz figure in the specification is a hand calculation of shot plus thermal noise at I<sub>C</sub> = 1 mA, R<sub>C</sub> = 1 kΩ — not an ngspice `.noise` result. Settling it needs an AC noise analysis; the specification gives the analysis line. |
| Total die power | **Not simulated.** The 15–45 mW range in the specification is an estimate, flagged there as Unknown. |
| σ<sub>VOS</sub> = 6.683 mV Monte Carlo | **Ran, but the artefacts were not retained** — see the caveat above. Not reproducible from this repository. |
| HBT f<sub>T</sub> = 379.8 GHz, β = 638.3 | **Extracted from the PDK model in SPICE, but the run artefacts were not retained.** Same status as the Monte Carlo. |
| Preamplifier gain, CML latch speed, 5 GS/s sampling rate | **Not simulated.** No preamp or latch schematic exists yet; these are derived from f<sub>T</sub> and are marked Assumed in the specification. |
| P(bit = 1) = 0.5, bit autocorrelation, NIST/Dieharder randomness | **Not evaluated.** There is no transient simulation of the assembled chain. |
| CMOS inverter switching threshold, 27 PVT points | **Ran and passed.** Every number traceable to a committed run directory. |
| Inverter behaviour outside those 27 points (mismatch, transient, drive strength, load) | **Not run.** The only inverter parameter characterised is the DC switching threshold. |

## What is in this directory

```
specification/    P1 top-level specification, xschem block diagram, rendered SVG
characterisation/ the CMOS inverter proxy work: schematic, CACE spec, DUT netlist,
                  testbench template, the three characterisation matrices, and the
                  seven CACE run directories the tables cite
```

## What was deliberately left out

- **Failed and superseded runs.** The workspace holds 25 CACE run directories.
  Seven are published — the ones the characterisation tables actually cite. The
  rest are bring-up runs that errored or reported 0.000 V while the testbench was
  being made to work, plus one exact duplicate of the `mos_tt` baseline sweep.
  They record the flow being debugged, not a result about the circuit.
- **Two ad-hoc SPICE sweeps** (`temp_sweep`, `mos_tt_sweep`) that reproduce the
  same values through a hand-written testbench instead of CACE. They corroborate
  and add nothing a reader cannot get from the CACE runs.
- **The W<sub>p</sub> = 2.0 µm baseline netlist.** The published DUT netlist is the
  nulled 1.414 µm version. CACE testbenches `.include` the DUT by path, so the run
  directories for the baseline matrix do not themselves record the device width.
  The two netlists differ only in the `w=` field of the PMOS line — `w=2.0u`
  instead of `w=1.414u` — but that reconstruction is stated here rather than
  committed as if it had been captured. This is a reproducibility gap in the
  baseline matrix and is recorded as one.
- Everything not about the design.

## Licence

Apache 2.0, as with the rest of this repository.
