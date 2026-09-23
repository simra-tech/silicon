# Isolated OSC R0.95 physical candidate, 2026-09-24

This is a simulated/design-check candidate, not a production macro or chip adoption. The four RA/RB PolyRes segments are 55.575 µm rather than 58.5 µm. The original generator, delivered macro and old-PEX simulation evidence remain unchanged. IHP SG13G2 public PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, EDA image config digest `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, one assigned CPU; stock rule/model sources were not edited.

| Check on isolated candidate | Status | Saved result |
|---|---|---|
| Scoped four-body geometry, external pin polygons and boundary | passed | `geometry.json`; bare GDS SHA `411d52f74d0515895b4616b37af466f65481419ff0137ddc16970107851c6827` |
| Bare stock deep main/maximal DRC; antenna | passed | Zero markers in each deck |
| Bare native-device strict-port stock LVS | passed | Explicit `Netlists match`; 81-device comparison CDL SHA `b5bdd5549f645dc265743600b93ade50eaa9f49362def58b512131470dea7e1b` |
| PDK macro fill, then filled stock deep main/maximal DRC and antenna | passed | Filled GDS SHA `960a9e9a2f2e60e10757c707e6ddc51aa3f9937335cdae6d50926c2808e24cc6`; zero markers |
| Filled native-device strict-port stock LVS | passed | Explicit `Netlists match`, missing/mislabeled top ports treated as errors |
| Isolated filled-macro stock density-only | failed | Eight markers: `AFil.g`, `M1.j`–`M5.j`, `TM1.c`, `TM2.c`. Deck used the macro bbox as the density-window origin; chip-context density remains not run for this candidate. No density rule was waived. |
| New KLayout-PEX 0.3.12, 2.5D `CC` | passed extraction; limited model | Converted CPEX SHA `8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5`; 609 positive extracted wire capacitors. Exact decimal parameter and 53-net terminal-bijection audit passes all 81 native devices: 51 MOS, 18 resistors, 1 antenna diode and 11 reinserted MIM capacitors (`pex_native_audit.json`). |
| KPEX internal LVS of MIM-stripped, no-simplify PEX input | failed | Retained internal `Netlists don't match`; it is not substituted for the separate filled-GDS stock LVS pass. |
| Current full-chip OSC-cell comparison | passed scoped comparison | `macro_vs_current_chip.json`: only baseline fill on layers 50/22 and 67/22 and four internal 50/25 annotations differ; all other recursive nontext geometry, external labels and bbox match. New cell integration has not run. |
| New-source nine-case mismatch qualification | passed limited source control | Independent run `osc_r095_newpex_qual_20260924_r1`: 9/9 cases, zero timeout/failure/missing, all 12 inherited repeat/freeze/seed/disabled/device-class checks true. Analysis SHA `30afe1a9198a481cf401fd510fbdd810d42edfdcb5dde66d82d915161f3d93d9`. This does not reuse prior old-PEX population results. |
| New-source population/PVT, integrated physical replacement, new chip density, wire-R/MIM-plate/fill-coupling PEX, silicon measurement | not run | No adoption or yield claim. |

The PDK macro filler uses a temporary EdgeSeal ring and `no_topmetal`; its seven datatype-22 shape counts are: Active 557, Poly 557, Metal1 725, Metal2 622, Metal3 424, Metal4 290, Metal5 290. The capacitance-only PEX input deliberately strips MIM/upper-plate layers and floating fill because the pinned kpex technology cannot model MIM plates; the unchanged converter re-inserts 11 ideal PDK MIM devices. Wire resistance and MIM plate/fill coupling are not extracted. The separate exact-parameter/native-net audit checks this converted source, not RC accuracy or silicon performance.

Bulk GDS, tool databases, logs, and extracted netlists remain outside Git under an operator-selected results root. `bulk_manifest.json` names their relative paths, byte lengths and SHA-256. No command below changes the delivered macro.

## Reproduction commands

Run from the repository root with the public PDK commit above, ngspice 46, KLayout 0.30.9 and KLayout-PEX 0.3.12. Select a fresh external `BULK_ROOT` and an allocated `ASSIGNED_CPU`; the required resource gate and CPU lease are separate admission controls and must pass before invoking the tools. The original simulated R0.95 source is the pinned `sim/qualification/runs/osc_r095_candidate_shard0_20260921_01/osc.spice` (SHA `f08bf0517066736fa0a4763b0a7a380d06a7b670730239d1be05a21133f4d319`).

```sh
export RESULTS_ROOT="$BULK_ROOT/osc-r095-physical-20260924-r1"
export G1_RESULTS_ROOT="$BULK_ROOT" G1_CPUSET="$ASSIGNED_CPU" G1_CPUS=1 G1_MEMORY=4g
export G1_EDA_IMAGE=tapeoutbench-eda:latest G1_EXPECTED_IMAGE_ID=sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2
export G1_EDA_PLATFORM=linux/amd64 G1_CONTAINER_ENGINE=podman
mkdir -p "$RESULTS_ROOT/pex_cc_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh klayout -b -r gen_osc_r095_candidate.py -rd out="$RESULTS_ROOT/osc_r095.gds"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh klayout -b -r audit_osc_r095_geometry.py -rd baseline=g1_osc.gds -rd candidate="$RESULTS_ROOT/osc_r095.gds" -rd report="$RESULTS_ROOT/geometry.json"
python3 designs/g1-guardian/blocks/g1_osc/layout/prepare_osc_r095_lvs.py designs/g1-guardian/blocks/g1_osc/sim/qualification/runs/osc_r095_candidate_shard0_20260921_01/osc.spice "$RESULTS_ROOT/osc_r095.cdl"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path="$RESULTS_ROOT/osc_r095.gds" --topcell=g1_osc --run_mode=deep --no_density --mp=1 --run_dir="$RESULTS_ROOT/drc_main_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path="$RESULTS_ROOT/osc_r095.gds" --topcell=g1_osc --run_mode=deep --antenna_only --mp=1 --run_dir="$RESULTS_ROOT/antenna_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout="$RESULTS_ROOT/osc_r095.gds" --netlist="$RESULTS_ROOT/osc_r095.cdl" --topcell=g1_osc --run_mode=deep --run_dir="$RESULTS_ROOT/lvs_native_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh bash fill_macro.sh "$RESULTS_ROOT/osc_r095.gds" "$RESULTS_ROOT/osc_r095_filled.gds" 3.0
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path="$RESULTS_ROOT/osc_r095_filled.gds" --topcell=g1_osc --run_mode=deep --no_density --mp=1 --run_dir="$RESULTS_ROOT/drc_filled_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path="$RESULTS_ROOT/osc_r095_filled.gds" --topcell=g1_osc --run_mode=deep --density_only --density_thr=1 --mp=1 --run_dir="$RESULTS_ROOT/density_filled_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path="$RESULTS_ROOT/osc_r095_filled.gds" --topcell=g1_osc --run_mode=deep --antenna_only --mp=1 --run_dir="$RESULTS_ROOT/antenna_filled_r1"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py --layout="$RESULTS_ROOT/osc_r095_filled.gds" --netlist="$RESULTS_ROOT/osc_r095.cdl" --topcell=g1_osc --run_mode=deep --run_dir="$RESULTS_ROOT/lvs_filled_r1"
cp "$RESULTS_ROOT/osc_r095_pexlabels.txt" "$RESULTS_ROOT/osc_r095_filled_pexlabels.txt"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh klayout -b -r pex_input.py -rd gds="$RESULTS_ROOT/osc_r095_filled.gds" -rd out="$RESULTS_ROOT/pex_cc_r1/osc_r095_pexin.gds"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh kpex --pdk ihp_sg13g2 --gds "$RESULTS_ROOT/pex_cc_r1/osc_r095_pexin.gds" --cell g1_osc --schematic "$RESULTS_ROOT/osc_r095.cdl" --2.5D --mode CC --out_dir "$RESULTS_ROOT/pex_cc_r1/extract"
python3 designs/g1-guardian/blocks/g1_osc/sim/postlayout/make_pex_netlist.py osc "$RESULTS_ROOT/pex_cc_r1/extract/osc_r095_pexin__g1_osc/g1_osc_k25d_pex_netlist.spice" "$RESULTS_ROOT/pex_cc_r1/osc_r095_pex.spice"
python3 designs/g1-guardian/blocks/g1_osc/layout/audit_osc_r095_pex_native.py --native "$RESULTS_ROOT/osc_r095.cdl" --pex "$RESULTS_ROOT/pex_cc_r1/osc_r095_pex.spice" --report "$RESULTS_ROOT/pex_cc_r1/native_audit.json"
G1_WORKDIR=. flow/run.sh klayout -b -r designs/g1-guardian/blocks/g1_osc/layout/compare_osc_macro_cell_r095.py -rd baseline=designs/g1-guardian/blocks/g1_osc/layout/g1_osc.gds -rd chip="$CURRENT_CHIP_GDS" -rd out="$RESULTS_ROOT/macro_baseline_vs_current_chip.json"
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/sim/qualification flow/run.sh python3 run_mc_newpex.py --run-id NEW_UNIQUE_ID --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --suite qualify --first-seed 63401 --tuple nominal --pex-source "$RESULTS_ROOT/pex_cc_r1/osc_r095_pex.spice" --pex-sha256 8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5
python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/analyze_mc.py NEW_UNIQUE_ID
```

`CURRENT_CHIP_GDS` is the hash-bound retained current-chip candidate SHA `3e3634389aff5126d0f55f6814466ad179f6d1280e9152c62a07ab5ea3d105bf` for the recorded comparison. The stock density failure and kpex internal comparison failure must remain visible; a successful command exit does not override their saved rule/comparison reports. Full-chip macro replacement, chip density, new-source population/PVT and all silicon measurement remain not run.
