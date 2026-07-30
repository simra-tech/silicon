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

## The gain does not hold over temperature

The section above closed by recording that 20.95 dB against a 20 dB floor left **0.95 dB of margin that had
not been tested** against corner, mismatch or temperature. It has now been tested against two of the three, and
**the margin is not there.** Loaded with the generator's 1059 Ω, at V_CC = 2.5 V ±5% over −40 … +125 °C:

| corner | V_CC | gain | f_-3dB |
| --- | ---: | ---: | ---: |
| cold, −40 °C | 2.625 V | 22.95 dB | 5.060 GHz |
| nominal, +27 °C | 2.500 V | 20.95 dB | 5.258 GHz |
| **hot, +125 °C** | 2.375 V | **18.12 dB** | 5.542 GHz |

**18.12 dB is 1.88 dB below the 20 dB floor.** The specification window is not met at the hot corner.

**And re-centring cannot fix it.** The spread is **4.83 dB** across a window that is **3 dB wide**, so no choice
of nominal gain fits inside it. Either the window widens or the gain has to stop moving with temperature.

**With process corners added it is 6.92 dB and it fails at both ends** — see *Process corners: 6.92 dB* below.
The 4.83 dB figure was measured with the process libraries held at typical and was published as a lower bound;
this is what the bound was hiding.

Bandwidth, by contrast, is well behaved: 5.06 → 5.54 GHz, under 9.5% across the range, because the interface pole
is set by 1059 Ω and ~28.6 fF and neither moves much with temperature.

### Where the 2.83 dB goes, and why that makes the fix determinate

The corners bundle supply and temperature. Separating them, one variable at a time:

| condition | gain | attributable to |
| --- | ---: | --- |
| 27 °C, 2.375 V | 20.46 dB | **supply alone: 0.50 dB** |
| 125 °C, 2.500 V | 18.63 dB | **temperature alone: 2.33 dB** |

0.50 + 2.33 = 2.83 dB, the full hot-corner drop, so the two are independent. **Temperature is 82% of it.**

Gain per stage goes as `R_C / (r_e + R_E + re_model)`. Measuring the per-side collector current directly, it is
0.8933 mA at 27 °C and 0.9243 mA at 125 °C — a rise of only **3.5%**. But `r_e = V_T / I_E`, and V_T rises 33%
across that range, so r_e goes **28.9 Ω → 37.1 Ω, up 28%**. In a denominator of 28.9 + 15 + 14.26, r_e is the
single largest term at **50%**. That is 1.17 dB per stage, and there are two cascaded stages: **2.34 dB
predicted against 2.33 dB measured.**

So the mechanism is fully attributed, and the consequence is specific: **the emitter degeneration, at 15 Ω, is
weaker than the transistor's own intrinsic emitter resistance at 29 Ω.** The gain is set mostly by a quantity
proportional to absolute temperature. That is not a marginal sizing choice; it is the reason the block misses.

**The fix that follows.** Make the tail current proportional to absolute temperature. If I_E ∝ T then
`r_e = V_T / I_E` is constant by construction — at 398 K the tail would carry 1.185 mA rather than 0.924 mA,
r_e stays at 28.9 Ω, and the gain goes flat to within **0.03 dB**. A PTAT reference costs no headroom. The
alternative, raising R_E until it dominates r_e, flattens the gain too but sells gain that then has to be bought
back with a larger R_C, and R_C is what sets the output headroom.

**Recorded as a failure rather than as a to-do**, because an unmet specification and an untested one look
identical in a summary table and are different facts about a chip. Decks and logs for every number above are in
[`rebuild-2p5v/`](rebuild-2p5v/).

## Process corners: 6.92 dB, and it misses at both ends

Adding the process corners — `hbt_bcs`/`res_bcs`/`cap_bcs` and `hbt_wcs`/`res_wcs`/`cap_wcs`, where
`rsh_rppd` runs 234 / 260 / 286 Ω/sq — against the same 1059 Ω load:

| corner | process | T, V_CC | gain |
| --- | --- | --- | ---: |
| **cold, best-case** | bcs | −40 °C, 2.625 V | **24.11 dB** — 1.11 dB **above** the 23 dB ceiling |
| cold, worst-case | wcs | −40 °C, 2.625 V | 22.03 dB |
| nominal | typ | +27 °C, 2.500 V | 20.95 dB |
| hot, best-case | bcs | +125 °C, 2.375 V | 19.07 dB |
| **hot, worst-case** | wcs | +125 °C, 2.375 V | **17.19 dB** — 2.81 dB **below** the 20 dB floor |

**Envelope 17.19 … 24.11 dB: a 6.92 dB spread across a 3 dB window, missing at both ends.**

> **The sizing made a round trip, and the table is current.** These numbers were measured with the collector
> loads at w = 1.0 µm, l = 0.7115 µm (255 Ω). Twelve minutes later the schematic was changed to l = 0.923 µm,
> and about twenty minutes after that it was changed back. A fresh export at that point reproduced the table
> exactly — 17.1854 / 20.9532 / 24.1136 dB — so these are measurements of a real netlist and not of an
> assumption.
>
> **The schematic continues to move, and this table is not re-quoted for every revision.** It is measured with
> `RBIAS` at l = 2.808 µm; a later revision at 2.872 µm gives 17.05 / 20.83 / 24.01 dB, which is 0.12 dB lower
> across the board and changes the envelope from 6.92 dB to 6.96. Revisions of that size will keep happening
> while the bias reference is being designed, and chasing each one would make this page a changelog. **What is
> stable, and what the page is asserting, is the shape: an envelope of roughly 7 dB against a 3 dB window,
> missing at both ends, from a mechanism attributed to r_e = V_T/I_E.** The exact figures are labelled with the
> sizing that produced them so a reader can tell which netlist they belong to.
>
> **Superseded again, and the block is mid-repair.** A PTAT bias attempt has since been added — four new devices,
> `QPTAT`/`RPTAT` per stage — and the schematic no longer matches this table. Two things are wrong with it as
> drawn, both measured: the tail current rises only **1.9%** from −40 °C to +125 °C where PTAT requires 32.7%,
> because both reference legs are diode-connected onto one node with nothing forcing their current ratio; and
> `Q3` has its **collector, emitter and substrate on the same net**, which collapses the differential gain to
> −2.5 dB at typical. So the envelope is not being requoted against a broken circuit — this table remains the
> last measurement of a working amplifier, and it is labelled as describing the l = 0.7115 µm fixed-mirror
> design rather than what is currently in the file.
>
> **The excursion is worth keeping as a result.** At l = 0.923 µm the same three corners gave
> **18.14 / 21.12 / 23.42 dB**: a 5.28 dB spread rather than 6.92. The load increase did not shift the envelope
> uniformly — the bottom rose 0.95 dB and **the top fell 0.69 dB** — which a pure re-centring cannot do. The
> likely cause is collector headroom at cold/best-case, where the drop across 307 Ω at that corner's higher
> current is the largest in the PVT space, but that is unconfirmed. It matters because **a spread that narrows
> because the top end is compressing is not a spread that narrows because the gain is stable**, and the two are
> indistinguishable in a gain table. Recorded so the 1.64 dB is not banked before the mechanism is known.

The diagonal is the true envelope, which is worth stating because it is not obvious: the crossed corners
(cold+wcs, hot+bcs) both land *inside* the diagonal pair. The HBT corner dominates the resistor corner —
`res_bcs` lowers R_C, which alone would lower gain, but `hbt_bcs` raises it by more. So cold+bcs is the
maximum and hot+wcs the minimum, and two corners suffice to bound this block.

### The PTAT fix is not implemented

The tail is still the fixed-resistor mirror. An attempt to emulate a PTAT tail by overriding the bias resistor
per corner from inside the simulator's control block did not take effect — the committed log records
`Error: no such device or model name xamp.xrbias1.r1` twice for each of the two altered corners, because the
`rppd` subcircuit contains exactly one element, `NR1`, and no `r1`. Every number in the table above therefore
uses the nominal 791.5 Ω bias resistor.

**That is the right outcome for the wrong reason, and both halves matter.** Overriding a resistance to a
different value at each corner is not a PTAT tail even when the device name is correct — it sets the answer once
per corner and would report a flat gain that means nothing. A PTAT reference is a circuit: a ΔV_be across a
resistor, carrying its own process spread and its own residual temperature coefficient, none of which appears in
numbers produced by an `alter`. **The fix in the section above remains a recommendation, not a result.**

### Unexamined: 430 rated-voltage warnings

The corner log carries **430** instances of `V(i2,c) voltage is greater than specified by vmax`, spread across
**every** `rppd` in the design — collector loads, degeneration, bias resistors and the base divider. What `vmax`
is for `res_rppd`, and whether these indicate real overstress or an artefact of the model's internal thermal
network, has not been established. Recorded because 430 warnings in one committed log is not a thing to leave
unread, and because the answer could change the sizing before any geometry is drawn.

## Not run

| Check | State |
| --- | --- |
| Temperature and supply on the rebuilt amplifier | **Run, and the gain specification is not met** — see *The gain does not hold over temperature* below. |
| Process corners | **Not run.** All runs load `hbt_typ` / `res_typ` / `cap_typ` and never vary them, so the 4.83 dB spread below is a **lower bound**. |
| Mismatch | **Not run.** No Monte Carlo on the rebuilt schematic. |
| Layout, extraction, post-layout bandwidth | **Not run.** No layout exists for this block. |
| Linearity, compression, supply rejection | **Not run.** |
| Silicon measurement | **Not done.** |
