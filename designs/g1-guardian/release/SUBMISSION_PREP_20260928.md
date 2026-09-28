# G1 guardian: IHP Open-Silicon-MPW submission package (submitted 2026-09-28)

Prepared and submitted 2026-09-28. **Status:** repository https://github.com/simra-tech/IHP__SoC1816
(main, one commit) holds the package below with `trl` 5 and the TRL sheet filled; the request issue is
https://github.com/IHP-GmbH/Open-Silicon-MPW/issues/68 (`Request for submission Oct-2026 IHP__SoC1816`,
opened 2026-09-28, awaiting IHP's review). The seal ring was verified present in the release GDS
(EdgeSeal 39/0 and the metal ring at 32.2 um inset from the die edge, flattened into the top cell;
KLayout `bbox_per_layer`). Before submission no solver was run. KLayout was used
only to re-save and inspect the GDS. `${REPO}` is a checkout of https://github.com/simra-tech/silicon
(at `fb355d9f2`, the commit before the one that adds this file), the package is `IHP__SoC1816/` next to this file (`${PREP}` below is the
directory the package was prepared in).

The IHP instructions were read from https://github.com/IHP-GmbH/Open-Silicon-MPW, branch `main` at
`d757e3b06125b0eac657017bcfddafa0e351d114` (2026-09-24). In this file, `MPW/` stands for
`https://github.com/IHP-GmbH/Open-Silicon-MPW/blob/main/`, and `issues/N` for
`https://github.com/IHP-GmbH/Open-Silicon-MPW/issues/N`.

## 1. What IHP requires

- **How submission works.** The IP lives in its own GitHub repository. After a GitHub issue
  requests it, IHP adds that repository as a git submodule under
  `<MPW-run>/<Category>/IHP__<abbrev><4digits>` (MPW/README.md, MPW/Submission-process.md).
- **Naming.** The repository and its directory are named `IHP__<subcategory-abbrev><4digits>`.
  The 4 digits come from `gen_structure.py` (random, 0000-9999). The top cell name is the generated
  name without `IHP__` (for example `OPA4532`) and must be the same "across all views". The
  `info.json` fields `name` and `top_cell_name` carry it (MPW/IP-development-steps.md step 4,
  MPW/gen_structure.py). The categories are listed in MPW/IP-Categories.md and
  MPW/ip-categories.json. G1 fits Mixed-Signal / SystemOnChip / `SoC`.
- **Repository layout.** This is what `python3 gen_structure.py IHP SoC` creates (MPW/gen_structure.py;
  example in MPW/IHP__ADC5871-structure.md):
  - `README.md` and `.github/workflows/check-workflow-sync.yml`;
  - `doc/{info.json,Datasheet.md,Specification.md,TRL-Mixed-Signal-IP.md}`;
  - `dependencies/` and `measurements/v.1.0.0/`;
  - `release/v.1.0.0/{gds,netlist,doc}/` and `release/v.1.0.0/ReleaseNote.md`;
  - `<name>-main/`, containing `layout/{def,klayout,lef,magic}`, `model/{spice,verilog-A}`,
    `netlist/{layout,pex,rcx,schematic}`, `schematic/{qucs-s,xschem}`,
    `testbenches/{ac,corners,noise,tran}/{qucs-s,xschem}`, `timing/`, `verification/{drc,lvs}` and `README.md`.
- **info.json fields.** The defaults are written by `create_ip_structure` in MPW/gen_structure.py.
  IHP publishes no schema and no list of allowed values beyond these:

  | Field | Value or default |
  | --- | --- |
  | `name` | the generated name, for example `SoC7610` |
  | `design_type` | `A`/`D`/`M`/`R`/`P` (Analog/Digital/Mixed-Signal/RF/Photonics) |
  | `technology` | `IHP`, `SKY` or `GF`; must be `IHP` |
  | `unique_id` | the 4 digits, as a string |
  | `license` | default `Apache-2.0` |
  | `trl` | integer, default 0 |
  | `sealring_x`, `sealring_y` | float, default 1.0; unit not stated |
  | `repository` | URL |
  | `pdk_version` | default empty |
  | `process` | default `SG13CMOS` |
  | `dependencies`, `tools` | objects |
  | `top_cell_name` | the generated name |
  | `release` | `version` (`v.1.0.0`), `gds`, `netlist`, `doc`, as paths relative to the repository root |

  Accepted examples are in `MPW/March-2026/submitted-tmp/SG13G2/*/info.json`:
  - SoC7610: die 3350 µm, `sealring_x` 3350.0, `pdk_version` a commit hash;
  - RFID4410: `sealring_x` 1.414, `release.gds` = `release/v.1.0.0/gds/RFID4410.gds.gz`, `netlist` empty.
- **GDS save options.** These are set in MPW/IP-development-steps.md ("Acceptance criteria" item 5)
  and MPW/fig/klayout_save.png. IHP applies them with MPW/March-2026/submitted-tmp/conv2sub.pv.
  - Format GDS2, all layers, database unit 0.001 µm, scaling 1.0.
  - "Store PCell and library context information" **off** (`write_context_info = False`).
  - Library name `LIB`, maximum cell-name length 32000, maximum vertices 8000.
  - Multi-XY off, cell and layout properties off, skew arrays not resolved.
  - "Eliminate zero-length paths" **on** (`gds2_no_zero_length_paths = True`).
  - Time stamps on. Compression "Auto" (chosen by the file extension).

  IHP also removes zero-area polygons on 36 listed layers (MPW/March-2026/submitted-tmp/zero.py, INFO.md).
- **Sign-off** (MPW/IP-development-steps.md, "Acceptance criteria"):
  - a seal ring is present;
  - fillers are generated and included;
  - DRC is clean, including the minimal rules in IHP-Open-PDK
    `ihp-sg13g2/libs.tech/klayout/tech/drc/docs/precheck_rules.md` (a violation of these can lead to rejection);
  - LVS is clean against the final netlist;
  - the release GDS is saved with the options above.

  IHP's CI reads `release.gds` and `release.netlist` from `doc/info.json`. It runs DRC with the
  precheck on, and LVS if a netlist is referenced. A referenced file that is missing fails the run.
- **Rules seen only in IHP review comments on issues:**
  - only one GDS under `release/` (issues/62);
  - a design without a seal ring, or with a wrong `info.json`, is refused, and the density rules
    AFil/MFil are enforced (issues/66);
  - the LBE layer is not allowed (issues/67).
- **Die size.** The MPW repository publishes no die-size rule. MPW/Packaging.md says IHP offers
  QFN64 with a fixed 18 mm² padframe.
- **Submission and deadline.** Open an issue titled `Request for submission <MPW-run>
  IHP__<abbrev><4digits>` with the repository URL, category directory, submodule path and a
  `.gitmodules` snippet. IHP confirms on GitHub (MPW/Submission-process.md). The documents still
  say `July-2026`, but the current open requests use `Oct-2026` (issues/58, 61, 62, 64, 66, 67).
  **The repository states no deadline and no other form.**

## 2. Requirement checklist

| Requirement | Source | How satisfied | Status |
| --- | --- | --- | --- |
| Category, subcategory, abbreviation | MPW/IP-Categories.md | Mixed-Signal, SystemOnChip, `SoC` | passed (category confirmed by the owner 2026-09-28) |
| Name `IHP__<abbrev><4digits>` from the generator | MPW/IP-development-steps.md step 3 | `gen_structure.py IHP SoC` (Python 3.11) gave `IHP__SoC1816`. The ID 1816 appears in none of `Catalog.md`, `.gitmodules`, the MPW issues or a GitHub repository search | passed |
| Repository follows the generated structure | MPW/IP-development-steps.md, MPW/gen_structure.py | the package is the generator output, populated. Empty generated directories are kept here; git will not keep them | passed |
| Top cell = generated name in every view | MPW/IP-development-steps.md step 4 | GDS top renamed `g1_chip_top` → `SoC1816`; CDL top `.SUBCKT` renamed; `info.json` `name`/`top_cell_name` = `SoC1816`. The copied sign-off reports keep the old name because they describe the source file | passed |
| `doc/info.json` complete and correct | MPW/IP-development-steps.md checklist | filled; `trl` left as a TODO string. `process` set to `SG13G2`: the generator default is `SG13CMOS`, but the chip uses `npn13G2` HBTs. `sealring_x/y` = 1.414, with the unit assumed to be mm as in the RFID4410 example | filled: `trl` 5; `sealring_x/y` corrected to 1414.0 on 2026-09-28 (IHP's pre-check compares them with the 63/0 text label in um, tolerance 0.001: issues 8, 50, 61); `process` either value accepted (issues/13) |
| TRL document in `doc/` | MPW/IP-development-steps.md step 4 | filled 2026-09-28 (self-assessed TRL 5, 31 of 41 items met, each with its evidence path) | passed |
| `doc/Datasheet.md`, `doc/Specification.md` | MPW/gen_structure.py | datasheet summary written; specification copied from the design repository | passed |
| `release/v.1.0.0/` holds the final GDS and netlist; the `info.json` paths resolve | MPW/IP-development-steps.md | `gds/SoC1816.gds`, `netlist/SoC1816.cdl`, `doc/` and `ReleaseNote.md`; both `info.json` paths exist | passed |
| One GDS under `release/` | issues/62 | one file | passed |
| GDS saved with the IHP KLayout options | MPW/fig/klayout_save.png, conv2sub.pv | `resave_for_ihp.py` sets every option in the figure explicitly. Header check: LIBNAME `LIB`, units 1e-3 µm / 1e-9 m, GDS 600, no context cell | passed |
| The re-save did not change the geometry | this task | `compare_gds.py`: 304 cells, 1 284 438 shapes and 55 646 instances identical. Negative control (r3 against the release file) detects the TRIP cell and the top cell | passed |
| No zero-area polygons (IHP removes them) | MPW/March-2026/submitted-tmp/zero.py | `inspect_gds.py` with IHP's layer list finds 0 | passed |
| Seal ring present | MPW/IP-development-steps.md | EdgeSeal 39/0 ring 32.2-1381.8 µm, Passiv ring, registration text (`TAPEIN_PACKAGE_20260924.md` §3) | passed |
| Fillers generated and included | MPW/IP-development-steps.md | x/22 filler shapes on Activ, GatPoly, Metal1-5 and TopMetal1/2; the density run gives 0 markers; GFil.g margin 918.98 µm² | passed |
| DRC clean, including the precheck rules | MPW/IP-development-steps.md | r4 sign-off on the source GDS: main, maximal, precheck, density and antenna give 0 markers with the stock deck `84374023` and with IHP dev deck `4fd47c5e`. Copied to `SoC1816-main/verification/drc/` | passed on the source GDS; not run on `SoC1816.gds` itself |
| LVS clean against the final netlist | MPW/IP-development-steps.md | canonical CDL **failed**: 14 IO and level-shifter sub-cells, caused by the PDK IO reference semantics (IHP-Open-PDK #1218/#1130). The projected reference passed: 62 956 devices, 22/22 pins | **failed** (canonical) |
| IHP CI DRC/LVS on the repository | MPW/IP-development-steps.md, "Automated verification flow" | needs the published repository. LVS is expected to fail as above, because `release.netlist` is referenced | not run |
| Die size and package | MPW/Packaging.md | 1414 × 1414 µm with its own padring, QFN24. IHP documents only QFN64 on an 18 mm² padframe | asked in issues/68 (QFN24 or QFN64 only) |
| Submission request issue and deadline | MPW/Submission-process.md | filed as issues/68 for the `Oct-2026` run (the run the other open requests target) | done |
| Dependencies under `dependencies/` | MPW/IP-development-steps.md | none; only the PDK `sg13g2_io` cells are used | not applicable |
| Measurements | MPW/gen_structure.py | `measurements/v.1.0.0/README.md` says not run | not applicable (nothing fabricated) |

## 3. KLayout commands used

Every command ran from `${REPO}` with `G1_CPUSET=0-3`. `G1_RESULTS_ROOT=${PREP}` mounts the prep
directory into the container (KLayout 0.30.9, PDK `84374023`, image `ddeb6957…`).

```
# re-save with renamed top cell
G1_CPUSET=0-3 G1_RESULTS_ROOT=${PREP} flow/run.sh klayout -b -r ${PREP}/tools/resave_for_ihp.py \
  -rd input_file=/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds \
  -rd output_file=${PREP}/package/IHP__SoC1816/release/v.1.0.0/gds/SoC1816.gds -rd newtop=SoC1816
# geometry identity (negative control: the same with a=.../g1_chip_top_1414_r3.gds)
G1_CPUSET=0-3 G1_RESULTS_ROOT=${PREP} flow/run.sh klayout -b -r ${PREP}/tools/compare_gds.py \
  -rd a=/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds \
  -rd b=${PREP}/package/IHP__SoC1816/release/v.1.0.0/gds/SoC1816.gds \
  -rd oldtop=g1_chip_top -rd newtop=SoC1816 -rd out=${PREP}/verify/compare_r4_vs_SoC1816.json
# inspection, on the source (with -rd newtop=SoC1816 as a name-collision check) and on the release file
G1_CPUSET=0-3 G1_RESULTS_ROOT=${PREP} flow/run.sh klayout -b -r ${PREP}/tools/inspect_gds.py \
  -rd gds=${PREP}/package/IHP__SoC1816/release/v.1.0.0/gds/SoC1816.gds -rd out=${PREP}/verify/inspect_SoC1816.json
# raw GDS header, on the host
python3 ${PREP}/tools/gds_header.py <source.gds> <release.gds>
```

To make the netlist copy, `sed "13075s/^\.SUBCKT g1_chip_top /.SUBCKT SoC1816 /"` was run on the r4
CDL and one comment line was prepended. `diff` shows that only that line changed.

Results, in `release/v.1.0.0/doc/provenance/`:

| Property | Source `g1_chip_top_1414_r4.gds` | Release `SoC1816.gds` |
| --- | --- | --- |
| sha256 | `225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a` | `eb3e51a820c471a8991d23c2316c55c3c81fd47d11d4cd84d8e2081d6af4ff53` |
| bytes | 84 156 088 | 84 156 084 |
| top cell | `g1_chip_top` (only top) | `SoC1816` (only top) |
| bbox | (0,0;1414,1414) µm | (0,0;1414,1414) µm |
| dbu | 0.001 µm | 0.001 µm |
| cells / layers | 304 / 73 | 304 / 73 |
| LIBNAME / GDS version / context cell | LIB / 600 / none | LIB / 600 / none |
| BGNLIB time stamps | zero | 2026-09-28 10:12:09 (write time) |

The release file carries its write time, so every re-save gives a new sha256. The sha256 above
identifies this package.

## 4. Package tree with sha256

Package `package/` (sha256, path):

```
752d56d0405329a27a3d10dbdee8f2a27f22ba995ee096ff557776735b65db2a  IHP__SoC1816/doc/Datasheet.md
acda6e1cbad19e0fd2302ba747b05dd3a009669836b40ffff1fa779cabd308eb  IHP__SoC1816/doc/info.json
5f676f616ef649585164569b7e9793c20cb23d485305a1950dd40c707fdd848b  IHP__SoC1816/doc/Specification.md
21dd2d1bdbf9846d42c71f8ccaed54b03ecd4e607b48104d53eca79b648754a6  IHP__SoC1816/doc/TRL-Mixed-Signal-IP.md
96be8fb87512d10f0ad5c3f3a11971be1afd9b302442a765bc8acdf5e6ed3fc1  IHP__SoC1816/.github/workflows/check-workflow-sync.yml
57d9abe235472912d8b22cb855e10c64d68b06785e8b6016276ff9badb8f2a5b  IHP__SoC1816/measurements/v.1.0.0/README.md
743ef64cb765813ff8b73a9eae7b7da837bdcd427387254358953a40a57112b3  IHP__SoC1816/README.md
a8c2ba5dc78dafdbacb4dd276782865a230accc17472aaae21c29a240a481ef5  IHP__SoC1816/release/v.1.0.0/doc/bondmap_20260928_gdsr4.csv
d5088a81c9b042bd0ad403559cd45f5b8a6f4de4d5051f1ca02561b784507b93  IHP__SoC1816/release/v.1.0.0/doc/BONDPLAN_20260925.md
486396fdb2e80fde1d994c7d0f5e41d1e0d30eb0520b8aba227ab9a75cb78191  IHP__SoC1816/release/v.1.0.0/doc/bondplan_20260925.svg
93c427be1cee1f60e52bbdf80ea0007b646ff99767c706922bb117945756e681  IHP__SoC1816/release/v.1.0.0/doc/provenance/compare_gds.py
dfb12a9efcaad92428ab033a93daa7607d71b807acda17674d6fda9c36cfc17e  IHP__SoC1816/release/v.1.0.0/doc/provenance/compare_r4_vs_SoC1816.json
fc9d285d18fea478f7c36fb00d9152447472808c59eccef5054db3ef7ca2e71b  IHP__SoC1816/release/v.1.0.0/doc/provenance/control_r3_vs_SoC1816.json
7f12a62420e673a4eb2274c6cc4faa37d9a51dd6210c721a970f212f2f0c2efe  IHP__SoC1816/release/v.1.0.0/doc/provenance/gds_header.json
7fbc60f4d746e2016405dc987de32e61f8ede24893e1ca4991a8e37d5d9ec86a  IHP__SoC1816/release/v.1.0.0/doc/provenance/gds_header.py
cbdff055aef4969b6ee5b017caca779a6ffeb2e7b0db8b9e209923e1ec78f62f  IHP__SoC1816/release/v.1.0.0/doc/provenance/inspect_gds.py
05229ad9e3a1d0a671bb3e90612ba5d74606986aec26840a0d49a5d8380213c8  IHP__SoC1816/release/v.1.0.0/doc/provenance/inspect_input_r4.json
1771c7512df97e41ab3da212900008b0331925d186247494b6000b296992ba5d  IHP__SoC1816/release/v.1.0.0/doc/provenance/inspect_SoC1816.json
1563ed0d67b7de62af2770ca67f8b18b784c20e04660afd97e73c4e75ab74d6d  IHP__SoC1816/release/v.1.0.0/doc/provenance/README.md
d3a37ace72148603b7d9a236bbcc151c0980c07486980a02a1e30bc366d2960d  IHP__SoC1816/release/v.1.0.0/doc/provenance/resave_for_ihp.py
a8c2ba5dc78dafdbacb4dd276782865a230accc17472aaae21c29a240a481ef5  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/bondmap_r4chip_hashonly.csv
92624b352939bb405b9abb8b2c7b1c575c1104fd60c5c28530fefd371128a087  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/run_quick.sh
9b2fa17c26a01dbb66823604af116a9a30e091f3eb736bac87c6ceb986b8cdd0  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r3csv_on_r4.json
135a11142eb72cf34af4fdc2273d01e79a059f787fa4e6d7402b38d4c5083f09  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r3csv_on_r4.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r3csv_on_r4.log.rc
d5c26f55061e513b0b320646bdfcd371676ac371ed04d6bd1fc7527a2c3dc3d3  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r4_hashonly.json
6f8fd87ced66cd87f5a22d035ba4a5f92357f802063ffd951ffd20c84040a65b  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r4_hashonly.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/bondmap/verify_bondmap_r4_hashonly.log.rc
dd211002ca8d779dd1fc81f1f57a805d398a171a8262c5908787f88369f0cc72  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/cell_cut.py
bffec6335c0de5912419d599be0dbba4f44c2c9f02b4eb1d6bea7a2c181aa59c  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/cell_xor.py
d615ae83f42296ab31e1912738c5eb693f96700f82a3362eb8f4978ae2ce94f1  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/digital_xor_r3_r4.json
1791a83790029351895f6d2593a2fc95edfa6f02b2d5db00818d07aa81fbd83c  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/digital_xor_r3_r4.log
93ff7811a209e2a8479230bbb9b6bc19f7f311d3af383ec350c1db2a7e7d5494  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/digital_xor_r3_r4.log.rc
79ee42b8787564a5e607d9ac2a89d94aefe47449c6d142cd83ec45f1100f6acc  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/g1_digital_cut_r3.log
6b48f66102b6e04d0c899b758f94a80705adf963c7c19113da2caec12aad0b3f  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/g1_digital_cut_r4.log
369b83f49136736211cf73891aff5e494a311e8a61c012d223ee4b5d9be560f6  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/digital_identity/g1_digital_cut.sha256
6e7c6e9a624dd3cf6ec1a5bb9e0c1ce76bd9a2638a9109d3ad5fe0873a182ea6  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/gds_inventory/gds_inventory_g1_chip_top_1414_r4.json
754c79b6c065ea08620003dc7a7c4a3040c268659145bcc4cfc189ef642c7781  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/gds_inventory/gds_inventory_r4.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/gds_inventory/gds_inventory_r4.log.rc
f87022abb7f992fabdbb7c03ede9841ce35412bfb5077cbdb7ee1f9a20e31b9a  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/input_gds.sha256
b5dd697b68be257e2c85c339b46a21925f973177f3ab6e424b7ed1f2b90e1b34  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/input_gds.sha256.assembly
2216315041bf6428482efc3d7656a1ff8f55495493929beb18591ea1802760d1  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/manifest.json
34e62cd8fc1dba4241238767b2a59066407aef06baa4a484ad106135781e8b32  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_control.json
223ac64d268f1215ac370f5df0b821f9b8467945570f551dd2193ca49a438fe7  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_control.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_control.log.rc
36b86920cd0a239c0b9e6559b89a7d070e0fe46af92b6fc805f933951d804fa6  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor.json
4d5ff533eec76ec5229c7f3da6c4828f95097caf500b9e10296d6303f222e872  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor.log.rc
d4f297e7d9b29fc4b4c09458d6989daaa7dee64b983b700b73d49490acb357b0  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_prefill.json
dd9dd481d14255c7869737dada431f6c396e238225629bb1206d091e7524a3b5  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_prefill.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/chip_xor_prefill.log.rc
da3043206fea12d0110aa1cea9a7ea6d996f1a574e893cafb74c20eb7d3b6984  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/fill.json
818e2fe84f0c79b0dd19fa8252240e2931e0392e8212d193b15274739ca88e33  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/fill.log
8bfcd164b5d547df0df77f82e3709c62adab7817bbd5af4f591e7c4bead41115  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/flatten_control.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/flatten_control.log.rc
bb4c11d61c14ad6596b17104a4865c07193dc3574228831edc52fdb52872556e  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/flatten.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/flatten.log.rc
ccfbda625430bf7f4adc010ff2c5891e996dc4b3317d6e735bb796191dca6cda  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/g1_chip_top_1414_r4_projected_ref.cdl.json
0a6f1b54eadaa1d182e7dd67571508e3c1e12d1472fcf30f4d1e5c1a06183f7c  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/r4_identity/r3_projected_ref_control.cdl.json
a81ee7b077bacba607b15d35c371992a2ece97e6fe33ce3b2355a50a7f78ead5  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/README.md
c0607218830083955a759749ab6b8bd3e21c9761150a4f9c19fbce1d3293d006  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/stock_compare/stock_compare_r4.json
e7a16249af5d1249c3ebd6671f52bcc9b39b81933869e3cae5f3139442aa55bf  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/stock_compare/stock_compare_r4.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/stock_compare/stock_compare_r4.log.rc
a43bd4ac61c86b7a66427c3b2c9e144a1146391f64f530b240c903bdbf8f4f7a  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/trip_identity/trip_cand_vs_r4chip_xor.json
cd8c17f463c61206776011d95a7c70e9c0296a814eb7127379bdfb2da83a288a  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/trip_identity/trip_cand_vs_r4chip_xor.log
93ff7811a209e2a8479230bbb9b6bc19f7f311d3af383ec350c1db2a7e7d5494  IHP__SoC1816/release/v.1.0.0/doc/signoff-1414r4-20260927/trip_identity/trip_cand_vs_r4chip_xor.log.rc
eb3e51a820c471a8991d23c2316c55c3c81fd47d11d4cd84d8e2081d6af4ff53  IHP__SoC1816/release/v.1.0.0/gds/SoC1816.gds
755910c3338a0d1e68f39ed734fbe33fc80a4874847c24557c92018fc8925331  IHP__SoC1816/release/v.1.0.0/netlist/SoC1816.cdl
374222e9b5a0ca8f48d3036450b8632c4211bd60f91387ec11dcd9d109308272  IHP__SoC1816/release/v.1.0.0/ReleaseNote.md
c61c028b5d3cfe091b4471d93eddbe43f540ec5ed8f2274900d95e97f2152b5c  IHP__SoC1816/SoC1816-main/README.md
929a17824d8652a4b6b134dcf6e8fe44a84a160045a97c28c06f7456cad5f521  IHP__SoC1816/SoC1816-main/verification/drc/antenna/drc_run_2026_09_27_15_17_43.log
58db0c4b1dfcb5ebe1c61a2f6df51acd940f77a8b8fff50bd1d650bc0a9f3725  IHP__SoC1816/SoC1816-main/verification/drc/antenna/g1_chip_top_1414_r4_g1_chip_top_antenna.log
71533d82f287d01047acf8033525efa68bde620d947df9dc4c6a144f39e0acdc  IHP__SoC1816/SoC1816-main/verification/drc/antenna/g1_chip_top_1414_r4_g1_chip_top_antenna.lyrdb
d38d4cf4385a35454db3ddc472c3b41395c313a71bf3dfb79ae24181eeb99830  IHP__SoC1816/SoC1816-main/verification/drc/antenna/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/antenna/run.log.rc
a799a1d98d9933179837f577f53702e6b68b93a5c4232106589b5d9e0ae517e2  IHP__SoC1816/SoC1816-main/verification/drc/density/drc_run_2026_09_27_15_17_43.log
3e7e772121e57943a85a70c24fc3cc7551f9b8ead4ff42cf8f8314664565ca20  IHP__SoC1816/SoC1816-main/verification/drc/density/g1_chip_top_1414_r4_g1_chip_top_density.log
89149c554977898d872f4a42afb69b2db7b70940f2a21b0ec69ccef5099d4a57  IHP__SoC1816/SoC1816-main/verification/drc/density/g1_chip_top_1414_r4_g1_chip_top_density.lyrdb
e48b76620c7b5c84655fd5c9c370c9b9a61df3b0353c6ed178800fcf9e6882c2  IHP__SoC1816/SoC1816-main/verification/drc/density/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/density/run.log.rc
0fa69f5952836f13b4ca8ee09e8cb1be1ec751a3367433e51ec6f996589893e6  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/antenna/drc_run_2026_09_27_18_50_23.log
5f7786ff09bc1b17fc6fb1669451ea34c6d196f4f8b6cee216a5e3028d113513  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/antenna/g1_chip_top_1414_r4_g1_chip_top_antenna.log
4c14d560634da5df26a0445383b0e369922b59bfaec3e71aee77b9a9fc2b4002  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/antenna/g1_chip_top_1414_r4_g1_chip_top_antenna.lyrdb
6605d6ebf573ae28f060d2dc5d12c3ecb6ed7d5d2847727e8626a114a605d3fb  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/antenna/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/antenna/run.log.rc
ed009c41d17ba8406e5a042a13821b2b16c9d902cfba9be106fe03b633dd3f6f  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/density/drc_run_2026_09_27_18_50_23.log
8af1f8c131af1a09069677b510cb2325fca591e9a6871b2a44701a35447943f7  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/density/g1_chip_top_1414_r4_g1_chip_top_density.log
b62de455c398c707d003d70fe8174147280f78663b4fcba654f7bc623c3fcbbd  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/density/g1_chip_top_1414_r4_g1_chip_top_density.lyrdb
99b432cb33ce24f33c68169fa0376e61a69b53a9fa9bfdf074c2e44dfb44336e  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/density/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/density/run.log.rc
bb8645797f595ddbbb77f3a7447c0d9a85cd40a07df07a51505c7601278dd322  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_main/drc_run_2026_09_27_18_50_22.log
879d8a66d8ebc78496c2e60b4cb63f7d796b524cbb95ec0f3db15d38059733ff  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_main/g1_chip_top_1414_r4_g1_chip_top_main.log
8aab4ce0dc725560f35c6ce7217f8b40d2283ea988aed062206de8f47678e6b5  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_main/g1_chip_top_1414_r4_g1_chip_top_main.lyrdb
63b1e108b79af0ecc5aa3e41598496994a0c2c1b98520a25ed628fbd3d7a44fe  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_main/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_main/run.log.rc
00712ada6a76ee7dcf4781997d5fd401c13bb98aa00b2ae4b315e141c3df9d30  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_maximal/g1_chip_top_1414_r4_g1_chip_top_sg13g2_maximal.log
b713e2b77838f343073489a3346912f20b77b3b944f8ffce6da238acfa08a7e9  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_maximal/g1_chip_top_1414_r4_g1_chip_top_sg13g2_maximal.lyrdb
f610fcc2b56e9b9fbe544089ff1ef147733f728a3e3d79baf925a7375413a2ad  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_maximal/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/drc_maximal/run.log.rc
9ae57825a5803124ad182581b15d6b6bb41fdda38ddf6cf82da7c39b6ff47cef  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/input_gds.sha256
9ae57825a5803124ad182581b15d6b6bb41fdda38ddf6cf82da7c39b6ff47cef  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/input_gds.sha256.after
d15209667dc6495dd2c729cfcb360a616476c05b6bed3fded2e83f8d9259933a  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/drc_run_2026_09_27_18_50_23.log
d0731eb558d546e92bdcfb7a7048a0c799200474cc19baab147d05a398ad3f00  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/g1_chip_top_1414_r4_g1_chip_top_density.log
17d0383c4326c5cf1dd9032c361231a48474edfb7501419c1e36bd81ae1a9d1c  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/g1_chip_top_1414_r4_g1_chip_top_full.lyrdb
b81b112402abceffccdb01a680001ea2b8f7da30a350d0dd93f4b85bf6ee1dcd  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/g1_chip_top_1414_r4_g1_chip_top_main.log
3faf462505cfab941c6420e176e6fb23aa67e327cc9640ab4d9817940dd7ebf2  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/devdeck_check/precheck/run.log.rc
90e0cb082068281c1c5f25d3695c208a746eaeae1924a44a317d3c96b3d67cca  IHP__SoC1816/SoC1816-main/verification/drc/drc_main/drc_run_2026_09_27_15_17_43.log
2efe2f8c8a5e197945c0cff36a661bbc621dbeabbe8d38c2cb8e602f5093d83e  IHP__SoC1816/SoC1816-main/verification/drc/drc_main/g1_chip_top_1414_r4_g1_chip_top_main.log
3da5e270e1e3b93a83e39ad31033d6e80782a5d07520752d00875e6e3f9d8ce1  IHP__SoC1816/SoC1816-main/verification/drc/drc_main/g1_chip_top_1414_r4_g1_chip_top_main.lyrdb
128dbe5b0e4b960b43c90bb842aaf716d0b0f607dc3532e71d70b7c301ff24b5  IHP__SoC1816/SoC1816-main/verification/drc/drc_main/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/drc_main/run.log.rc
c744b88935aa16bf118d18349c2f636688c715ed52292c611f81cc11c5fbcba6  IHP__SoC1816/SoC1816-main/verification/drc/drc_maximal/g1_chip_top_1414_r4_g1_chip_top_sg13g2_maximal.log
f54b65a57dfe9e33c83e104e4906c904b8a8f11fd4cf69f8a1244a3e0c6e8f3e  IHP__SoC1816/SoC1816-main/verification/drc/drc_maximal/g1_chip_top_1414_r4_g1_chip_top_sg13g2_maximal.lyrdb
6e18414fc1448e4621637294da4b84571413369bb666272a0ddd6947d50b62ce  IHP__SoC1816/SoC1816-main/verification/drc/drc_maximal/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/drc_maximal/run.log.rc
c3bf747a10341896cc89dbea546aef2304892936ddcfc2afc171d5cf0fe1e853  IHP__SoC1816/SoC1816-main/verification/drc/precheck/drc_run_2026_09_27_15_17_44.log
d0853ec1f6834f847753484aaf413d7d66d821d1d315e2b9b56d31b2af0ebb1f  IHP__SoC1816/SoC1816-main/verification/drc/precheck/g1_chip_top_1414_r4_g1_chip_top_density.log
92416e926f5c2deb63753403fd2b5fb07d77652ea62771083222ba8c7c3cf477  IHP__SoC1816/SoC1816-main/verification/drc/precheck/g1_chip_top_1414_r4_g1_chip_top_full.lyrdb
e86cff9669eecf19be55c823f04691f2ffea6d7fc91a25637711c68305dcf5a2  IHP__SoC1816/SoC1816-main/verification/drc/precheck/g1_chip_top_1414_r4_g1_chip_top_main.log
e2e7b8b3600a66eb5436229da2e64af1c9416ccc73acdcd476f28d2af10f4d0e  IHP__SoC1816/SoC1816-main/verification/drc/precheck/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/drc/precheck/run.log.rc
20692b27c95711cd607dc6ef507ef8a935bc1d57137be98222c65a531a82b48b  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_canonical/g1_chip_top_1414_r4.log
b6fd9ca2ae2beb07832d45434183efc9cb1bb7b15adf444dc5feb42bb04396ba  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_canonical/lvs_run_2026_09_27_15_17_43.log
7fa0048b13bc6fdad510e24a21160e38a48f80e2433480f168954b8d2fb95a12  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_canonical/pair_counts.json
f71611bb8d9843bed447714fb08e05a186ae89ecbab818268efd87324d390821  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_canonical/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_canonical/run.log.rc
4a522271d7e641f7f5d00ceb245bc3dd7914945bad619fd964a9fb7391300614  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_projected/g1_chip_top_1414_r4.log
9003a38be9b22a40d35fd206e1fee92581e05ac77775928111355d1e5914ab23  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_projected/lvs_run_2026_09_27_15_17_44.log
825a9163a6f6501696a7de50c42ad841d77245d49a77fe371ab0c0cc09d9de5e  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_projected/pair_counts.json
7eeec88d523f17249428952e4430b1e67052351361b17495140dbfa478856402  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_projected/run.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  IHP__SoC1816/SoC1816-main/verification/lvs/lvs_projected/run.log.rc
```

Empty generated directories (kept, not tracked by git):

```
IHP__SoC1816/dependencies
IHP__SoC1816/SoC1816-main/layout/def
IHP__SoC1816/SoC1816-main/layout/klayout
IHP__SoC1816/SoC1816-main/layout/lef
IHP__SoC1816/SoC1816-main/layout/magic
IHP__SoC1816/SoC1816-main/model/spice
IHP__SoC1816/SoC1816-main/model/verilog-A
IHP__SoC1816/SoC1816-main/netlist/layout
IHP__SoC1816/SoC1816-main/netlist/pex
IHP__SoC1816/SoC1816-main/netlist/rcx
IHP__SoC1816/SoC1816-main/netlist/schematic
IHP__SoC1816/SoC1816-main/schematic/qucs-s
IHP__SoC1816/SoC1816-main/schematic/xschem
IHP__SoC1816/SoC1816-main/testbenches/ac/qucs-s
IHP__SoC1816/SoC1816-main/testbenches/ac/xschem
IHP__SoC1816/SoC1816-main/testbenches/corners/qucs-s
IHP__SoC1816/SoC1816-main/testbenches/corners/xschem
IHP__SoC1816/SoC1816-main/testbenches/noise/qucs-s
IHP__SoC1816/SoC1816-main/testbenches/noise/xschem
IHP__SoC1816/SoC1816-main/testbenches/tran/qucs-s
IHP__SoC1816/SoC1816-main/testbenches/tran/xschem
IHP__SoC1816/SoC1816-main/timing
```

Tools and verification outputs outside the package (`tools/`, `verify/`; copies of both are in `release/v.1.0.0/doc/provenance/`):

```
93c427be1cee1f60e52bbdf80ea0007b646ff99767c706922bb117945756e681  tools/compare_gds.py
7fbc60f4d746e2016405dc987de32e61f8ede24893e1ca4991a8e37d5d9ec86a  tools/gds_header.py
cbdff055aef4969b6ee5b017caca779a6ffeb2e7b0db8b9e209923e1ec78f62f  tools/inspect_gds.py
d3a37ace72148603b7d9a236bbcc151c0980c07486980a02a1e30bc366d2960d  tools/resave_for_ihp.py
dfb12a9efcaad92428ab033a93daa7607d71b807acda17674d6fda9c36cfc17e  verify/compare_r4_vs_SoC1816.json
fc9d285d18fea478f7c36fb00d9152447472808c59eccef5054db3ef7ca2e71b  verify/control_r3_vs_SoC1816.json
7f12a62420e673a4eb2274c6cc4faa37d9a51dd6210c721a970f212f2f0c2efe  verify/gds_header.json
05229ad9e3a1d0a671bb3e90612ba5d74606986aec26840a0d49a5d8380213c8  verify/inspect_input_r4.json
1771c7512df97e41ab3da212900008b0331925d186247494b6000b296992ba5d  verify/inspect_SoC1816.json
```

## 5. Remaining human steps

**Done 2026-09-28 (owner instruction to finish the submission):** step 1 (`trl` 5, category `SoC`, ID 1816
kept), step 3 (repository created and pushed, GDS as a plain 84 MB file, GitHub raw download verified
sha256 `eb3e51a8…`), step 5 (issues/68 opened; the run is `Oct-2026`; the questions of step 2 are in the
issue text). Step 4 done on our side 2026-09-28: the stock DRC decks (main, maximal, density, precheck, antenna) were re-run on `SoC1816.gds` itself, 0 markers each (`IHP__SoC1816/SoC1816-main/verification/drc_release_20260928/`). Still open: IHP's own DRC and step 6 (record IHP's answer).
The original list follows unchanged.

1. **Decide and fill the TODOs:** `info.json` `trl` (an integer, self-assessed with
   `doc/TRL-Mixed-Signal-IP.md`), and confirm the category (`SoC`) and the ID 1816. Choosing a
   different ID means renaming the top cell and the files again and re-running §3.
2. **Ask IHP** (on the request issue) about:
   - the run name and the deadline. The repository states neither; the design repository has an
     unreconciled "end of September" against "21 October" (`TAPEIN_PACKAGE_20260924.md` §8.7);
   - whether a 1414 µm die with its own `sg13g2_io` ring and QFN24 is accepted, given that
     MPW/Packaging.md documents only QFN64 on an 18 mm² padframe;
   - the value of `process` (`SG13G2` against the default `SG13CMOS`) and the unit of `sealring_x/y`;
   - whether the projected-reference LVS is accepted (canonical LVS fails on the PDK IO cells);
   - the remaining questions in `TAPEIN_PACKAGE_20260924.md` §8 (Ant.e on `sg13g2_IOPadIn`,
     PolyRes on the IO copies, no DigiBnd, keeping the text and pin layers).
3. **Create the repository** `https://github.com/simra-tech/IHP__SoC1816` (the name is already in
   `info.json` `repository`). Copy `package/IHP__SoC1816/` into it, then commit and push it (a
   human pushes). The 84 MB GDS is under GitHub's 100 MB hard limit but over its 50 MB warning.
   Git LFS would break IHP's raw-file access, so commit it as a plain file (or ask IHP whether
   `.gds.gz` is preferred; RFID4410 used it, and a gzip copy must then replace the `.gds` so that
   only one GDS remains).
4. **Let IHP's workflows run**, or run the IHP-Open-PDK KLayout DRC with the precheck on
   `SoC1816.gds`. DRC on the renamed file itself is **not run** here; the geometry identity was
   proven instead.
5. **Open the request issue** on https://github.com/IHP-GmbH/Open-Silicon-MPW (do not fork). Draft:

```
Title: Request for submission <MPW-run, e.g. Oct-2026> IHP__SoC1816

## Submodule request for <MPW-run> Open-Silicon MPW

- Repository URL: https://github.com/simra-tech/IHP__SoC1816.git
- Category directory: <MPW-run>/Mixed-Signal
- Submodule path: <MPW-run>/Mixed-Signal/IHP__SoC1816

### .gitmodules snippet

[submodule "<MPW-run>/Mixed-Signal/IHP__SoC1816"]
  path = <MPW-run>/Mixed-Signal/IHP__SoC1816
  url = https://github.com/simra-tech/IHP__SoC1816.git
```

6. **After IHP responds**, record in the design repository the IHP intake result (pass or fail,
   and the date) on the release sha256 `eb3e51a8…`.
