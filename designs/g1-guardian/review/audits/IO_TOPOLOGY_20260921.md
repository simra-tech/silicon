# Stock IO topology and schematic-parameter diagnostics

All comparisons below use the installed unmodified PDK deck. They fail;
none is an IO signoff pass. Baseline and modified reference/GDS hashes,
commands, logs, extracted netlists and cross-reference databases are retained.
No extracted netlist is substituted for a schematic reference.

## Input-pad candidate versus baseline

`pad-outward-dummy-clean-lvs-20260921/` compares the baseline delivered input
pad, the clean candidate with stock reference, and the candidate with an
independently specified additional all-VDD W4.65/L0.45 PMOS in the reference.
All three report **failed**, with DCNDiode, DCPDiode and SecondaryProtection
unmatched; LevelDown and IOPadIn parents are skipped. The resulting candidate
netlist differs from baseline only by two top-level tap instance identifiers.
This three-child result is for IOPadIn; the earlier five-child result in
`io-lvs-deep-20260921` was for IOPadAnalog, which additionally includes clamps.

A follow-up uses the stock `--no_simplify` option, with all three comparisons
retained in `io-unsimplified-20260921/`. They still fail at the same three
children, and neither the original nor added electrically shorted all-VDD
MOS survives in the output netlist. Inspection identifies an unconditional
`target_netlist.purge_devices`/`purge` in `rfmos_model_mapping.lvs` before the
optional simplify stage. Thus disabling simplify does not provide a count of
this dummy. The physical gate area/dimensions and G/S/D/VDD-tap connectivity
are independently checked by the geometry candidate generator; these probes
do not substitute for a successful full IO comparison.

## Independent tap geometry inconsistency

`audit_tap_geometry.py` directly computes raw stock Activ/pSD polygon area and
perimeter, excluding nwell, gate and resistor regions, for five simple failing
children. It does not read extracted netlists. The stock CDL perimeter equals
`4*sqrt(CDL area)` in every case, to the printed rounding precision: it
represents an equivalent square rather than the physical tap/guard-ring
perimeter. Actual polygon areas are close (within 0.061%), but perimeters differ
substantially. The stock tap device class compares both area and perimeter.

| Stock cell | CDL A (µm²) | Raw A (µm²) | CDL P (µm) | Raw P (µm) |
|---|---:|---:|---:|---:|
| SecondaryProtection | 9.030 | 9.0304 | 12.02 | 53.12 |
| Clamp_N20N0D | 55.801 | 55.7736 | 29.88 | 328.08 |
| Clamp_P20N0D | 66.994 | 67.0344 | 32.74 | 394.32 |
| DCNDiode | 141.253 | 141.2964 | 47.54 | 221.76 |
| DCPDiode | 33.524 | 33.5104 | 23.16 | 197.12 |

Evidence: `io-tap-geometry-20260921.json`. The direct geometry values reproduce
the prior stock extraction values. This identifies a concrete parameter
inconsistency; it does not justify disabling tap extraction or rewriting a
schematic from an extracted netlist. A future local derived-cell reference
must state the intended substrate/tap circuit and independently reconcile
these parameters, including the smaller area differences.

## Flat topology and global-substrate probes

The stock CDL uses `sub!` in children but does not declare `.GLOBAL sub!`.
In a flat comparison, the reader consequently retains separate schematic
`I3.SUB!`, `I4.SUB!`, `I5.SUB!` nodes while the layout has the physical
substrate connection. A diagnostic reference adds only `.GLOBAL sub!`;
all device statements and parameters remain unchanged. This is a reference
view hypothesis, not a new virtual layout connection. The third trial also
uses the earlier PolyRes-only GDS annotation over the existing resistor body.

All three use stock flat mode and device combination; they do not enable
implicit connections, disable taps, ignore top pins or alter rule decks.

| Trial | Result | Unmatched nets | Unmatched devices | Unmatched pins |
|---|---|---:|---:|---:|
| Stock GDS/CDL, flat | failed | 9 | 6 | 0 |
| Stock GDS, `.GLOBAL sub!` CDL | failed | 7 | 5 | 0 |
| PolyRes annotation + global CDL | failed | 5 | 5 | 0 |

Evidence: `io-topology-20260921/`, script `io_topology_probe.py`. The final
mismatch still includes substrate/taps and separate IOVDD physical regions
that are labelled alike within the standalone cell. Those rails may be joined
through abutment in the complete ring; no standalone implicit merge is
adopted here. Core and full assembled IO-inclusive candidate LVS are separate
runs in `pad-outward-dummy-clean-lvs-20260921`. Core LVS **passed**, explicit
stock comparison match (1153.79 s wrapper wall time). Full IO-inclusive LVS completed **failed** in the normalized assembled view;
its final result is below. The clean candidate's DRC/antenna/density passes
cannot override these circuit mismatches.

## Recognition annotation DRC follow-up

`io_annotation_drc.py` compares the untouched standalone AnalogIO cell and
its previously retained PolyRes-only recognition annotation using the stock
hard and recommended deck. **Both passed, zero markers** (12.41 s baseline,
12.51 s annotation). Exact hashes, commands and reports are preserved in
`io-annotation-drc-20260921/`. Only layer 128/0 differs, as independently
proved in the original recognition diagnostic; all original mask geometry
is unchanged. This closes the previously unrun diagnostic DRC check, not the
five remaining LVS child failures or process acceptance of the marking layer.
The annotation has not been added to the delivered or clean full-chip candidate.

## Boundary for a local repair or external PDK disposition

The missing PolyRes recognition marker is independently localized to the
existing unsilicided poly body and agrees with the existing schematic's
1 µm × 2 µm resistor intent. A design-local cloned SecondaryProtection cell
with this marker is a reproducible candidate: it extracts the expected series
resistor and passes the unchanged stock hard/recommended DRC. Production
adoption still requires acceptance of this recognition-layer use and complete
IO-inclusive LVS; the current clean full-chip candidate contains no such
annotation.

The tap parameter discrepancies have a different disposition. Five stock
reference perimeters encode an equivalent square while the physical shapes
are guard rings. Changing the mask to force a square would change guard-ring
and ESD intent. Changing reference parameters merely to match extraction would
not establish the intended circuit. A local reference repair therefore needs
an independently documented substrate/guard-ring model and parameter meaning,
including the small area differences; that intent is not established here.
Until reconciled, these are explicit stock-PDK/library disposition blockers,
not waived checks. No upstream message or foundry contact has been sent.

The proposed all-VDD dummy is separately specified in the design-local CDL
from its intended W/L and four-terminal connectivity. The stock extractor
purges these shorted devices even with `--no_simplify`; independent physical
area/connectivity evidence is retained, and no extracted netlist is used as
golden. Electrical/ESD/power-sequence qualification remains outstanding.


## Completed exact-candidate full IO comparison

`p01-full-io-normalized-20260921` contains a completed strict stock deep LVS
comparison of the exact clean candidate, with geometrically identical standard
cell aliases folded/renamed and `.GLOBAL sub!` declared in a diagnostic
reference. The independent dummy statement remains present. Full-chip merged
polygon XOR is zero after normalization; unchanged rule decks and top-port
checking remain enabled. **Failed**, 1591.44 s wrapper wall time; the stock
wrapper exits zero despite the explicit comparison failure, so report status
is determined from the comparison outcome.

- **52 matched** circuit pairs, including every design macro and the digital
  macro/stdcells.
- **14 unmatched IO children**: Clamp_N15N15D, N20N0D, N2N2D, N43N43D4R,
  N8N8D; Clamp_P15N15D, P20N0D, P2N2D, P8N8D; DCNDiode, DCPDiode,
  LevelUpInv, RCClampInverter and SecondaryProtection (all `sg13g2_` names).
- **Four missing-reference circuits**: Corner, Filler2000, Filler400 and
  Filler4000. These contain physical substrate-tap devices and must not be
  treated as empty filler. Their intended reference view is absent from the
  stock CDL used here.
- **11 skipped parents**, including the chip top and input-pad cell. The added
  dummy cannot be reported LVS-qualified from a skipped parent comparison;
  the unconditional stock purge also removes shorted MOS devices.

`baseline_comparison.json` compares the historical untouched 1200 µm ring:
the same 14 child names failed there. Corner/filler missing-reference failures
also existed there, with Filler200 instead of Filler4000 in that ring size.
All 18 currently failing child/corner/filler cells retain identical merged
polygon geometry to the installed stock library across the union of layers.
This localizes failures to unchanged stock-cell/reference issues; it does
not prove full assembled connectivity because the top comparison is skipped.
The LVSDB is preserved compressed, with raw and compressed SHA256 values;
decompression identity independently passed. Raw database remains in scratch.

The five-child standalone AnalogIO result was a smaller hierarchy, not the
expected number of failures for the full ring. No new dummy-specific mismatch
was established, and no conclusion of dummy equivalence follows. Production
adoption remains blocked by this full IO failure, the disposition requirements
above, and outstanding electrical/ESD/power-sequence checks.

## Independent tap electrical-reference semantics — 2026-09-22

A new read-only audit pins the public PCell callback, technology constants,
stock SPICE/CDL, raw-geometry audit and electrical model in
[io-tap-reference-semantics-20260922-r1/summary.json](io-tap-reference-semantics-20260922-r1/summary.json).
The unchanged `CbTapCalc` defines `R = 1 / (A/raspec + P/rpspec)`;
`ptap1_raspec=980 ohm*um²`, `ptap1_rpspec=980 ohm*um`. The ngspice `ptap1`
model uses suppliedR directly; its source says schematic capture calculatesR.
Thus area and perimeter carry electrical meaning in the public PCell model.

| Cell | Stock SPICE R | R from stock CDL A/P | Conditional R from raw guard geometry |
|---|---:|---:|---:|
| SecondaryProtection | 46.556 ohm | 46.55582 ohm | 15.76820 ohm |
| Clamp_N20N0D | 11.438 ohm | 11.43778 ohm | 2.55306 ohm |
| Clamp_P20N0D | 9.826 ohm | 9.82614 ohm | 2.12418 ohm |
| DCNDiode | 5.191 ohm | 5.19087 ohm | 2.69931 ohm |
| DCPDiode | 17.289 ohm | 17.28883 ohm | 4.24922 ohm |

The CDL equivalent-square perimeter and stock SPICE resistance agree within
0.003%. Applying the same formula to raw guard geometry gives1.92–4.63times
lowerR, but that last column is an inference: the rectangular PCell's model
validity for arbitrary guard-ring geometry has not been established. It is
not a validated replacement resistance.

This strengthens the disposition boundary. The reference perimeter is not
merely harmless comparison metadata: rewriting it alone would create a
mismatch between reference geometry and its existing electrical-model intent.
Neither a reference rewrite nor a physical guard-ring change is justified by
this audit. Independent guard-ring parameter/model intent and library
reconciliation remain required. No PDK/model/rule changes, production adoption,
new LVS rerun, or external message was performed for this read-only check.

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/audit_tap_reference_semantics.py --output build/scratch/io-tap-reference-repeat
```
