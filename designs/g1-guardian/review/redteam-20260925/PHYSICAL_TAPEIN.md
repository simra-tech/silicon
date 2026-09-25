# G1 physical tape-in red-team review (2026-09-25)

Independent review of the GDS of record. The aim was to find anything that could
make IHP reject the file or make the silicon differ from intent. Each check below ran
on the file itself. The sign-off records were not taken on trust. Nothing tracked was
modified, and the GDS was not edited.

## Scope and built-against

| Item | Value | How established |
|---|---|---|
| GDS | `designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds`, sha256 `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | `sha256sum` at the start of the review |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (a `dev`-branch commit dated 2026-07-24; not an ancestor of `origin/main`) | container `COMMIT` check in `flow/run.sh`; `git log` / `git merge-base` in the local PDK clone |
| KLayout | 0.30.9 (PDK `versions.txt` minimum: 0.30.5) | `run_drc.py` log |
| Container | `tapeoutbench-eda` `sha256:ddeb6957…` | `flow/run.sh` identity check |
| CPUs | 36-37 (`taskset`, rootless cgroups v1) | `G1_CPUSET=36-37` |
| Scripts / raw output | `${BULK}/redteam-20260925-physical/{scripts,s1..s10,precheck,maximal}` | not committed (bulk). Script sha256 prefixes: s1 `42906182`, s2 `fc55fcec`, s3 `3161696d`, s4 `f58f9318`, s5 `b8a1fe29`, s6 `0ba75407`, s8 `303d1655`, s9 `54af1d3f`, s10 `7094e0b4` |

Every script was run as
`G1_CPUSET=36-37 G1_CPUS=2 G1_CONTAINER_ENGINE=podman G1_WORKDIR=. G1_RESULTS_ROOT=${BULK}/redteam-20260925-physical flow/run.sh klayout -b [-n sg13g2] -r <script>`.
The GDS header parse used host `python3` on the raw records.


> **Disposition 2026-09-25 (after this review).** Findings 1 (labels), 4 (bond map) and 6 (stock-named modified cell)
> are resolved in revision r2 (`layout/g1_chip_top_1414_r2.gds`, SHA256 9049e87b…): labels corrected, three modified
> stock-named cells renamed, per-layer XOR against r1 empty, full sign-off re-run at 0 markers (see
> `blocks/g1_padring/reports/signoff-1414r2-20260925/README.md`). Finding 2 is resolved by the owner's choice of the
> standard convention (`padframe/BONDPLAN_20260925.md`, spec §3 lead column). Finding 5 (density margins) was accepted
> as is by the owner. Finding 3 (IHP rejection test) is done by the owner on the r2 file. The 2 mm² allocation was confirmed by the owner on 2026-09-25, so finding 1 is closed.

## Ranked findings

Severity key: **blocker** means IHP will or is likely to reject the file, or the silicon
will not work as intended. **must-fix** means it has to be resolved before submission
(the fix can be a document or a confirmation, not only a GDS change). **should-fix**
means real risk or a thin margin. **note** means it should be recorded or disclosed.

### 1. Blocker until confirmed: die area vs registration, and the stale registration text

- The die outline (EdgeSeal boundary 39/4 and the top-cell bbox) is 1414 × 1414 µm = **1.9994 mm²**.
  The top cell carries the sealring-PCell registration labels on TEXT 63/0, at (5, 5) µm and (5, 1404) µm:
  `Device registration size: x=1050.0 um ; y=1050.0 um\nCalculated area: 1.1e-06 sq mm` and
  `PDK version: Unknown (Not a Git repo or Git not installed)`.
  The PDK PCell writes this text for device registration (`sealring_code.py`, "Creating text label w/ area for device registration").
  In this file it states a 1050 µm die and an unknown PDK version.
- Whether the shuttle allocation covers 1.9994 mm² is recorded as *assumed* in `review/TAPEIN_PACKAGE_20260924.md` §1 and §8 item 6.
  No written confirmation is in the repository.
- Check: s1 (`top_texts_63`), s2 (EdgeSeal boundary `(0,0;1414000,1414000)`).
- Action: get written confirmation of the allocated area from IHP. Either correct the two labels to `x=1414.0 um ; y=1414.0 um` and the real PDK commit (a text-only change, provable by the same per-layer XOR method as `verify_rename.py`), or declare the mismatch explicitly in the submission.

### 2. Must-fix: pad numbering on the north and west sides runs opposite to package order

- The bond map (`padframe/bondmap_candidate_20260923_r2.csv`) and the GDS labels agree with each other.
  South pads 1→6 run left to right (x = 395…955) and east pads 7→12 run bottom to top.
  North pads 13→18, however, also run **left to right** (x = 395…955 at y = 1313), and west pads 19→24 run **bottom to top** (y = 395…955 at x = 101).
  In a counter-clockwise sequence, 13→18 would run right to left and 19→24 top to bottom.
- `padframe/README.md` specifies "pad *n* on side *s* to the lead directly opposite, no crossings".
  Under the standard counter-clockwise QFN24 lead numbering, that bonds pad 13 to lead 18, pad 18 to lead 13, pad 19 to lead 24, and so on.
  The package pin numbers of all 12 north and west pins would then differ from the spec's pin map (`specification/G1_TOP_LEVEL_SPECIFICATION.md` §3).
  The alternative is to bond pad *n* to lead *n*, which needs crossing wires on two sides.
- Check: s2 `label_map` (22 TopMetal2 labels on 134/25, each at an opening centre, with names equal to the CSV rows) against the CSV coordinates.
- Action: before the bonding diagram is ordered, write the explicit pad→lead table with QFN lead numbers and the pin-1 mark. Then either renumber the spec and board pinout, or accept the reversed lead order in writing. This needs no GDS change.

### 3. Must-fix: IHP's own tape-in check has not been run

- Layout rules §4.1 (`libs.doc/doc/SG13G2_os_layout_rules.pdf`, Rev 0.4) says that critical rules "are checked during tape-in… If any of them are violated, the layout is rejected… no waivers are granted". It recommends the online **MPW Rejection Test** (dk.ihp-microelectronics.com).
  The open KLayout decks mirror those rules but are not IHP's check.
- The stock KLayout **precheck** mode was not run in the sign-off (`TAPEIN_PACKAGE` §6: "not run").
  **This review ran it** (details below): 0 markers.
- Action: run IHP's rejection test, or whatever check IHP names in its submission instructions, on this exact SHA.

### 4. Must-fix (documentation): the bond map is bound to an older GDS

- The CSV column `candidate_gds_sha256` is `3e363438…` and `status` is `candidate_not_tapeout`.
- An independent geometric check of this file passed. All 24 Passiv openings are 65.8 × 65.8 µm rectangles at exactly the CSV centres. Each is enclosed by TopMetal2 by 2.1 µm and lies inside dfpad. The pitch is 112 µm, the opening-to-die-edge distance is 68.1 µm, and the opening to the inner EdgeSeal edge is 31.7 µm (Pad.d 7.5, Pad.dR 25). Every one of the 22 labels sits at its opening centre.
- Check: s2 `openings`, `label_map`.
- Action: write a new CSV revision bound to `629d303a…` (already listed in `TAPEIN_PACKAGE` §9).

### 5. Should-fix: two density figures pass by very thin margins

| Rule | Value on this file | Limit | Margin | Source |
|---|---|---|---|---|
| GFil.g, global GatPoly (5/0 ∪ 5/22, merged) | **15.021 %** | ≥ 15 % | 0.021 points ≈ 420 µm² of poly | s6 flat merged area; the stock density deck gives the same 15.02 % |
| M2Fil.h, Metal2 ∪ filler in the worst 800 × 800 µm window | **25.21 %** at window origin (290, 320) µm | ≥ 25 % | 0.21 points | s8: sweep of every window position on a 5 µm grid, all windows inside the die |
| AFil.g2, Activ in the worst 800 × 800 µm window | 27.09 % at (330, 330) µm | ≥ 25 % | 2.1 points | s8 |
| M4Fil.h, worst window | 26.87 % at (295, 295) µm | ≥ 25 % | 1.9 points | s8 |

The stock density deck steps its windows by 400 µm, so it never evaluates the worst Metal2 window found here. It passes the file (0 markers in both sign-off and this review's precheck).
GFil.g and MxFil.h are on the precheck (critical) list. A small difference in IHP's area basis would flip GFil.g: for example, a chip area taken from the seal outline with scribe added, or a different treatment of GatPoly under PolyRes. GatPoly ∪ PolyRes is 17.13 %.
Action: ask IHP which area basis and window step they use. If the margin cannot be confirmed, add GatPoly and Metal2 fill in the core. That is a GDS change and needs a full re-sign-off.

### 6. Should-fix: a cell with a stock library name has modified content

- `sg13g2_LevelDown` in this GDS is not the PDK cell. It carries 2.00 µm² of PolyRes 128/0 (through `g1_io_secondary_polyres_r1`), which the PDK cell does not.
  If the shuttle merge or a library-cell substitution matches cells by name, the two versions collide.
- Every other stock-named cell (84 of them: all standard cells, all `sg13g2_Clamp_*`, `DCN/DCPDiode`, `LevelUpInv`, `GateLevelUpInv`, `RCClampInverter`) is geometrically identical to the PDK GDS, including texts.
  The renamed IO cells `retained_fullchip_sg13g2_*` differ from the stock cells only on 128/0:
  IOPadVdd and IOPadIOVdd +520 µm², IOPadIn +2 µm², IOPadAnalog +2 µm². All other layers XOR to zero.
- Check: s3 `stock_compare` (per-layer XOR of each chip cell against `libs.ref/sg13g2_io/gds/sg13g2_io.gds` and `sg13g2_stdcell.gds`, plus a text comparison).
- Action: rename it design-locally (for example `g1_LevelDown_polyres`), or return to the unmodified stock cells. That is `TAPEIN_PACKAGE` §8 question 3. Either way it is a GDS change.

### 7. Note: TopVia2 under the passivation opening on all 24 pads

- 3168 TopVia2 (133/0) shapes overlap the 24 openings, 1078.7 µm² in total (44.9 µm² per pad). None lies wholly inside an opening: they straddle the opening edge, in the 2.1 µm enclosure band of the via ring.
  The deck's Pad.kR uses `TopVia2.inside(Passiv_dfpad)` and so does not flag them.
  The rule text reads "TopVia2 may be damaged during packaging… we recommend not to use them below Passiv".
- All of these vias are in `retained_fullchip_bondpad_70x70_tm1`. The PDK `bondpad` PCell places its via ring in the edge stripe (`bondpad_code.py`, square/stack branch), so this is a property of the PDK cell and not a design edit.
- Check: s3 `tv2_*`.

### 8. Note: PDK commit and deck provenance

- `84374023` is on `dev` and not on `main`. In the local clone's refs, the KLayout DRC tree differs from `origin/main` (2026-09-01) and from `origin/dev` (2026-09-23) only in two places: the Schottky rule `6_7_schottkydiode.drc` (schottky_contbar derivation) and a new `recog_momf` 99/40 layer definition. This design has no Schottky diode and no 99/40, so neither change affects it. The remote was not fetched during this review.
- The deck header carries no version string. The KLayout version gate comes from `versions.txt` (0.30.5; 0.30.9 was used).

### 9. Note: shuttle-merge hygiene of names and records

- The library name is `LIB`. There are generic cell names such as `nmos`, `pmos`, `nmos$1`, `cmim$1` and `rppd$2$1`. 24 cell names are longer than 32 characters (for example `__rz_port_text_033_g1_cmp_regenpair4`). BGNLIB timestamps are all zero.
  None of these breaks KLayout, but a multi-project merge can rename or collide generic names. Ask IHP whether a unique prefix is required.
- The file also contains 141 PATHTYPE 4 paths (custom extensions) and 37 246 PATHTYPE 2 paths. The GDS version is 600. MAG and ANGLE appear only on TEXT elements (MAG) and on SREF/TEXT (ANGLE 90/180/270). There is no magnified or arbitrarily rotated instance.
- 39/4 EdgeSeal.boundary and 189/4 prBoundary.boundary are in `sg13g2.lyp` but not in the rules-PDF layer table (§2). All other 71 layer/datatype pairs are in it. Both 39/4 and 189/4 come from PDK cells.
  Ask IHP whether these, the `.text`/`.pin` layers and the HeatTrans/HeatRes texts should be kept (`TAPEIN_PACKAGE` §8 item 5).

### 10. Note: the `D_ELT` label

- There is no enclosed-layout transistor in the file: 0 merged GatPoly polygons have a hole, so there is no ring gate over Activ (s3).
  Pad 21 is still labelled `D_ELT` on 134/25. The disclosure is already planned (`TAPEIN_PACKAGE` §8 item 4).

### 11. Note: VDDA is supplied through an analog pad

- `VDDA` (pad 7) is an `sg13g2_IOPadAnalog` feeding the 3.3 V core blocks, and it is its own net (s4 `pad_clusters`: cluster 4, separate from `iovdd`).
  Its only ESD path is the analog pad's DCP diode to `iovdd` and then the IOVdd clamp. There is no dedicated VDDA-to-VSS clamp. This is a design decision (D14) and is recorded here for the ESD assessment only.

## Checks that passed

| Check | Result | Evidence |
|---|---|---|
| Top cell and hierarchy | **passed**: one top `g1_chip_top`; 306 cells; no ghost, proxy, empty or orphan cells; no duplicate STRNAME; none of the 60 118 recursive instances and no shape on any layer extends outside (0,0;1414,1414) µm | s1; raw GDS parse |
| Database unit | **passed**: UNITS 0.001 µm / 1e-9 m; GDS version 600 | raw GDS parse |
| Layers vs PDK map | **passed**: 73 pairs, all in `sg13g2.lyp`; none of the §3.2 forbidden layers; texts only on x/25, 51/0, 52/0 and 63/0, none on a mask drawing layer | inventory JSON (re-derived in s1) |
| Seal ring geometry | **passed**: Activ, pSD, Cont, Metal1–5, Via1–4, TopVia1/2, TopMetal1/2, EdgeSeal and Passiv each merge to one closed ring (1 polygon, 1 hole). Metals, Activ, pSD and EdgeSeal run 32.2–36.4 µm from each edge; via and contact bars start at 34.2 µm (Cont 0.16 µm wide, Via 0.19, TV1 0.42, TV2 0.90); the Passiv ring runs 25.0–29.2 µm. These are the `sealring_code.py` offsets with edgeBox 25 µm. The corners are stepped with no 45° edges, as the PCell draws them | s2 `seal_cut_707`; s10 |
| Pad openings | **passed** (see finding 4) | s2 |
| Bond-map labels vs openings | **passed**: 22 labels at the 22 uniquely named openings; the second VSS (843, 101) and second IOVSS (955, 101) pads carry no label and reach their nets through the ring | s2; s4 |
| Ring rails | **passed**: `iovss` (3 bands), `iovdd` (2 bands), `vdd` and `vss` each probe to a single net cluster on Metal3, Metal4, Metal5 and TopMetal1 at every 2 µm sample around the ring. Gaps occur only inside the stepped corner cells, and on TopMetal2 inside the supply pad cells where the pad strap crosses; both are stock-cell geometry. The four rail nets are distinct from one another | s4 (LayoutToNetlist Metal1…TopMetal2 with vias; `probe_net` samples) |
| Pad to rail | **passed**: VDD→`vdd`, both VSS→`vss`, IOVDD→`iovdd`, both IOVSS→`iovss`; the 18 other pads, VDDA included, are 18 distinct nets (metal connectivity only) | s4 `pad_clusters` |
| ESD present | **passed**: every IO cell, corner and filler is geometrically identical to the PDK `sg13g2_io` except the PolyRes additions in finding 6, so the stock diodes and clamps are present unmodified | s3 |
| PolyRes 128/0 over gates | **passed**: PolyRes ∩ Activ = 0 and PolyRes ∩ (GatPoly ∩ Activ) = 0 over the whole chip; all PolyRes lies inside SalBlock, EXTBlock and pSD. So the LVS deck's `tgate = gatpoly & activ − res_mk` removes no MOS gate, and no rppd forms over an active gate | s3 |
| Drawn devices vs PCells (HBT) | **passed**: 308 npn13G2 (TRANS 26/0). No shape of the PDK PCell is missing on any of 12 FEOL layers at any of them. The `npn13G2$7` cell is XOR-identical to the default PCell. The only extra geometry within 1.5 µm is neighbouring Activ/Cont, which is DRC-clean | s9 |
| Antenna diodes | **passed (presence only)**: the OSC cell contains one Recog.diode shape (the claimed `vth` diode). The 6 top-level `sg13g2_antennanp` A pins land on 4 signal nets. Whether the OSC diode is connected to `vth` was **not traced**. The antenna deck was not re-run here; the sign-off record shows 0 markers | s5 `recog_diode_cells`; s4 `antenna_cells` |
| Precheck DRC (`run_drc.py --precheck_drc --disable_extra_rules`, with density) | **passed, 0 markers**, 321 s. Log: FORBIDDEN, PIN, OFFGRID, ANGLE and RECOMMENDED enabled, PreCheck true | `${BULK}/redteam-20260925-physical/precheck/` |
| Maximal DRC re-run (`run_maximal.py`, stock `sg13g2_maximal.drc`, recommended rules on) | **passed, 0 markers**, 901 s | `${BULK}/redteam-20260925-physical/maximal/` |
| Recommended rules in the sign-off main run | **passed** (record inspected): `RECOMMENDED enabled: true`; Pad.fR_M1…TM2 executed; the lyrdb has 0 items. The earlier 1350 µm assembly's 60 Pad.fR markers are not present | `reports/signoff-1414-20260924/drc_main/*.log`, `*.lyrdb` |
| Global densities | **passed**: Activ 44.22 %, GatPoly 15.02 %, M1 46.97 %, M2 37.35 %, M3 47.79 %, M4 46.76 %, M5 48.38 %, TM1 50.33 %, TM2 46.84 % (flat merged areas equal the deck's) | s6; precheck density log |
| Fill near the edges | **passed**: fill starts 1.1 µm inside the seal ring (Activ filler at 37.5 µm). This is the PDK filler behaviour (`sg13g2_filler_ActGatP.lym` fills `EdgeSeal.holes`), and Seal.b applies to Activ drawing only | s2 `sealband`, macro source |

## Maximal re-run

**Passed, 0 markers.** The stock `sg13g2_maximal.drc` was run through `flow/signoff/1414/run_maximal.py` with 2 threads and `no_recommended=false`, and completed in 901 s (rc 0). 292 rule lines each report "0 error(s)", including Pad.aR/a1/bR/d/dR/d1R/gR/jR/kR and all Seal.* rules, and the lyrdb has 0 items. This matches the sign-off record.

## Not run

- IHP MPW Rejection Test (finding 3).
- Main and antenna DRC were **not re-run** in this review; the sign-off records were inspected.
- LVS (canonical or projected) was **not re-run**. The canonical failure (R13) stands as recorded.
- Tracing the OSC antenna diode to `vth`, and device-level ESD path checks: **not run** (identity to the stock cells used instead).
- Comparison of `retained_fullchip_bondpad_70x70_tm1` against a fresh PDK `bondpad` PCell: **not run**.
- Seal-ring geometry against a native 1364 µm PCell: **not applicable** at this PDK commit (the PCell fails above 1000 µm; `sealring_g1.py`). The measured offsets and closure above were used instead.
