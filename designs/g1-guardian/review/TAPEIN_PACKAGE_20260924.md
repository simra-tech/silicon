# G1 tape-in package, IHP SG13G2 open PDK: draft checklist (2026-09-24)

This is a **draft**. It does not approve tape-out. The owner will add IHP's official
submission instructions later. Each item is marked with one of:

- **confirmed:** measured from the file in this repository, or stated in the public
  IHP-Open-PDK documentation at commit `84374023` (`libs.tech/klayout/tech/drc/docs/*.md`,
  `sg13g2.lyp`).
- **assumed:** a project decision or common shuttle practice that the public PDK
  documentation does not state. It must be checked against IHP's instructions.
- **open:** still to be done or answered.

Built against: IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9 and OpenSTA 3.1.0
in `tapeoutbench-eda` sha256:ddeb6957… (`flow/run.sh`). The PDK layer-properties file
`sg13g2.lyp` (sha256 c7595750…) is identical in the container and in the local PDK copy.

## 1. GDS file

| Item | Value | Status |
| --- | --- | --- |
| File | `blocks/g1_padring/layout/g1_chip_top_1414_r2.gds`, 84 500 300 bytes, sha256 `9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c` (**r2, file of record since 2026-09-25**) | confirmed (sha256sum). Written from r1 by `flow/signoff/1414r2/make_r2.py` (no timestamps; two writes byte-identical). Metadata-only: the two seal-ring registration texts on 63/0 corrected (section 3) and three modified stock-named cells renamed (`sg13g2_LevelDown` → `g1_LevelDown_polyres`, `nmos` → `g1_gate_nmos`, `pmos` → `g1_gate_pmos`). Geometric identity to r1: confirmed (per-layer XOR empty on all 73 layers, hierarchy and instance tree identical modulo the renames; `reports/signoff-1414r2-20260925/r2_identity/`) |
| Superseded file (r1) | `blocks/g1_padring/layout/g1_chip_top_1414.gds`, 84 500 250 bytes, sha256 `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | kept unchanged. Created from the source `candidate.gds` sha256 `60730627…` (kept as `layout/g1_chip_top_1414_src.gds`) by renaming the top cell only (`flow/signoff/1414/rename_top.py`; `reports/signoff-1414-20260924/rename_verify/verify_rename.json`) |
| Top cell | `g1_chip_top`, the only top cell | confirmed (KLayout) |
| Database unit | 0.001 µm (1 nm) | confirmed (KLayout `Layout.dbu`). The DBU IHP requires: assumed 1 nm |
| Die / bounding box | (0, 0) to (1414, 1414) µm, i.e. 1414 × 1414 µm = 1.999396 mm² (EdgeSeal boundary 39/4 is the same box) | confirmed (top bbox). Whether the die size is taken from the bbox or the EdgeSeal outline, and the allowed size and area on the shuttle: assumed |
| Cells | 306 | confirmed |
| Filename, compression, one top cell per submission, GDS version | `g1_chip_top_1414_r2.gds`, uncompressed, GDS version 600 | assumed |
| Size limit of the file | 84.5 MB | assumed acceptable |
| The file is in Git | r1: tracked since commit `10ee4868`. r2: not yet committed (2026-09-25). The sha256 above is the identity of the file. | r1 confirmed; r2 open. How the file is delivered to IHP: open |

## 2. Layer usage (from the GDS)

Script `review/tapein/gds_inventory.py`. Output `review/tapein/gds_inventory_g1_chip_top_1414.json` (r1) and
`review/tapein/gds_inventory_g1_chip_top_1414_r2.json` (r2: identical in every layer count, text count and cell list apart from the renames and the sha256)
(flat counts = direct shapes × flat placements of each cell). Command, repository root:

```
G1_CPUSET=<cpu> G1_CPUS=1 G1_CONTAINER_ENGINE=podman flow/run.sh klayout -b -r designs/g1-guardian/review/tapein/gds_inventory.py \
  -rd gds=designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds \
  -rd lyp=/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp \
  -rd out=designs/g1-guardian/review/tapein/gds_inventory_g1_chip_top_1414.json
```

73 layer/datatype pairs carry shapes. **All 73 are defined in the PDK `sg13g2.lyp`**; no layer
outside the PDK map was found (confirmed).

| Layer | Name | Flat shapes | Flat texts |
| --- | --- | --- | --- |
| 1/0, 1/20, 1/22, 1/23 | Activ drawing / mask / filler / nofill | 68 954 / 308 / 28 594 / 18 | 0 |
| 5/0, 5/2, 5/22, 5/23 | GatPoly drawing / pin / filler / nofill | 58 634 / 1 748 / 30 377 / 18 | 0 |
| 6/0 | Cont | 3 620 229 | 0 |
| 7/0, 7/21 | nSD drawing / block | 60 / 308 | 0 |
| 8/0, 8/2, 8/22, 8/23, 8/25 | Metal1 drawing / pin / filler / nofill / text | 101 569 / 52 242 / 49 997 / 18 / 0 | 42 764 on 8/25 |
| 9/0 | Passiv | 25 | 0 |
| 10/0, 10/2, 10/22, 10/23, 10/25 | Metal2 | 81 248 / 1 094 / 60 684 / 19 / 0 | 493 on 10/25 |
| 14/0 | pSD | 32 248 | 0 |
| 19/0, 29/0, 49/0, 66/0 | Via1 / Via2 / Via3 / Via4 | 92 776 / 112 975 / 59 665 / 62 124 | 0 |
| 26/0, 33/0 | TRANS, EmWind (HBT) | 308 / 308 | 0 |
| 28/0 | SalBlock | 2 041 | 0 |
| 30/0, 30/2, 30/22, 30/23, 30/25 | Metal3 | 42 269 / 1 163 / 32 177 / 27 / 0 | 1 161 on 30/25 |
| 31/0 | NWell | 13 908 | 0 |
| 36/0, 129/0 | MIM, Vmim | 19 / 6 316 | 0 |
| 39/0, 39/4 | EdgeSeal drawing / boundary | 1 / 1 | 0 |
| 40/0 | Substrate | 1 194 | 0 |
| 41/0 | dfpad | 24 | 0 |
| 44/0 | ThickGateOx | 2 077 | 0 |
| 50/0, 50/2, 50/22, 50/23, 50/25 | Metal4 | 9 281 / 1 045 / 32 361 / 22 / 0 | 1 044 on 50/25 |
| 51/0 | HeatTrans | 2 973 | **2 569** |
| 52/0 | HeatRes | 1 627 | **1 532** |
| 63/0 | TEXT | 0 | 3 351 |
| 67/0, 67/2, 67/22, 67/23, 67/25 | Metal5 | 3 864 / 1 032 / 33 156 / 22 / 0 | 1 032 on 67/25 |
| 99/31 | Recog.diode | 140 | 0 |
| 111/0 | EXTBlock | 6 096 | 0 |
| 125/0, 133/0 | TopVia1, TopVia2 | 58 326 / 40 153 | 0 |
| 126/0, 126/2, 126/22, 126/23, 126/25 | TopMetal1 | 1 837 / 1 065 / 5 640 / 26 / 0 | 1 035 on 126/25 |
| **128/0** | **PolyRes.drawing** | **1 693** | 0 |
| 134/0, 134/2, 134/22, 134/23, 134/25 | TopMetal2 | 941 / 787 / 6 942 / 26 / 0 | 801 on 134/25 |
| 160/0 | NoMetFiller | 14 | 0 |
| 189/4 | prBoundary.boundary | 13 290 | 0 |

Flags for review:

- **Text and label layers are present.** The `.text` layers (x/25) carry texts; the `.pin`
  layers (x/2) carry shapes; `TEXT` 63/0 carries 3 351 texts. HeatTrans 51/0 and
  HeatRes 52/0 also carry texts (2 569 and 1 532). These are ordinary PDK layers, but
  where their texts come from was not traced. Whether IHP wants labels, pin layers and prBoundary kept or
  stripped before submission: assumed kept, open.
- **PolyRes 128/0 is present** in 18 cells, 1 693 flat shapes. The stock PDK IO cells
  `sg13g2_Clamp_N20N0D` and `sg13g2_Clamp_P20N0D` carry it (checked against `sg13g2_io.gds`: 1 shape each, same
  as in the chip). It is also on the **design-local IO cell copies**
  `g1_io_rc_polyres_r1(_alias1)` (26 shapes) and `g1_io_secondary_polyres_r1(_alias1)` (1 shape), which do not exist in
  the PDK. It is also on the analog blocks (`g1_bgr__*`, `g1_dac8`, `g1_ota*`, `rppd$2$1`, and
  wrapper cells `__rz_port_text_*`). See the foundry question in section 8.
- **Design-local marker layers:** no layer outside the PDK map. Marker and recognition layers
  in use, all PDK-defined: 1/20 Activ.mask, 7/21 nSD.block, 26/0 TRANS, 99/31 Recog.diode, 111/0 EXTBlock,
  160/0 NoMetFiller, x/23 nofill, 51/0 and 52/0 Heat*, 189/4 prBoundary. Whether each is legal in a
  submitted mask GDS: assumed legal.
- Cell names include `retained_fullchip_*`, `__rz_port_text_*` and the legacy
  `placed_core_NOT_CONNECTED_FULLCHIP` lineage (now renamed). These are names only (see the handoff note on the legacy top name).

## 3. Seal ring

| Item | Value | Status |
| --- | --- | --- |
| Present | yes, drawn flat in the top cell (no separate seal-ring cell): EdgeSeal 39/0 one shape, box 32.2–1381.8 µm; 39/4 boundary; Passiv ring 25–1389 µm; ring shapes on Activ, pSD, Cont, Metal1–5, Via1–4, TopVia1/2, TopMetal1/2 in the top cell | confirmed (KLayout) |
| Rules | Seal.l (nothing outside the seal ring), Seal.m (one seal ring per chip), Seal.n (unbroken Passiv ring), Pad.d 7.5 µm / Pad.dR 25 µm pad-to-EdgeSeal | confirmed as documented rules (`main_rules.md`, `extra_rules.md`). The result on this file is in section 6 |
| IHP adds its own seal ring, or expects the designer's | the designer's is included | assumed |
| Seal-ring registration text | r2 (top cell, TEXT 63/0, same positions (5, 5) and (5, 1404) µm, size 5 µm): "Device registration size: x=1414.0 um ; y=1414.0 um\nCalculated area: 1.999396 sq mm" and "PDK version: IHP-Open-PDK 84374023ee8b4b126bebbba67fcbada0a9c0ff0b". r1 carried the stale 1050 µm / "PDK version: Unknown" text of the 1000 µm PCell that `sealring_g1.py` stretches (`review/audits/prepare_sealring_1414.py`). TEXT 63/0 is listed as not used for mask generation (layout rules §3.1) | **corrected in r2** (new SHA, full sign-off rerun: `reports/signoff-1414r2-20260925/`). Whether IHP reads this text at intake, and IHP's written confirmation of the 1.999396 mm² allocation: open |

## 4. Bond pads

| Item | Value | Status |
| --- | --- | --- |
| Pad cells | 24 `sg13g2_IOPad*` (retained copies): 11 Analog, 3 In, 2 Out4mA, 1 Out16mA, 1 Out30mA, 1 Vdd, 2 Vss, 1 IOVdd, 2 IOVss. Also 4 Corner, 112 fillers | confirmed (placement count) |
| Bond pads | 24 × `retained_fullchip_bondpad_70x70_tm1` (70 × 70 µm TopMetal2), plus 1 `bondpad_outward_5um_retained_metal`; 24 `dfpad` 41/0 shapes | confirmed |
| Passivation openings | 24 openings of 65.8 × 65.8 µm, plus the seal-ring Passiv ring | confirmed (merged 9/0) |
| Pad pitch, opening-to-die-edge distance, bonding rules for the QFN24 cavity | from the bond map below | assumed acceptable to the assembly house |

## 5. Bond map and package

| Item | Value | Status |
| --- | --- | --- |
| Bond map | `padframe/bondmap_20260925_r3.csv` (sha256 `ead5f109…`): the 24 rows of `bondmap_candidate_20260923_r2.csv` (pad number, pin, side, opening centre, 65.8 µm size, die 1414 µm) plus `qfn24_lead` and `lead_side` | confirmed: each row coincides with exactly one Passiv opening of r2 (centre to 1 nm, size, TopMetal2 enclosure ≥ 2.1 µm, inside dfpad) and the 22 TopMetal2 labels equal the row nets (`reports/signoff-1414r2-20260925/bondmap/verify_bondmap_r3.json`) |
| Hash binding | `candidate_gds_sha256` = `9049e87b…` (r2), status `chip_of_record` | **confirmed** (resolved 2026-09-25; the r2 CSV `3e363438…` / `candidate_not_tapeout` is superseded and unchanged) |
| Pin order (die pads) | S: 1 VDD, 2 VSS, 3 IOVDD, 4 IOVSS, 5 VSS, 6 IOVSS; E: 7 VDDA, 8 SENSE_P, 9 SENSE_N, 10 GATE, 11 FAULT_N, 12 EN; N: 13 TRIP_SET, 14 SCLK, 15 SDI, 16 SDO, 17 TEMP_OUT, 18 VREF; W: 19 G_SHARED, 20 D_STD, 21 D_ELT, 22 HBT_E, 23 HBT_B, 24 HBT_C | confirmed from the CSV and the GDS labels |
| Pad → QFN24 lead | owner decision 2026-09-25: each pad to the lead directly opposite, no crossings; leads counter-clockwise, pin 1 top-left of the top view; die rotated 90° clockwise so pads 1–6 face leads 1–6. Pads 1–12 → leads 1–12; pads 13–18 → leads 18–13; pads 19–24 → leads 24–19. Spec §3 carries both numbers | **decided**; plan and drawing `padframe/BONDPLAN_20260925.md`, `bondplan_20260925.svg`. Acceptance by the bonding house: open |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch; 10 packaged parts, no bare die | specified (`specification/G1_TOP_LEVEL_SPECIFICATION.md`). Availability on the IHP run: assumed |
| Die thickness | 200 µm | specified. The IHP backgrinding option: assumed |
| Cavity or paddle size for a 1.414 mm die, paddle connection (VSS or floating) | paddle = `VSS` (owner decision 2026-09-25, `BONDPLAN_20260925.md`) | paddle potential decided; cavity/paddle size: open |

## 6. Sign-off checks on `g1_chip_top_1414_r2.gds`

Results from [`blocks/g1_padring/reports/signoff-1414r2-20260925/README.md`](../blocks/g1_padring/reports/signoff-1414r2-20260925/README.md),
all run on this exact file (`9049e87b…`, top `g1_chip_top`) with the stock PDK decks at `84374023`, KLayout 0.30.9,
with the same options as the r1 sign-off ([`signoff-1414-20260924`](../blocks/g1_padring/reports/signoff-1414-20260924/README.md), `629d303a…`, superseded).
The file SHA-256 was rechecked after all runs and was unchanged.

| Check | Deck / tool | Status | Evidence |
| --- | --- | --- | --- |
| r1 top-cell rename is geometry-identical to the source | `flow/signoff/1414/verify_rename.py` | passed: 306 cells, same DBU/bbox, per-cell shapes and instances identical, deep XOR empty on all 73 layers | `signoff-1414-20260924/rename_verify/verify_rename.json` |
| r2 is metadata-only vs r1 | `flow/signoff/1414r2/verify_r2.py`, `gds_record_diff.py` | passed: 306/306 cells, per-layer XOR empty on all 73 layers, instance tree identical (60 118 instances) modulo 3 renames; on 63/0 only the two registration strings differ; raw GDS records differ only in those 2 STRINGs and the 3 renamed STRNAME/SNAME | `r2_identity/` |
| No modified cell carries a stock PDK name | `flow/signoff/1414r2/stock_compare.py` (per-layer XOR + texts vs every `libs.ref/*/gds`) | passed on r2: 51 exact stock-named cells, 0 differ (r1: 3 differed, now renamed) | `stock_compare/` |
| KLayout DRC main (hard rules) | `run_drc.py --run_mode=deep --no_density --disable_extra_rules` | passed, 0 markers (351 s) | `drc_main/` |
| KLayout DRC maximal | `sg13g2_maximal.drc` via `flow/signoff/1414/run_maximal.py` | passed, 0 markers (763 s) | `drc_maximal/` |
| KLayout DRC precheck | `run_drc.py --precheck_drc --disable_extra_rules` (density included) | passed, 0 markers (275 s); PreCheck, OFFGRID, ANGLE, PIN, FORBIDDEN and RECOMMENDED enabled. New in r2 (on r1 it was run only by the physical review, 0 markers) | `precheck/` |
| Density | `run_drc.py --density_only` | passed, 0 markers (40 s) | `density/` |
| Antenna | `run_drc.py --antenna_only --antenna` | passed, 0 markers (154 s); the R14 `sg13g2_IOPadIn` flag did not appear on this file | `antenna/` |
| Seal.* and Pad.* rules | inside the main/maximal DRC | passed: every `Seal.*` and `Pad.*` rule reports 0 errors | `drc_maximal/run.log` |
| LVS, full chip, canonical unprojected reference (`netlist/g1_chip_top_1414_r2.cdl`) | PDK KLayout LVS, `--top_lvl_pins --spice_comments` | failed (every per-circuit count identical to r1 modulo the `LevelDown` rename); cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130. "Netlists don't match"; 14 stock-named IO/level-shifter sub-cells NoMatch, top skipped (R13) | `lvs_canonical/pair_counts.json`; [`review/upstream/evidence/`](upstream/evidence/README.md) |
| LVS, full chip, projected reference | same options, comparison-only reference (3 all-VDD pad dummy PMOS removed) | passed: 61 684/61 684 devices, 31 173 nets, 22/22 pins, 0 warnings | `lvs_projected/pair_counts.json` |
| Block-to-netlist map | per-layer XOR of each chip block cell vs. its named block GDS (run on r1; carried to r2 by the identity above, not re-run) | passed (XOR empty) for SENSE, TRIP comparators and remainder, OSC, BGR, T2F, GATE, digital, level shifters, DOSE, DUT. IO ring: the PolyRes cells `g1_io_*_polyres_r1` are identical to IHP `dev` cells (2026-09-25); rest of the ring not XOR-checked | `blockmap/`; `upstream/evidence/xor/` |
| Off-grid, angle | inside the DRC | passed (part of main/maximal, 0 markers) | `drc_main/`, `drc_maximal/` |
| Digital timing (macro + routed signal netlist) | OpenSTA 3.1.0 | passed setup/hold, 3 corners; failed annotation / slew / fanout items dispositioned | `blocks/g1_ctrl/reports/sta_merged_sdc_20260924/README.md` |
| Full-chip PEX and timing of the final GDS | — | not run | |
| IHP's own intake checks (MPW Rejection Test) | IHP | not run | |

### Physical red-team findings addressed by r2

From [`redteam-20260925/PHYSICAL_TAPEIN.md`](redteam-20260925/PHYSICAL_TAPEIN.md):

| Finding | Resolution | Status |
| --- | --- | --- |
| 1. Die area vs registration; stale registration text | Text corrected in r2 (section 3) | text **resolved**; IHP written confirmation of the 1.999396 mm² allocation still **open** |
| 4. Bond map bound to an older GDS | `bondmap_20260925_r3.csv` bound to `9049e87b…`, geometrically re-verified | **resolved** |
| 6. Modified cell with a stock library name | `sg13g2_LevelDown` → `g1_LevelDown_polyres`; the wider check (including `sg13g2_pr.gds`) also found `nmos`/`pmos` PCell variants and renamed them; 0 differing stock-named cells remain | **resolved** |
| 2. North/west pad order vs package | owner decision 2026-09-25: pad to the lead directly opposite, spec §3 renumbered (section 5) | **resolved** (bonding-house acceptance open) |
| 3. IHP's own tape-in check | stock precheck mode passed on r2; IHP's MPW Rejection Test not run | **open** |

## 7. Board constraints (to go with the parts)

| Constraint | Source | Status |
| --- | --- | --- |
| **VDD (1.2 V) must come up before or together with IOVDD (3.3 V).** On the chip netlists, IO-first drove `GATE` to 3.28–3.30 V for 4.2–4.4 µs until `VDD` was up, with or without a 10 kΩ pull-down, at tt/27, ss/125 and ff/−40 °C (`--pads nodcn`). | `blocks/g1_top/sim/campaigns/RESULTS_20260925.md` §5; spec §6 P1 | simulated on the chip netlists (behavioural front end); IO-first with stock pads not run to completion |
| **Independent load-bus inhibit during every power-up, whatever the order** (corrected 2026-09-25): with the `EN` pad model the `EN` input reads enabled and the `GATE` latch state is undefined until `IOVDD` > 1.1 V (`review/redteam-20260925/ELECTRICAL_SYSTEM.md` M1). Pull-downs on `EN`/`SCLK`/`SDI`, a clean fast `EN` edge, a `VDD` supervisor and a Kelvin-integrity check: spec §6 P8, P9. Core-first on the chip netlists (ideal `EN` copy): `GATE` ≤ 0.0725 V without pull-down (`gB_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log`), ≤ 0.0090 V with 10 kΩ (`gB_pd`). With IO first only the independent load-bus inhibit holds the FET off. | `blocks/g1_top/README.md`; spec §6 P2 | simulated on the chip netlists. (The earlier "VDD-first without it did not converge" came from the schematic 1350 µm review, `G1_DESIGN_REVIEW.md`, and is superseded.) |
| **VDDA (pin 7) tied to the IOVDD 3.3 V rail on the board.** VDDA must not exceed IOVDD by more than a diode drop. | `specification/G1_TOP_LEVEL_SPECIFICATION.md` (pin 7, D14) | specified |
| EN low at power-up (EN is the only digital reset; no pad pull-down) | register map; spec §6 P6 | specified |
| Every EN rise re-opens the ~1 ms inrush window with `FAST_EN`=0 and defaults restored | spec §6 P7 | accepted design behaviour covered by the external inhibit, pending owner confirmation |
| Host rules H1–H5: clock watchdog (`CHIP_ID`/`OSC_CNT_L`), `INRUSH` changes only under the inhibit, read-back and ≥ 128-cycle idle for safety-relevant writes, `SOFT_TIME` only with `SOFT_EN` cleared, periodic configuration rewrite | spec §6; `review/redteam-20260925/DIGITAL.md` | specified (host contract) |
| SCLK ≤ f_OSC; host drives SDI ≥ 2 ns after the falling SCLK edge | SDC / register map | specified (STA assumption) |

## 8. Open foundry questions

1. **R13, IO-cell LVS:** canonical full-chip LVS failed; cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130. The IO cells fail cell-level LVS
   against the PDK's own CDL even with the `dev` deck and library, where the `rppd` is now extracted:
   `sub!` is local in every IO subcircuit, and ptap and antenna-diode records do not pair; rails
   are joined only by abutment. Which LVS result does IHP accept? (`PLAN.md` R13,
   [`upstream/evidence/`](upstream/evidence/README.md), draft report `upstream/ihp-io-lvs-issue-draft.md`,
   `blocks/g1_padring/reports/lvs_reference/`)
2. **R14, antenna deck:** `Ant.e` flags every current-revision `sg13g2_IOPadIn` because the
   receiver gate is tied to the `vdd` rail; the previous cell revision is clean. Is this a
   deck/library artefact that IHP waives? (`blocks/g1_padring/reports/antenna_reference/`)
3. **PolyRes markers on design-local IO cell copies:** `g1_io_rc_polyres_r1` and
   `g1_io_secondary_polyres_r1` (and their aliases) are project copies that carry PolyRes 128/0. They are identical on every
   layer to `sg13g2_RCClampResistor` / `sg13g2_SecondaryProtection` in IHP's `dev` library after PR #1223 (not yet on `main`).
   Is that acceptable to IHP for a `84374023`-based submission?
4. **ELT not included:** the enclosed-layout NMOS variant failed `Gat.f` and is not in the
   chip. Pad 21 `D_ELT` is a legacy name for the HV NMOS drain of the default dose pair.
   Tell IHP so that no ELT-specific handling is expected.
5. Texts on HeatTrans 51/0 and HeatRes 52/0, labels on `.text`/`.pin` layers, and prBoundary 189/4: keep or strip? (assumed keep)
6. Die size 1414 µm (1.999396 mm², now also stated in the r2 registration text) vs the registered area, QFN24 cavity fit and 200 µm thinning. (assumed) Paddle potential: `VSS` (owner decision 2026-09-25).
7. Submission deadline: "end of September 2026" in repository notes vs the owner's recollection of 21 October. **Unreconciled**, confirm with IHP.

## 9. Before submission

- [ ] Final GDS identity frozen. Current: r2 `9049e87b…` (2026-09-25); `gds_inventory.py` and the bond-map match re-run on it. If it changes again, re-run both and update every sha256 here.
- [x] Section 6 filled from `signoff-1414r2-20260925/` (r2), with passed / failed / not run as reported.
- [x] Bond map rebound to the r2 sha256 as a new CSV revision (`bondmap_20260925_r3.csv`), with QFN24 lead numbers.
- [ ] Canonical LVS: failed; cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130. IHP's acceptance of the projected-reference result (§8 question 1): open.
- [x] Stale seal-ring registration text (section 3) resolved: corrected in r2 with a full sign-off rerun.
- [ ] IHP's official instructions added, and every "assumed" item resolved.
- [ ] A human signs and submits. Agents do not push or submit.
