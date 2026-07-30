# P1_NOISE_GEN — physical layout

The first physical layout in this project. Geometry for the entropy source in the
IHP SG13G2 open PDK: two `npn13G2` SiGe HBTs, two `rppd` 1 kΩ collector loads, and a
`ptap1` substrate tie, in a 42 × 57 µm cell.

**It is DRC-clean on every geometry rule and it matches its schematic.** Both verdicts
below come from the PDK's own tools, and both are reproducible from the files here.

## Verdicts, as the tools reported them

| Check | Deck | Result |
| --- | --- | --- |
| DRC — FEOL & BEOL geometry | `libs.tech/klayout/tech/drc/ihp-sg13g2.drc`, KLayout 0.30.9 | **0 errors** |
| DRC — forbidden hand-drawn layers | same | **0 errors** |
| DRC — minimum global density | same | **9 violations, waived at block level** — see below |
| LVS | `libs.tech/klayout/tech/lvs/sg13g2.lvs` | **PASS (netlists match)** |

The LVS reference is generated from `../p1_noise_gen.sch` by xschem, not written by
hand. Extraction and reference agree terminal for terminal:

    reference                                    extraction
    Q1 RAW_NOISE_N VB1 IE sub! npn13G2           Q$1 RAW_NOISE_N VB1 IE $1 npn13G2
    Q2 RAW_NOISE_P VB2 IE sub! npn13G2           Q$2 RAW_NOISE_P VB2 IE $1 npn13G2
    R1 RAW_NOISE_N VCC sub! rppd w=1u l=3.85u    R$3 RAW_NOISE_N VCC $1 rppd w=1u l=3.85u
    R2 RAW_NOISE_P VCC sub! rppd w=1u l=3.85u    R$4 RAW_NOISE_P VCC $1 rppd w=1u l=3.85u
    R5 VSS sub! ptap1 A=4p P=8u                  R$5 VSS $1 ptap1 A=4p P=8u

Seven ports, five devices, both sides.

### Why the nine density violations are waived rather than fixed

All nine are **minimum *global* density** rules — `AFil.g` (Activ ≥ 35%), `GFil.g`
(GatPoly ≥ 15%), `M1.j`–`M5.j` (Metal1–5 ≥ 35%), `TM1.c` (TopMetal1 ≥ 25%), `TM2.c` —
and each is computed over `chip_bbox`. Running them on a 42 × 57 µm block evaluates a
fragment as though it were the whole chip, and no block that size can reach 35% metal
density by any means.

**They are also the wrong thing to fix locally.** Satisfying a metal density minimum
means adding dummy fill, and dummy fill inside a shot-noise source adds parasitic
capacitance and coupling immediately beside the thing whose noise is the product. That
is the opposite of what this block needs. Density and fill are assembly-level concerns
and belong at top level, against a real chip boundary.

## What is deliberately not claimed

- **No PEX.** Parasitics have not been extracted, so none of the behavioural results
  elsewhere in this repository have been re-simulated against layout parasitics. Every
  number in `../../offset-loop/` still rests on schematic values.
- **No top-level assembly.** This is one block of five. Nothing has been placed
  relative to anything else.
- **Density not evaluated.** Waived here, unevaluated anywhere.
- **Not tapeout-ready, and that is not a status a tool emits.** A clean DRC and LVS with
  extraction is a necessary condition for a tapeout candidate, not a sufficient one.
- **No silicon.** Nothing fabricated, nothing measured on a wafer.

## How this went, because the record is more useful than the result

Nine attempts, and the failures were more instructive than the pass. In order:

1. **The first layout contained no devices.** 1,930 bytes, one flat cell, 29 hand-drawn
   rectangles, zero PCell instances, and 0.0005 mm² against a 0.03 mm² budget. DRC
   rejected it on `forbidden.baspoly`, `forbidden.empoly`, `forbidden.deepco` — rules
   that exist precisely to stop hand-drawn HBT geometry. The PCell library had failed to
   import **with exit code 0**, so the generator carried on and drew the layers itself.
2. **The load resistor was wrong three times**: 112 Ω (`rsil`, 16 squares at 7 Ω/sq),
   then 3.16 kΩ (`rhigh` at its default, because the generator passed a lowercase `r`
   where the parameter is `R` — silently discarded), then 130 Ω (`rppd` with the length
   left at `Lmin`). The `R` parameter field read 1000, then 3160, then 397 across those
   revisions: it is a stored request, not a measurement. What finally worked is
   `verify_rppd_geometry.py` here — compute `Rspec × l / w` from the drawn geometry and
   fail hard on any deviation over 10 Ω.
3. **The reference netlist was hand-written for several attempts**, and was twice edited
   to agree with the layout — once while the layout carried a 7.7× undersized resistor.
   A reference maintained by hand cannot disagree with the layout, because whenever it
   does, the hand fixes the reference. Generating it from the schematic is what made the
   comparison mean anything.
4. **The schematic did not netlist.** Five of six transistor terminals landed on unnamed
   nets, because the collector and base wires had been drawn to the symbol's origin
   column rather than to its pin columns, 20 units off.
5. **Then a run of shorts**, each introduced by the fix for the last: base to emitter;
   one substrate onto the base bias; the tail node swallowed by a new ground wire whose
   segment contained the tail wire's endpoint; and three, then four, labels colliding
   onto one net (`IE|VB1|VB2|VSS` — KLayout naming a short for you).
6. **The bias nets did not exist for six attempts.** Tabulating every extraction showed
   the base had never once been on a net of its own — so it was a routing gap, not the
   labelling error everyone was treating it as. A label cannot name a net that does not
   exist.
7. **The device cell contacts two of its four terminals.** Three Metal1 shapes, two
   contacts, nothing under the centre pad. The base has to be contacted from the top
   level; the cell will not do it for you.

The check that ended up catching everything has three clauses, and each was added after
an error walked past the previous version:

1. every terminal in the extraction names the net the reference names for it;
2. every device in the extraction corresponds to a device in the reference *(added after
   two resistors merged into one 7.7 µm device and the supply went missing)*;
3. no net carries more than one label *(added after `IE|VB1|VB2`, which satisfies both
   clauses above)*.

One further note, because it nearly slipped through. The `ptap1` instance in the
schematic briefly carried a hand-written `format=` override hardcoding `A=4.00p
P=8.00u` as literals, where the PDK symbol computes both from `w` and `l`. LVS passed
with it in place — but that pass **asserted** the tap's size instead of testing it, so a
resized tap would have kept matching. The override was removed, the reference
regenerated, and the pass reproduced with both values derived. That is the pass recorded
above.

## Contents

```
p1_noise_gen.gds                     the layout, 42 × 57 µm
generate_p1_noise_gen_layout.py      deterministic generator: PCells, wiring, labels
verify_rppd_geometry.py              computes R from drawn geometry, fails over 10 Ω
p1_noise_gen.cdl                     LVS reference, exported from ../p1_noise_gen.sch
p1_noise_gen_extracted.cir           the extracted netlist LVS compared against it
lvs_run.log                          the LVS run reporting PASS
drc/drc_run_*.log                    the DRC run and its violated-rule list
drc/*_full.lyrdb                     the 9 density violations, itemised
```

Reproduce with the PDK's `run_drc.py` and `run_lvs.py` after setting `$PDK_ROOT` to an
IHP SG13G2 installation. The generator needs `KLAYOUT_PATH` pointing at
`libs.tech/klayout` so `SG13_dev` PCells resolve — if that is missing the import fails
with exit code 0, which is how attempt 1 produced a layout with no devices in it.
