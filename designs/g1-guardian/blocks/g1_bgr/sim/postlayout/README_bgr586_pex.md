# bgr586 capacitance PEX (kpex 2.5D) — 2026-09-24

Post-layout view of the bandgap that is physically on the frozen chip,
`bgr_loop24_qref4_r253p465_hv06` (source 586: 336 HV MOS, 301 `npn13G2`, 399 resistors —
384 `rppd` + 15 `rhigh`). It replaces nothing: `g1_bgr_pex.spice` (Sep-19 layout) is kept.

## Inputs

| Item | Path (block-relative) | sha256 |
| --- | --- | --- |
| Layout, top cell `g1_bgr` | `layout/coordinated_supply_followup_20260923/evidence/supply-20260923-r1/candidate/bank.gds` | `e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb` |
| LVS reference | `.../candidate/bank.cdl` | `7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2` |
| Schematic-level netlist 586 | `sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice` | `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |

Built against: pinned image `tapeoutbench-eda:latest` (`sha256:ddeb6957…`, checked by `flow/run.sh`),
PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9 (LVS log), kpex 0.3.12
(`kpex --version`, `reports/pex/cc_bgr586_20260924/kpex_console.log`), ngspice 46 (log banner).
Paths under the results directory are written `<results-root>` in the saved logs.

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| PDK block LVS, `bank.gds` vs `bank.cdl` | **passed** ("Congratulations! Netlists match.", run time 10.5 s) | `reports/lvs_bgr586_20260924/` |
| kpex internal LVS (kpex's own deck, same CDL) | **passed** ("Netlists match.") | `reports/pex/cc_bgr586_20260924/kpex_lvs.log` |
| kpex 2.5D `--mode CC` extraction | **run**, rc 0, 2158 s wall on one CPU | `reports/pex/cc_bgr586_20260924/` |
| Extracted device list vs source 586 | **passed**: multiset of (model, all instance parameters) identical, 1036 = 1036 | this README |
| DC operating point 27 °C, tt 3.3 V | **passed** (converged, compared below) | `bgr586/ngspice_pex.log` |
| V<sub>REF</sub> temperature sweep −40…125 °C | **passed** (compared below) | `bgr586/results_bgr586_pex.csv` |
| AC / PSRR / noise / start-up transient on this netlist | **not run** | — |
| Process, supply corners and mismatch on this netlist | **not run** | — |
| Wiring resistance (kpex RC) | **not run** (kpex 0.3.12 RC mode unusable here, see `make_pex_netlist.py`) | — |

Commands (repository root; `<E>` = the candidate directory above, `<R>` = results dir):

```
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py \
    --layout=/work/<E>/bank.gds --netlist=/work/<E>/bank.cdl --topcell=g1_bgr --run_mode=deep --run_dir=<R>/lvs/run
flow/run.sh kpex --pdk ihp_sg13g2 --gds /work/<E>/bank.gds --cell g1_bgr \
    --schematic /work/<E>/bank.cdl --2.5D --mode CC --out_dir <R>/kpex/out
python3 sim/postlayout/make_pex_netlist.py reports/pex/cc_bgr586_20260924/g1_bgr_k25d_pex_netlist.spice \
    sim/postlayout/g1_bgr586_pex.spice      # then header comment lines 1 and 3 edited to name bank.gds
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim/postlayout/bgr586 flow/run.sh ngspice -b tb_pex.cir   # and tb_sch.cir
```

LVS options are those of the block's Sep-19 LVS (`--topcell --run_mode=deep`, see `../../README.md`
"Commands"); the Sep-23 stock run of the same files additionally used `--top_lvl_pins --spice_comments`
and also passed. kpex options are those of `reports/pex/cc/kpex_plain.log` (Sep-19): same engine, mode,
PDK, with the LVS CDL as schematic. The Sep-19 kpex internal LVS reported "Netlists don't match";
this one matches.

## Netlist

`g1_bgr586_pex.spice`, sha256 `01227a3d8d8210d10d2d1ee6933842351140b8825fe29282f0327936a3064ad5`
(raw kpex netlist `reports/pex/cc_bgr586_20260924/g1_bgr_k25d_pex_netlist.spice`, sha256 `e1b4677e…`).
Subcircuit `g1_bgr vdd vss r4 vref iptat pbias pcasc vbe dvbe` — same name and pin order as 586 and as
`bank.cdl`. kpex writes the ports alphabetically; `make_pex_netlist.py` rewrites the `.subckt` line
in the schematic order (ports are bound by name inside the body), so **no wrapper subckt is needed** and
the file is a drop-in for `.include` of 586 in a chip deck. Contents: 336 XM, 301 XQ, 399 XR, 978
capacitors (the 979th, 1.40 pF VSUBS–vss, disappears because the substrate is mapped to vss), 10.10 pF
in total, 177.1 fF on `vref`. Source 586 carries the 329 historical Sep-19-layout capacitances
(399.7 fF, 17.5 fF on `vref`); the physical layout's parasitics are therefore about 25× larger.
Same 2.5D limitation as before: no well conductor, so capacitances over n-wells are referenced to vss.

## Simulation comparison (simulated; nominal hbt_typ / mos_tt / res_typ, 3.3 V)

Fixture: `sim/qualification/runs/bgr_one_draw_20260922_r1/disabled/nominal.cir` (1 pF on VREF, ideal
1 V IPTAT termination, same options and `.spiceinit`), mismatch-parameter prints removed, `dc temp`
step 1 °C; decks `bgr586/tb_sch.cir`, `bgr586/tb_pex.cir`. TC = box over the 5 °C grid / V(25 °C) / 165
(qualification definition). Control: the schematic deck reproduces the qualified reference
(V<sub>REF</sub>(25 °C) 1.04544958 V, TC 8.529823 ppm/°C) within 0.4 nV on all 34 points.

| quantity | schematic 586 | PEX bgr586 | delta | status |
| --- | --- | --- | --- | --- |
| V_REF op 27 °C | 1.04546022 V | 1.04546022 V | +0.1 nV | passed |
| I_PTAT op 27 °C | 4.134131 µA | 4.134131 µA | < 1 fA | passed |
| supply current op 27 °C | 319.692 µA | 319.692 µA | < 1 pA | passed |
| V_REF −40 °C | 1.04403047 V | 1.04403047 V | +0.2 nV | passed |
| V_REF 27 °C | 1.04546022 V | 1.04546022 V | −0.2 nV | passed |
| V_REF 125 °C | 1.04401335 V | 1.04401335 V | −0.1 nV | passed |
| TC −40…125 °C | 8.529823 ppm/°C | 8.529823 ppm/°C | < 1e-7 | passed |

Reading: DC and TC are identical because the extracted device geometry is identical to 586 (which was
itself built from extracted device geometry) and capacitors do not enter DC. The extraction therefore
confirms 586's device view against the physical layout; what it adds are the 10.1 pF of real parasitics,
which matter only for AC, PSRR, noise and start-up — all **not run** on this netlist. Wiring
resistance remains unextracted. Runtime: ngspice 90 s wall (PEX deck) including container start.
