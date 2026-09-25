# Schematic readability pass and chip-of-record sheets (2026-09-25)

The tracked xschem schematics of the G1 blocks were generated as label-per-pin device lists: no wires, every
pin carrying a `lab_pin`, symbols with all pins on one edge. This pass redraws them **from their
generators**, without changing any netlist, and adds sheets for the chip-of-record variants that had no
schematic (BGR586, SENSE comp45 + R100, TRIP regenpair4 + NF4, OSC R0.95) and a chip-level interconnect
sheet. Every sheet was netlisted with xschem in the pinned container and compared with its reference
netlist. No simulation, DRC, LVS or PEX was run (see "Not run").

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| xschem | 3.4.8RC (`xschem -v`: "XSCHEM V3.4.8RC", copyright 1998-2026) | in the container |
| Python / networkx | container `python3`, networkx 3.6.1 | recorded in every `proof/*/*.equiv.json` |
| SVG to PNG | rsvg-convert 2.42.7 (host) | `rsvg-convert --version` |
| Chip of record | `g1_chip_top_1414_r2.gds` `9049e87b…`, canonical CDL `g1_chip_top_1414_r2.cdl` `41d47877…`; block map `../../blocks/g1_padring/reports/signoff-1414-20260924/README.md` | design README |

## Method

1. **Generators, not outputs.** All tracked block sheets are generator outputs (`gen_*.py`); each generator
   was run first and reproduced its tracked `.sch`/`.sym` byte for byte. The generators now draw through
   `flow/schematic/xsch_readable.py` (new, replaces the five `xsch.py` copies). Device attribute strings,
   instance order and port order are unchanged, so xschem writes the same netlist.
2. **Geometry check before writing.** `xsch_readable.Sheet.check()` rebuilds the connectivity from the
   drawing with xschem's rules (coincident points join; a pin or wire end on a wire joins; crossing wires do
   not; equal label names join) and refuses to write a sheet that shorts two nets. It also gives every
   component a label, so no net is renamed `netN` by xschem. It caught real errors during the work (for example a
   latch wire through a supply stub, a gate column through another gate).
3. **Netlist and compare.** `run_proof.sh` netlists every sheet in the container (`xschem -n -q -x`, the
   PDK `xschemrc`, the same `sed` as the blocks' `netlist.sh`) into a results directory and runs
   `check_equivalence.py`:
   - *text*: netlists compared byte for byte after removing the `** sch_path:` / `** sym_path:` comment lines;
   - *named*: both netlists flattened from the top cell; every primitive compared by instance path, model,
     ordered terminal nets and sorted parameters;
   - *multiset*: the same records without instance names (for sheets drawn with xschem instance arrays);
   - *connectivity*: bipartite device/net graphs (device label = model + parameters, net label = port name
     or "internal", edge label = terminal position, the two `rppd`/`rhigh` ends interchangeable) compared
     by networkx graph isomorphism, independent of all names.
   The chip sheet uses `compare_chip_subset.py` (name, cell and ordered nets of every drawn top-level
   instance against the CDL top subcircuit; port lists equal).
4. **Before.** The committed sheets (unchanged between `270f24b2` and `3d964bf0`) were netlisted the same way.
   Their netlists equal the tracked `sim/netlist/*.spice` (and `xschem/g1_t2f.spice`) apart from the path
   comment lines, so the tracked files are the references below.

## Inventory

| Sheets (tracked) | Origin | On the chip of record? | This pass |
|---|---|---|---|
| `g1_gate/schematic/*.sch` (7) | `gen_gate.py` | yes (GATE baseline) | redrawn |
| `g1_ctrl/ls/xschem/g1_ls_up.sch` | `gen_ls.py` | yes (3 level shifters) | redrawn |
| `g1_osc/schematic/*.sch` (7) | `gen_osc.py` | R0.95 | redrawn; default now R0.95 |
| `g1_sense/schematic/g1_sense.sch`, `g1_ota.sch` | `gen_sense.py` | revision B; chip is comp45 + R100 | redrawn; chip sheets added |
| `g1_trip/schematic/*.sch` (8) | `gen_trip.py` | 12/0.34 µm comparators; chip is regenpair4 + NF4 | redrawn; chip sheets now in `schematic/` |
| `g1_t2f/xschem/g1_t2f.sch` | `gen_g1_t2f.py` (+ `g1_bgr/xschem/schgen.py`) | yes (baseline, not rev1) | redrawn |
| `g1_t2f/xschem/g1_ref_sensor.sch` | hand-written hierarchy check | not a chip cell | unchanged; still netlists identically |
| `g1_bgr/xschem/g1_bgr.sch` | `gen_g1_bgr.py` | **no** (Sep-19 single-unit parent) | unchanged; BGR586 sheets added |
| `g1_t2f/rev1/xschem/*` | `rev1/xschem/gen_g1_t2f.py` | no | unchanged |
| `g1_bgr/source/…`, `g1_sense/source/…` (6) | third-party, hand-drawn | no (design sources) | unchanged |

## Results (final run, `proof/summary.txt`)

Reference SHA-256 prefixes are of the tracked files. "Before = after" is the text comparison of the old and
new sheet netlists (path comments removed; SHA-256 prefixes in `proof/before_after.json`).

| Sheet | Reference netlist | Devices | Before = after | Result |
|---|---|---|---|---|
| GATE `g1_gate`, `g1_lvlup`, `g1_lvldn` | `g1_gate/sim/netlist/g1_gate.spice` `846a55e0`, `g1_lvlup.spice` `71af3cd8`, `g1_lvldn.spice` `d253d0a6` | 78, 8, 4 | yes | identical |
| GATE leaves `g1_lv_inv`, `g1_lv_nand2`, `g1_hv_inv`, `g1_hv_nor2` | subcircuits of `g1_gate.spice` | 2, 4, 2, 4 | yes | identical |
| LS `g1_ls_up` | `g1_ctrl/ls/sim/netlist/g1_ls_up.spice` `5567c807` | 8 | yes | identical |
| OSC leaves (inv, nor2, nor3, nand2, cbank), `g1_osc_cmp` | `g1_osc/sim/netlist/g1_osc.spice` `43a16205`, `g1_osc_cmp.spice` `ad2ce6b3` | 2–9 | yes | identical |
| OSC `g1_osc`, default R0.95 | `g1_osc.spice` `43a16205` (117 µm) | 68 | no, by design | **differs in exactly XRA, XRB: l 117u → 111.15u** (= chip CDL `RRA`/`RRB`); all else identical |
| OSC `g1_osc`, `G1_OSC_VARIANT=baseline` | same | 68 | — | identical (text identical) |
| SENSE `g1_ota`, `g1_sense` (revision B) | `g1_sense/sim/netlist/g1_ota.spice` `7f68bf0f`, `g1_sense.spice` `8880157b` | 21, 159 | yes | identical |
| SENSE comp45 + R100 `g1_sense` (new, `g1_sense/xschem/comp45_r100/`) | `…/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice` `aeee4d41` (bulk source `bb933fda`, differs only in the path comment) | 159 | new | identical (named, connectivity) |
| TRIP chip `g1_trip` (new content of `g1_trip/schematic/`) | chip deck `g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice` `f5f0a90a` | 2305 | new | identical (named: every instance, terminal and parameter, incl. NF4 as/ad/ps/pd and `rppd` bodies on `vss`) |
| TRIP historical (`g1_trip/schematic/historical_12u034/`, 8 cells) | `g1_trip/sim/netlist/g1_trip.spice` `6f265319`, `g1_cmp` `a31a1f15`, `g1_cond` `ef8ed581`, `g1_dac8` `9f967559`, `g1_tlvlup` `5eac9e76` | 2–2305 | yes | identical |
| T2F `g1_t2f` | `g1_t2f/xschem/g1_t2f.spice` `8011b761` | 83 | yes | identical; `g1_ref_sensor` (121 devices) text identical to before |
| BGR586 `g1_bgr` (new, `g1_bgr/xschem/bgr586/`) | `g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/…hv06.spice` `586ffb58` | 1036 + 329 Cext | new | equivalent: multiset identical (every device with its nets and parameters), graph isomorphic; instance names differ by construction (arrays) |
| Chip interconnect `g1_chip_top` (new, `g1_top/xschem/chip_interconnect/`) | `g1_padring/netlist/g1_chip_top_1414_r2.cdl` `41d47877` (and r1 `af5a4dbd`) | 61 instances | new | identical for the drawn subset against r2 and r1; not drawn: 4645 decap_8, 17 decap_4, 38 fill_2, 21 fill_1, 6 antennanp, 4 IO corners, 112 IO fillers |

## What changed on the sheets

Common to all: signal flow left to right, supply rails on top (vdd/vdda/vdd12) and bottom (vss), wires
instead of per-pin labels inside each functional group, net labels (`lab_wire`) on every inter-group net,
bodies tied to their sources by a wire along the symbol (a small `b:<net>` tag where the body is a rail but
not the source), dashed frames with captions for functional groups, the PDK symbols' size text visible,
and a title block: block, function, chip of record, on-chip variant, "netlist-equivalent to <file> <sha>".
Block symbols have inputs left, outputs right, supplies top/bottom and gate-shaped bodies (inverter, NAND,
NOR, amplifier); the pin order, which fixes the subcircuit call, is unchanged.

- **GATE**: fast-path AND → 4 level-up shifters → 3.3 V set/reset NORs → cross-coupled NOR latch → gate
  enable → 3 level-down shifters; transistor sheets as CMOS stacks; note with the chip-level GATE timing (simulated).
- **LS, OSC, SENSE, TRIP, T2F**: transistor sheets as stacks and mirrors (cross-coupled pairs with one crossing,
  StrongARM core with precharge/dummies/latch groups, folded-cascode OTA with its Sooch bias), resistor strings as
  wired series columns, annotations with VREF, pedestal, gain 20, DAC LSB/threshold formula, clock and frequencies,
  each marked simulated with its record. The 1040-device `g1_dac8` keeps its placement grid and only gains frames
  and a title block (it is drawn as a symbol on the TRIP sheet).
- **OSC R0.95**: `gen_osc.py` draws RA/RB 1u/111.15u by default (`G1_OSC_VARIANT=baseline` restores 117u).
- **SENSE comp45 + R100**: generated by `g1_sense/xschem/comp45_r100/gen_comp45_r100.py` from the refactored
  `gen_sense.py` (functions `ota_sheet`, `sense_sheet`): `g1_ota_main_candidate` (M1/M2 384u, M3/M4 320u/4u,
  M14/M11/M15/M12 384u/4u, RZ 1u/100u, CC 45u × 23u) as XOTA, `g1_ota` for XBUF/XREF.
- **TRIP chip**: `gen_trip.py` default `G1_TRIP_VARIANT=chip`: soft `g1_cmp` with the NF4 pair (a local symbol
  `g1_nmos_geom.sym` netlists its as/ad/ps/pd), hard `g1_cmp_regenpair4`, `rppd` bodies on `vss` as in the chip deck.
- **BGR586**: `g1_bgr/xschem/bgr586/gen_bgr586.py`: top sheet with the branches of the topology (start-up, cascode
  bias, Q1, Q2, VREF, IPTAT, r4 test, dummies) and unit sub-sheets instantiated as xschem arrays: mirror+cascode
  unit ×24/×24/×24/×4/×1, start-up mirror ×1, NMOS cascode unit ×24 ×2, HBT unit (Q1 ×24, Q1B ×24, Q2 ×192,
  QD1/QD2 ×24, Qref ×4, dummies ×9), resistor units (R1 ×24; RB 10 series × 24; RX 4 series × 24; R2 6 series × 4;
  RDET 15 series × 1), and `bgr586_cext` holding the candidate's 329 extraction capacitors (values read from the
  candidate file; not design elements). Local primitive symbols `b586_*.sym` netlist the candidate's parameter
  set (MOS as/ad/ps/pd/rfmode, npn we/le/Nx/m, resistor body terminal). Renders in `bgr586/`.
- **Chip interconnect**: every macro, level shifter, tie cell, pad cell and bond pad of `g1_chip_top` as a black
  box with the CDL instance names and nets (west inputs, east outputs, north supplies, south test pads).

Renders: `renders/<block>/<cell>.svg` for every redrawn or new sheet (PNG as well for the top sheets;
`g1_dac8` as PNG only), `bgr586/*.svg` and `bgr586/g1_bgr.png`. The render uses a render-only copy of the PDK
`cap_cmim.sym` without its `tcleval(...)` capacitance text, which hangs xschem 3.4.8RC under `xvfb-run` in this
container; netlisting always uses the PDK symbol.

## Not run / not applicable

| Item | Status |
|---|---|
| Electrical simulation of any sheet | not run (drawing and netlist-equivalence task) |
| DRC / LVS / PEX | not applicable (no layout changed) |
| Rerun of the blocks' `netlist.sh` into `sim/netlist/` | not run on purpose: tracked simulation netlists are untouched. Note: run now, `g1_osc/schematic/netlist.sh` would write the R0.95 `g1_osc.spice` and `g1_trip/schematic/netlist.sh` the chip-of-record TRIP netlists |
| Redraw of `g1_bgr/xschem/g1_bgr.sch` (Sep-19, not on the chip), `g1_t2f/rev1`, third-party source sheets | not run (not chip cells) |
| Readable redraw of the `g1_dac8` string/tree placement | not run (frames and title only) |
| Chip sheet: fill, decap, antenna, corner, IO-filler cells | not drawn (counted above) |
| Visual review of every render at full size | done for the top sheets of each block; leaf sheets spot-checked |

## Reproduction

```sh
# regenerate (from each directory): gen_gate.py, gen_ls.py, gen_osc.py, gen_sense.py, gen_trip.py
#   (and G1_TRIP_VARIANT=baseline python3 ../gen_trip.py in schematic/historical_12u034), gen_g1_t2f.py,
#   comp45_r100/gen_comp45_r100.py, bgr586/gen_bgr586.py, chip_interconnect/gen_chip_interconnect.py
G1_CPUSET=<cpus> G1_CPUS=2 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=<dir> \
  flow/run.sh sh designs/g1-guardian/review/schematics-readability-20260925/run_proof.sh <dir>
```

`proof/` holds the equivalence JSON of every comparison, `summary.txt` and `before_after.json` of this run.
