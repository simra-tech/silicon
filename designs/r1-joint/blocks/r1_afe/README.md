# r1_afe — encoder analog front end (sine and cosine channels)

State (2026-10-21): **revision E, layout revision E2 (re-route): DRC, antenna and LVS clean (PDK decks); P/N pairs balanced (≤ 3.4 fF); full RC extraction and post-layout campaign run. Open: CM1/CM2 phase margins at ffx 61.3°/57.7° (target 63°), output CM +31 mV from supply resistance, ×32 settling offset −0.41 mV, two bias-range failures (see "Layout (revision E2)").** The revision-E layout record follows it. Schematic-level record: "Revision E" below.
Revision D is superseded by revision E (record below). Revision C is superseded; its record follows the revision-D section ("Revision C record"). Revision B is superseded; its
record is kept at the end ("Revision B record").
All numbers in this file are **simulated** unless they are marked estimated. Nothing is measured.

Track T3 of `../README.md`. Specification row: `../../specification/R1_TOP_LEVEL_SPECIFICATION.md` §2 (`r1_afe`),
§4 (encoder input), gate V1. Input standard and accuracy budget: `../../specification/studies/S1_ENCODER_CHAIN_20261020.md`.

## Layout (revision E2, 2026-10-21, track T3)

Layout revision E2 is a re-route of the revision-E layout. The schematic netlist of record does not change
(`schematic/r1_afe.spice`, revision E, sha256 `4a84a3d8…9e46`). The placement does not change. The changes are:
1. P/N pairs are routed first, with a halo cost, and the shorter net gets trim stubs on Metal3/Metal4.
2. The supply nets are widened, and two Metal5 straps (`vss`, `vdd`, 4.8 µm) feed the channels from the south pins.
3. The CM-sense nets (`xa1_vcms`, `xa2_vcms`) are routed first and are shorter.
4. The CS caps have the bottom plate on the OTA output (MIM plate orientation; see "LVS reference").

All post-layout numbers are **simulated**. Nothing is measured.

### Files (revision E2)

| Path | Content |
| --- | --- |
| `layout/r1_afe.gds` | layout of record, revision E2 (sha256 `fb3d6a3b…6a03`, 3.9 MB, top cell `r1_afe`) |
| `layout/r1_afe_revE.gds` | revision-E layout, kept for comparison (sha256 `0181e988…91e1`) |
| `layout/r1_afe_lvs.cdl` | LVS reference (sha256 `dc1b5e28…0652`): revision E with unit split and plate orientation |
| `layout/r1_afe_trim_e2.json` | trim stubs from the dev10 extraction (input of the generator, `-rd trim=`) |
| `layout/r1_afe_layout.json`, `layout/r1_afe_ports.json` | router statistics, pair lengths before/after trim; device-terminal ports for the RC build |
| `layout/r1_afe_layout.py`, `layout/maze_router.py`, `layout/r1_afe_netlist.py` | generator, router (priority nets, halo, stubs, widening), netlist flattener |
| `layout/tools/pin_layer_check.py` | pin set and layer check against `r1_afe_revE.gds` |
| `pex/run_pex.sh` | kpex of the channel cell and of the top cell without channels |
| `pex/pex_prepare.py` | flat GDS for kpex; mode `top_only` adds a dummy gate at each channel pin |
| `pex/pex_rc_build.py`, `pex/klrun.py` | wire and via resistance (KLayout `RNetExtractor`) plus kpex capacitance into one RC netlist |
| `pex/pair_loads.py`, `pex/rnet_report.py` | per-net capacitance of the pairs; supply resistance per port |
| `schematic/r1_afe_revF_candidate.spice` | revision-F candidate (MIM sizes only). **Not the netlist of record. It does not pass** (see below) |
| `sim/run_afe.py` | new campaigns `post2`, `postbias`, `postcm`, `poststb:<v>`, `postac:<v>`; parameter `IB` (bias current) |
| `reports/layout-e2-dev11/` | DRC, antenna and LVS logs, `run.json`, `pin_layer_check.json` |
| `reports/pex-e2-dev11/` | extraction `run.json`, `pair_loads.json`, `rnet_supply.json`, `pex_rc_report.json` |
| `reports/post-e2.json` | pre/post reduction (`sim/compare_post.py`) |
| `reports/layout-e2-dev1/` … `layout-e2-dev10/` | development check logs |

Reproduce (repository root). Set `G1_CPUSET=106-108; export G1_CPUSET` and `G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`. Then:
1. Set `G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout; export G1_WORKDIR`.
2. Run `flow/run.sh klayout -b -r r1_afe_layout.py -rd trim=r1_afe_trim_e2.json -rd out=<dir>/r1_afe.gds` (about 330 s).
3. Run `flow/run.sh sh run_checks.sh <run-id> all <dir>/r1_afe.gds`.
4. Run `sh designs/r1-joint/blocks/r1_afe/pex/run_pex.sh <abs dir> <abs gds>` (about 40 min).
5. Run the RC build and the campaigns with the commands in `reports/pex-e2-dev11/run.json` and `sim/runs/r1afe-*-e2-*/run.json`.

### Built against (revision E2)

| Item | Version | How established |
| --- | --- | --- |
| IHP SG13G2 open PDK | commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` compares `/foss/pdks/ihp-sg13g2/COMMIT` before every command; in each `run.json` |
| KLayout (layout, DRC, LVS, antenna, `klayout.pex`) | 0.30.9 | `reports/layout-e2-dev11/run.json` |
| kpex (klayout-pex) | 0.3.12 | `reports/pex-e2-dev11/run.json` |
| ngspice | ngspice-46 | `sim/runs/r1afe-post2-e2-rc/run.json` |
| Container image | `sha256:ddeb6957…bab2` | verified by `flow/run.sh` |
| CPU set | `G1_CPUSET=106-108` | command lines in the run records |

### Status (revision E2; run ids `layout-e2-dev11`, `pex-e2-dev11`, `r1afe-post2-e2-rc`, `r1afe-postbias-e2-rc`, `r1afe-postcm-e2-rc`)

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| DRC, PDK deck, main + maximal rule set | 0 violations | **passed**: 0 | `reports/layout-e2-dev11/drc.log` |
| DRC density | block level | **not run** (waived at block level, as revision E) | — |
| Antenna, PDK deck | 0 violations | **passed**: 0 | `reports/layout-e2-dev11/antenna.log` |
| LVS against `layout/r1_afe_lvs.cdl` | match | **passed**: `r1_afe` nets 63/63, devices 46/46; `r1_afe_ch` nets 143/143, devices 241/241 | `reports/layout-e2-dev11/lvs_summary.txt` |
| Pins | same pins as revision E | **passed**: 21 Metal3 pins; pin set (label, box) equal to `r1_afe_revE.gds` | `reports/layout-e2-dev11/pin_layer_check.json` |
| Bounding box | ≤ 192.8 × 494.4 µm | **passed**: 192.8 × 494.4 µm | same |
| TopMetal1 only on MIM plates; no TopMetal2 | — | **passed**: TopMetal2 area 0; TopMetal1 29 257 µm², all within 5 µm of a MIM (plates and 1.6 µm tabs), same as revision E. Metal5 adds the two supply straps | same |
| Reproduction of the GDS | same layout from the same inputs | **passed**: regenerated with `-rd trim=r1_afe_trim_e2.json`; KLayout `LayoutDiff` identical (file hash differs by the GDS time stamp); `r1_afe_ports.json` byte-identical | `<G1_RESULTS_ROOT>/r1_afe/layout-e2-repro/ldiff.out` |
| P/N pair imbalance, extracted | ≤ 5 fF per pair | **passed**: worst 3.4 fF (`op2`/`on2`) | `reports/pex-e2-dev11/pair_loads.json` |
| Full RC extraction (channel + top level, R and C) | completes | **passed**: channel 3192 C, 979 R; top 229 C, 58 R | `reports/pex-e2-dev11/run.json` |
| CM1/CM2 phase margin at ffx, post-layout | ≥ 60° + 3° allowance | **failed**: CM1 61.3°, CM2 57.7° | table below |
| CM2 stability, transient CM step, tt and ffx | settles, no growing oscillation | **passed** (ripple: open issue 8) | `sim/runs/r1afe-postcm-e2-rc/run.json` |
| Revision-F MIM candidate | CM1/CM2 ≥ 63° at ffx, other limits kept | **failed**: CM margins reached, f_c at ss 0.981 MHz < 1.0 MHz | "Revision-F candidate" below |
| Post-layout campaign `post2` | runs complete | **37 jobs, 4 failed** (settling decks, "timestep too small"; one stopped after 75 min) | `sim/runs/r1afe-post2-e2-rc/run.json` |
| Bias range (`r1_bias` PTAT current) | per value, below | **2 values fail** (see "Bias range") | `sim/runs/r1afe-postbias-e2-rc/run.json` |
| EM/IR sign-off | — | **not run** (supply R is extracted; currents not checked against EM rules) | — |
| LEF / abstract, fill | — | **not run** | — |

### Pair loads (kpex 2.5D CC, fF; P / N, difference P − N)

| Net pair | Revision E | Revision E2 |
| --- | --- | --- |
| `outp`/`outn` (stage-2 OTA output) | 73.9 / 132.8 (−59.0) | 115.7 / 119.0 (−3.3) |
| `op2`/`on2` | 180.2 / 187.4 (−7.2) | 205.3 / 208.8 (−3.4) |
| `m1p`/`m1n` (stage-1 outputs) | 251.7 / 246.7 (+5.0) | 287.6 / 286.4 (+1.3) |
| `x1p`/`x1n` (OTA1 inputs) | 209.5 / 220.0 (−10.5) | 225.0 / 224.5 (+0.6) |
| `x2p`/`x2n` (OTA2 inputs) | 117.0 / 129.2 (−12.2) | 136.4 / 137.0 (−0.7) |
| `inp`/`inn` | 18.3 / 21.3 (−3.0) | 23.1 / 23.5 (−0.4) |
| top level `souts_p`/`souts_n` | not extracted | 19.9 / 20.2 (−0.3) |
| top level `soutc_p`/`soutc_n` | not extracted | 55.3 / 53.9 (+1.3) |
| top level `sinp`/`sinn`, `cosp`/`cosn` | not extracted | 0.9 / 0.9 each |
| CM sense `xa1_vcms`, `xa2_vcms` | 117.0, 72.5 | 49.7, 53.9 |
| CM feedback `xa1_vcmfb`, `xa2_vcmfb` | 54.8, 50.6 | 51.9, 50.6 |
| Channel total | 3712.1 | 3819.8 |

The channel values are for one channel cell. Both channels use the same cell.

### Pre-layout vs post-layout (simulated; tt = 3.3 V, 27 °C; ss = 3.0 V, 125 °C; ff = 3.6 V, −40 °C; ffx = ff, 3.0 V, 125 °C; bias 10 µA ideal)

Columns: **schematic** = netlist of record (`r1afe-post-20261021e-sch`; ss, ff and THD rows from `r1afe-ac-20261021e`,
`r1afe-ac_mc-20261021e`, `r1afe-tran-20261021e`). **E post** = revision-E layout, channel capacitance only
(`r1afe-post-20261021e-pex`). **E2 post** = revision E2, full RC (`r1afe-post2-e2-rc`). Loop margins are the worst
over ×1 and ×32 and input CM 0.5 and 2.5 V. Reduction: `reports/post-e2.json`.

| Quantity | Limit | Schematic | E post | E2 post | Status (E2) |
| --- | --- | --- | --- | --- | --- |
| f_c min over steps, tt | ≥ 1.0 MHz | 1.280 MHz | 1.292 MHz | 1.281 MHz | **passed** |
| f_c min over steps, ss | ≥ 1.0 MHz | 1.017 MHz | not run | 1.015 MHz | **passed** (margin 1.5 %) |
| f_c min, ff (E2: CM 2.5 V only) | ≥ 1.0 MHz | 1.645 MHz | not run | 1.877 MHz | passed |
| Pole matching, worst \|Δf3\| (σ), 20 MC × 6 steps, tt | ≤ 1 % | 0.563 % (0.232 %) | 0.716 % (0.228 %) | 0.645 % (0.233 %) | **passed** |
| Pole matching, ss | ≤ 1 % | 0.977 % (0.252 %) | not run | 0.802 % (0.219 %) | **passed** |
| DM1 PM, tt / ffx | ≥ 55° | 78.3° / 72.5° | 74.5° / 67.0° | 74.3° / 68.4° | **passed** |
| CM1 PM, tt / ffx | ≥ 60° (+3° allowance) | 75.6° / 62.3° | 72.9° / 59.7° | 74.5° / **61.3°** | passed against 60°; **failed** against 63° |
| DM2 PM, tt / ffx | ≥ 55° | 78.7° / 72.9° | 74.1° / 69.0° | 73.5° / 68.5° | **passed** |
| CM2 PM, tt / ffx | ≥ 60° (+3° allowance) | 68.2° / 61.7° | 65.5° / 58.3° | not readable / **57.7°** | **failed** (see open issue 2) |
| Settling, non-linear residual, tt/ss, ×1/×32 | ≤ 0.25 LSB | 0.0054 LSB | 0.0060 LSB | 0.0052 LSB | **passed** (16 of 20 decks; 4 failed, open issue 4) |
| Settling, total error (worst) | 0.25 LSB (linear part calibrated, INTERFACES.md) | 0.39 LSB | 1.28 LSB | **1.29 LSB** | failed (also before layout) |
| Settling offset at ×32, tt / ss | — | −0.0003 / −0.0002 mV | −0.25 / −0.23 mV | **−0.41 / −0.42 mV** | recorded (open issue 3) |
| Noise ×32 input-referred, ss | ≤ 35 µV | 31.01 µV | 30.82 µV | 31.48 µV | **passed** |
| Noise ×1 output, ss | ≤ 180 µV | 163.8 µV | 164.8 µV | 164.7 µV | passed |
| THD at 100 kHz (schematic: tt/ss/ff; E2: tt ×1, ×32) | ≤ 0.1 % | 0.025 % | not run | 0.012 % | **passed** |
| Output CM, all gains, tt/ss/ff | 0.600 V ± 30 mV | 0.5935–0.5973 V | 0.5953–0.5959 V (tt) | **0.6232–0.6296 V** | passed (margin 0.4 mV; open issue 1) |

Reading of the table:
1. Pair balance works: every pair is within 3.4 fF. The ×32 offset did not go away. It is larger (−0.41 mV). The
   revision-E hypothesis (P/N load imbalance causes the offset) is therefore **not supported**.
2. The full RC netlist shows a supply-resistance effect that the revision-E C-only run did not show. With the
   supply R divided by 1000 (diagnostic run `r1afe-postac-e2-supshort`), the output CM returns to 0.594–0.598 V and
   the ss f_c to 1.027 MHz. The +31 mV output-CM shift and −1.2 % f_c come from the `vss`/`vdd` wiring resistance.
3. The CM-sense nets are 26–58 % lighter, but CM1 and CM2 at ffx improve by only +1.6° and −0.6°. The CM-sense
   capacitance is not the main limit of the CM loops.

### Supply resistance (`reports/pex-e2-dev11/rnet_supply.json`; pin to farthest port, other ports open)

| Net | Top level | Inside the channel |
| --- | --- | --- |
| `vdd` | 6.2 Ω (sine channel), 11.1 Ω (cosine channel), 53.9 Ω (VCM1 divider head) | 203.5 Ω (gain-logic inverters `xi1`/`xi2`), others ≤ 138 Ω |
| `vss` | 42.3 Ω (divider foot), all other ports ≤ 19.9 Ω | 62.4 Ω worst |

The first E2 try (dev1) had vdd 54/131 Ω and vss 41/74 Ω from the pins to the two channels.

### Bias range (`r1_bias` PTAT current instead of the ideal 10 µA; run `r1afe-postbias-e2-rc`, E2 RC netlist)

Input from `r1_bias` (commit `7ff9a3fc3`): 10.14 µA at tt, 11.81 µA at ss/125 °C, 9.00 µA at ff/−40 °C, 6.9–15.4 µA
over PVT. No value is given for ffx (ff, 125 °C); ffx is run at both extremes (assumption). Loops: worst over ×1/×32
and CM 0.5/2.5 V. f_c: CM 2.5 V only. Noise: ss ×32.

| Corner, I_bias | DM1 PM | CM1 PM | DM2 PM | CM2 PM | f_c min | Output CM | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tt, 10.14 µA | 74.2° | 74.7° | 73.6° | not readable (4 of 4 rows) | 1.452 MHz | 0.628 V | **pass** (CM2 not read) |
| ss, 11.81 µA | 75.5° | 72.8° | 76.6° | 67.7° (1 of 4 readable) | 1.122 MHz | 0.633 V | **pass** (noise ×32 31.32 µV ≤ 35 µV) |
| ff, 9.00 µA | 73.7° | 75.2° | 69.2° | not readable | 1.862 MHz | 0.626 V | **pass** (CM2 not read) |
| tt, 6.9 µA | 73.7° | 69.4° | 72.3° | not readable | 1.403 MHz | 0.617 V | **pass** (CM2 not read) |
| tt, 15.4 µA | 67.1° | 81.3° | 75.4° (GM 7.2 dB) | 69.5° (1 of 4 readable) | 1.491 MHz | **0.646 V** | **fail**: output CM +46 mV |
| ffx, 6.9 µA | 60.5° | **56.4°** | 68.5° | not readable | not run | not run | **fail**: CM1 < 60° |
| ffx, 15.4 µA | 72.6° | 67.0° | 69.3° | 61.6° (3 of 4 readable) | not run | not run | **pass** (CM2 61.6°, below the 63° allowance) |

Both failures are at bias extremes. The netlist is not changed for them (coordinator instruction).

### CM2 loop reading and CM step

The Tian probe of the CM2 loop on the RC netlist often gives a phase that starts at −180° and rises (RHP flag; the
row is "not readable"). The magnitude curve is the same as in revision E. A transient CM step decides stability
(run `r1afe-postcm-e2-rc`, deck `tb_afe_cmstep.cir`, tt and ffx, ×1 and ×32; events: input CM ±, `vcm2` ±50 mV, VDDA ±):

| Quantity | E2 post, tt / ffx | Schematic (tt, `r1afe-cmstep-20261021e`) |
| --- | --- | --- |
| Output CM after a `vcm2` step of 50 mV: settle to 2 mV | 136–138 ns / 116 ns, 1 overshoot | 132 ns, 1 overshoot |
| Output CM after an input-CM step, peak / settle to 2 mV | ≤ 11.1 mV / ≤ 166 ns; ffx ≤ 15.0 mV / ≤ 146 ns | ≤ 3.1 mV / ≤ 46 ns |
| Stage-1 CM after an input-CM step (×32), settle to 5 mV | 430–470 ns / 382–388 ns | 404–420 ns |
| Steady-state ripple, stage-1 CM / output CM (peak-peak) | 0.37–0.49 mV / 0.08–0.16 mV | 0.008–0.022 mV / 0.006 mV |

Result: **every step settles; no growing oscillation**. The CM2 loop is stable at tt and ffx. The steady-state ripple is
about 20 times larger than in the schematic run and does not grow. Its cause (a small sustained oscillation or
numerical ringing of the RC netlist) is not isolated (open issue 8).

### Revision-F candidate (MIM sizes only; `schematic/r1_afe_revF_candidate.spice`, not the netlist of record)

Screens on the E2 RC netlist at ffx, ×1/×32, CM 0.5/2.5 V (`r1afe-poststb-e2dev10p-01` on the dev10 extraction, `r1afe-poststb-e2-02` on dev11):

| Variant (square side, µm) | CM1 | CM2 | DM1 | DM2 | f_c ss (CM 0.5 V) |
| --- | --- | --- | --- | --- | --- |
| E2 base (`WCS` 22/14, OTA2 `WCC` 18, `XCX` 15) | 61.3° | 57.7° | 68.4° | 68.5° | 1.015 MHz |
| OTA2 CS 18 or 22; OTA1 CS 26 | 61.0–61.9° | 57.6–59.0° | 66.4–68.4° | 65.6–67.2° | not run |
| OTA1 cross cap 17 + OTA2 CS 18 | 62.6° | 58.0° | 66.8° | 67.2° | not run |
| OTA1 cross cap 19 + OTA2 Miller 21 | 64.1° | 61.7° | 65.1° | 77.0° | not run |
| cross 19 + OTA1 Miller 27 + OTA2 Miller 22 | 65.7° | 62.7° | 67.4° | 79.2° | not run |
| **cross 21 + OTA2 Miller 24 (candidate)** | **65.5°** | **64.6°** | 63.6° | 82.8° | **0.981 MHz (fails 1.0 MHz)** |

The candidate reaches the CM target but fails f_c at ss (run `r1afe-postac-e2-01`; tt 1.393 MHz, ss CM 2.5 V
1.060 MHz). A MIM-only change cannot give CM2 ≥ 63° and f_c ≥ 1.0 MHz at ss together: the OTA2 Miller cap is the
only MIM lever for CM2, and it also slows the DM path. Recommendation for revision F: OTA1 cross cap 21 µm for CM1
(about +4°), and the OTA2 Miller zero resistor `LRZ` for CM2 (revision E: +2° for 6 → 10 µm). `LRZ` is not a MIM,
so it is outside this task. Not run on the candidate: tt/ss/ff loops, pole matching, settling, noise, THD; no layout.

### Open issues (revision E2)

1. **Supply resistance moves the output CM by +31 mV and lowers f_c by 1.2 %.** The output CM is 0.6296 V worst at
   10 µA (limit 0.630 V) and 0.646 V at 15.4 µA. Next step: find the net (channel `vss` is the probable one, 62 Ω)
   with a per-net R short, then widen it or give the CMFB reference a separate return.
2. **CM2 at ffx is 57.7° and many CM2 rows are not readable** (the Tian loop phase starts at −180°, the RHP flag is
   set). See "CM2 loop reading and CM step". CM1 at ffx is 61.3° (60° passed, 63° allowance not met).
   `r1_isense` revision b found the same flag and traced it to `vss` wiring R that closes a local loop; the
   same cause is probable here (not checked).
3. **×32 settling offset −0.41 mV** (revision E −0.25 mV). Not caused by P/N load imbalance (item 1 of the reading).
   Probable cause: supply or reference-path resistance; not isolated.
4. Four settling decks failed on the RC netlist ("timestep too small" at `vcm1__p1`; one stopped after 75 min). The
   residual and total error use the remaining 16 decks (at least 3 levels per gain and corner).
5. Bias range: CM1 at ffx with 6.9 µA is 56.4°; output CM at 15.4 µA is 0.646 V. The ffx bias value is an assumption.
6. Revision-F candidate fails f_c at ss. A non-MIM change (`LRZ`) is needed for CM2.
7. EM check of the supply wiring, LEF, fill: not run. Pole matching at ff on the E2 netlist: not run.
8. Steady-state CM ripple in the CM-step run: 0.37–0.49 mV (stage 1) and 0.08–0.16 mV (output), about 20 times the
   schematic value. Not growing. Cause not isolated; check with a tighter `reltol` and with the C-only netlist.

### Failures and mistakes (revision E2)

| # | What happened | Class | Record |
| --- | --- | --- | --- |
| 1 | A locked priority pass for the pairs walled in other pins. Fallback to an unlocked pass; lock is now off by default. | planning | `reports/layout-e2-dev1/` |
| 2 | dev1 had one M2.b notch from a Metal2 trim stub. Metal2 deficits now go to Metal3. | functional-bug | `reports/layout-e2-dev1/drc.log` |
| 3 | The PDK LVS database has unnamed layers, so the RC build could not use it. The kpex database is used. | tooling | `pex/pex_rc_build.py` |
| 4 | `klayout -b` did not print the `SystemExit` message of the RC build. Added `pex/klrun.py`. | tooling | — |
| 5 | kpex removed the top-level nets without devices. Added a dummy gate at each channel pin. The first try found only 4 of 36 pins (it used the bounding box, not the prBoundary). | tooling | `pex/pex_prepare.py` |
| 6 | The first C-only netlist used 1e-4 Ω links; ngspice stalled. Four ngspice processes were stopped by PID; run `r1afe-post2stb-e2dev1-c` is recorded with 4 failed jobs. The C-only view now merges the nodes. | numerical | `sim/runs/r1afe-post2stb-e2dev1-c/` |
| 7 | The RNetExtractor port index was mapped wrongly at first; fixed by keying on (kind, layer, port index). The tessellation mode gave negative elements; square counting stays the default. | tooling | `pex/pex_rc_build.py` |
| 8 | The RC run found about 100 mV `vdd` and 70 mV `vss` drop in the revision-E-style top-level supply wiring. The revision-E C-only extraction could not show it. Fixed by widening, Metal5 straps, Via4 farm and via feet (dev7–dev10). | verification-gap | `reports/layout-e2-dev6/` … `dev10/` |
| 9 | dev7: the router used the Metal1 guard ring as a `vss` conductor (vss 175–180 Ω). The ring is now a `vss` pin only near the south `vss` pins. | functional-bug | `reports/layout-e2-dev7/` |
| 10 | dev1 and dev6 routes differ for the same inputs, because the failed lock pass changed the router history. | process-hygiene | — |
| 11 | The first trim (dev10) over-corrected `souts_n` (19.9 / 35.5 fF). dev11 removed it. | estimation | `layout/r1_afe_trim_e2.json` |
| 12 | The ×32 offset hypothesis of revision E (P/N load imbalance) was wrong: the offset grew after balancing. | estimation | reading item 1 |
| 13 | The MIM-only revision-F path was planned without an f_c check at ss in the screens; the chosen candidate then failed f_c. | planning | `r1afe-postac-e2-01` |
| 14 | Settling decks on the RC netlist: 3 failed with "timestep too small", 1 was stopped by PID after 75 min. | numerical | `sim/runs/r1afe-post2-e2-rc/` |
| 15 | The time budget (about 5 h) was exceeded by about 4 h: three CPUs for 37 + 20 + 14 decks on an RC netlist that runs 3–5 times slower than the C-only one. | estimation | run records |
| 16 | Waits written with `sleep` were blocked; replaced by condition loops. | process-hygiene | — |

---

## Layout (revision E, 2026-10-21, track T3)

**Superseded by layout revision E2 (above).** The revision-E GDS is kept as `layout/r1_afe_revE.gds`.

Layout of record (until E2): `layout/r1_afe_revE.gds` (sha256 `0181e988…91e1`, 3.6 MB, top cell `r1_afe`, child cell `r1_afe_ch`
placed twice). It is generated from the revision-E netlist of record (`schematic/r1_afe.spice`, sha256 `4a84a3d8…9e46`)
by `layout/r1_afe_layout.py`. The block contains both channels, both stages, the gain switches, the anti-alias
filters, the CMFB circuits, the bias mirrors and the VCM1 divider. All post-layout numbers are **simulated**.

### Built against (layout)

| Item | Version | How established |
| --- | --- | --- |
| IHP SG13G2 open PDK | commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` compares `/foss/pdks/ihp-sg13g2/COMMIT` before every command; also in each `run.json` |
| KLayout (layout, DRC, LVS, antenna) | 0.30.9 | `klayout -v` in `reports/layout-20261021-a/run.json`; DRC log line "KLayout version detected" |
| kpex (klayout-pex) | 0.3.12 | `kpex --version` (`reports/pex-20261021-b/run.json`) |
| ngspice | ngspice-46 | `ngspice -v` in `sim/runs/r1afe-post-20261021e-*/run.json` |
| Container image | `sha256:ddeb6957…bab2` | verified by `flow/run.sh` |
| PDK decks | `libs.tech/klayout/tech/drc/run_drc.py`, `lvs/run_lvs.py` (unmodified) | `layout/run_checks.sh` |
| CPU set | `G1_CPUSET=106-108` | command lines in the run records |

### Files (layout)

| Path | Content |
| --- | --- |
| `layout/r1_afe_layout.py` | generator (KLayout batch Python): PDK PCells (`nmosHV`, `pmosHV`, `cmim`), `rppd` body copied from the PDK PCell, placement, routing, pins |
| `layout/maze_router.py` | grid maze router on Metal2–Metal4 (0.8 µm grid, A* with rip-up and history costs) |
| `layout/r1_afe_netlist.py` | flattens the netlist of record and writes the LVS reference `layout/r1_afe_lvs.cdl` (unit split, see below) |
| `layout/r1_afe.gds`, `layout/r1_afe_lvs.cdl`, `layout/r1_afe_layout.json` | layout, LVS reference, bounding box and router statistics |
| `layout/run_checks.sh` | DRC, antenna and LVS with the PDK decks; writes `reports/<run-id>/run.json` |
| `layout/tools/lvsdb_report.py` | net and device counts per circuit from the LVS database |
| `pex/pex_prepare.py`, `pex/make_postlayout.py` | flat GDS for kpex (MIM removed); post-layout netlist from the kpex capacitors |
| `sim/run_afe.py` | new campaign `post`; `R1AFE_NETLIST=<file>` replaces the netlist of record for a whole campaign (recorded in `run.json`) |
| `sim/compare_post.py` | pre/post-layout reduction (`reports/post-20261021e.json`) |
| `reports/layout-20261021-a/` | `run.json` (checks), `layout_run.json` (generation, reproduction), `drc.log`, `antenna.log`, `lvs.log`, `lvs_summary.txt` |
| `reports/pex-20261021-b/run.json` | extraction record |
| `reports/layout-dev4/`, `reports/layout-dev5/` | development check logs (dev4: failing DRC/LVS before the fixes in the mistakes list) |

Bulk outputs (flat GDS, kpex netlists, LVS databases, decks, waveforms) are in `<G1_RESULTS_ROOT>/r1_afe/<run-id>/`.

Reproduce (repository root): `G1_CPUSET=106-108; export G1_CPUSET; G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`, then
1. `G1_WORKDIR=designs/r1-joint/blocks/r1_afe/layout; export G1_WORKDIR; flow/run.sh klayout -b -r r1_afe_layout.py` (about 200 s).
2. `flow/run.sh sh run_checks.sh <run-id> all`.
3. The PEX and post-layout commands in `reports/pex-20261021-b/run.json` and `sim/runs/r1afe-post-20261021e-pex/run.json`.

### Floorplan and construction

- Block: **192.8 × 494.4 µm = 0.0953 mm²** (bounding box (0, 0; 192.8, 494.4) µm). Channel cell 168.8 × 193.6 µm.
- The sine channel is at the south and the cosine channel at the north. The cosine channel is a translated copy (same
  orientation, same dummies). The VCM1 divider (`RD1`/`RD2`) and its capacitor `CD` (2 × 2 units) are between the channels.
- Each channel, from south to north: the `rppd` array, NMOS rows, PMOS rows (one NWell). MIM units (Metal5 bottom
  plate, TopMetal1 top plate) cover the resistor array and the transistor rows (cut C6): 14 736 µm² of the 30 060 µm²
  of MIM are over `rppd` bodies.
- `rppd` (w = 1 µm): unit columns with two poly dummy columns at each end of every group. The PGA input resistors U1
  (18 per channel) are P/N interleaved in one group. Long resistors are straight series segments of equal length
  (≤ 78 µm, for example U1 = 2 × 76.925 µm).
- MIM: the feedback and output capacitors (`CF1`, `CF2`, `CO1`/`CO2`) are 2 × 4 common-centroid blocks (ABBA/BAAB);
  `COD` 2 × 2; compensation capacitors in P/N pairs. Capacitors larger than 28 µm are four units of half the side.
- All MOS are thick-oxide (`sg13_hv_*`, ThickGateOx over every row), fingers ≤ 10 µm, end dummies on every row,
  one tie strip per row. The input pairs are adjacent in one row, **not** interdigitated (open issue).
- A p+ guard ring (Activ 0.6 µm with pSD, contacts and a Metal1 ring, net `vss`) surrounds the block.
- Routing: Metal2–Metal4 only. **TopMetal1 is used only for the MIM top plates and their 1.64 µm tabs** (the PDK MIM
  has its top plate on TopMetal1). No TopMetal2. The core ring may pass over the block (C7) on TopMetal2.
- Pins: 21 pins on Metal3 (`30/2` pin shapes and labels) at the block edge: 17 at the south edge (outputs, `vcm2`,
  bias, `c1`–`c4`, supplies) and `sinp`, `sinn`, `cosp`, `cosn` at the west edge. VDDA = `vdd`, VSSA = `vss`.
  The netlist has no digital VDD/VSS (not applicable).

LVS reference (`layout/r1_afe_lvs.cdl`): the netlist of record with three mechanical changes, written by `r1_afe_netlist.py`:
`rppd` longer than 78 µm split into equal series segments; `cap_cmim` larger than 28 µm split into four parallel units of
half the side (the PDK deck merges parallel MIM units into m = 4); MOS finger count re-cut to ≤ 10 µm per finger.
The split changes the electrical netlist a little (each extra `rppd` segment adds two contact heads; four MIM units have
twice the perimeter). Its effect was simulated separately (column "split" below).

### Status (layout, run ids `layout-20261021-a`, `pex-20261021-b`, `r1afe-post-20261021e-*`)

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| Area | ≤ 0.10 mm² (task); S6 estimate 0.069 mm² | **passed** against 0.10: 0.0953 mm². Above the S6 estimate (open issue 6) | `reports/layout-20261021-a/layout_run.json` |
| Reproduction of the GDS | same layout from the same inputs | **passed**: regenerated, KLayout `LayoutDiff` identical (file hash differs only by the GDS time stamp) | `reports/layout-20261021-a/layout_run.json` |
| DRC, PDK deck, main + maximal rule set (deep, `--no_density`) | 0 violations | **passed**: 0 | `reports/layout-20261021-a/drc.log` |
| DRC density rules | block level | **not run** (waived at block level; chip-level fill and density are the integrator's) | — |
| Antenna, PDK deck | 0 violations | **passed**: 0 | `reports/layout-20261021-a/antenna.log` |
| LVS, PDK deck (`--no_series_res`) against `layout/r1_afe_lvs.cdl` (revision E, unit split) | netlists match | **passed**: `r1_afe` nets 63/63, devices 46/46; `r1_afe_ch` nets 143/143, devices 240/240 (after the deck merges parallel MIM units) | `reports/layout-20261021-a/lvs.log`, `lvs_summary.txt` |
| No TopMetal2; TopMetal1 only on MIM | C7 | **passed** (TopMetal2 area 0; TopMetal1 29 257 µm², all MIM plates and tabs). Spec ambiguity: see open issue 2 | layer report, `<G1_RESULTS_ROOT>/r1_afe/layout-20261021-a/r1afe_layers.py` |
| Pins on the boundary, Metal3 or lower | — | **passed**: 21 Metal3 pins | same |
| Fill (G1 fill scripts) | if the deck needs it | **not run** (block-level DRC without density does not need fill) | — |
| PEX, channel cell (kpex 0.3.12, 2.5D, CC) | extraction completes | **passed**: 3297 capacitors, 3.61 pF total in one channel | `reports/pex-20261021-b/run.json` |
| PEX, full block (top-level routing, VCM1 divider, outputs to the pins) | extraction completes | **not run to completion**: flat kpex of the whole block stopped after 2 h 33 min without a result (the channel alone took about 30 min) | `<G1_RESULTS_ROOT>/r1_afe/pex-20261021-a/` |
| Wiring resistance | — | **not run** (kpex CC mode is capacitance only) | — |
| Post-layout key decks | see the table below | **run**: 30 jobs, 0 failed; results in the table | `sim/runs/r1afe-post-20261021e-pex/run.json` |
| EM/IR of the 0.3 µm supply routing | — | **not run** | — |
| LEF / abstract | — | **not run** | — |

### Pre-layout vs post-layout (simulated; tt = 3.3 V, 27 °C; ffx = ff, 3.0 V, 125 °C; ss = 3.0 V, 125 °C)

Columns: **schematic** = netlist of record (`r1afe-post-20261021e-sch`); **split** = LVS unit split, no parasitics
(`…-split`); **post-layout** = split + kpex capacitances of the channel cell (`…-pex`). Reduction: `sim/compare_post.py` →
`reports/post-20261021e.json`. Loop margins are the worst over ×1 and ×32 and input CM 0.5 and 2.5 V.

| Quantity | Limit | Schematic | Split | Post-layout | Status (post-layout) |
| --- | --- | --- | --- | --- | --- |
| f_c, minimum over steps, tt, CM 0.5/2.5 V | ≥ 1.0 MHz | 1.280 MHz | 1.278 MHz | 1.292 MHz | **passed** |
| Pole matching, tt, 20 MC samples × 6 steps, worst \|Δf3\| (σ) | ≤ 1 % | 0.563 % (0.232 %) | 0.536 % (0.236 %) | 0.716 % (0.228 %) | **passed** at tt; ss not run post-layout (pre-layout ss worst 0.976 %) |
| DM1 phase margin, tt / ffx | ≥ 55° | 78.3° / 72.5° | 78.5° / 72.8° | 74.5° / 67.0° | **passed** |
| CM1 phase margin, tt / ffx | ≥ 60° | 75.6° / 62.3° | 75.8° / 62.8° | 72.9° / **59.7°** | **failed** at ffx (−0.3°) |
| DM2 phase margin, tt / ffx (information) | ≥ 55° | 78.7° / 72.9° | 79.0° / 73.2° | 74.1° / 69.0° | passed |
| CM2 phase margin, tt / ffx (information) | ≥ 60° | 68.2° / 61.7° | 70.0° / 63.1° | 65.5° / **58.3°** | **failed** at ffx (−1.7°) |
| Settling into the r1_adc T/H, non-linear residual, tt/ss, ×1/×32 | ≤ 0.25 LSB | 0.0054 LSB | 0.0053 LSB | 0.0060 LSB | **passed** |
| Settling, total error (worst) | 0.25 LSB (INTERFACES.md) | 0.39 LSB | 0.39 LSB | **1.28 LSB** (tt ×32) | **failed** (was failed before layout). New part: an output offset at ×32 of −0.25 mV (−0.57 LSB) tt and −0.23 mV ss; gain error 0.044 % |
| Noise ×32 input-referred, ss | ≤ 35 µV | 31.01 µV | 30.69 µV | 30.82 µV | **passed** |
| Noise ×1 output, ss | ≤ 0.41 LSB (180 µV) | 163.8 µV | 163.5 µV | 164.8 µV | passed |

Reading of the table:
1. The unit split alone changes nothing that matters (≤ 0.4° and ≤ 0.2 %).
2. The extracted capacitance lowers every loop margin by 3–6°. CM1 and CM2 at ffx fall below 60°.
3. The ×32 settling now has an offset of about −0.25 mV at the sample instant. Capacitors cannot give a DC offset, so the
   offset is dynamic. The probable cause is the P/N imbalance of the extracted loads (net totals: `outn` 132.8 fF and
   `outp` 73.9 fF; `x1n` 220.0 fF and `x1p` 209.5 fF; `m1p` 251.7 fF and `m1n` 246.7 fF). The reset kick of the T/H model is common mode; an
   unequal P/N load converts part of it to a differential error. This is a hypothesis; no run isolates it yet.

### Open issues (layout)

1. **CM1 (59.7°) and CM2 (58.3°) phase margins at ffx are below 60° after layout.** A next revision needs about +3° of
   CM margin at ffx before layout, or a layout with less capacitance on the CM-sense nodes (`xa1_vcms` 117 fF, `xa2_vcms` 73 fF in total).
2. **Settling offset at ×32 (−0.25 mV, −0.57 LSB).** Balance the P/N routing of `outp`/`outn`, `x1p`/`x1n` and `m1p`/`m1n`
   (route the pairs as matched pairs), then re-run `post`. The total-error limit was failed before layout (coordinator item).
3. **TopMetal1 is used in the block** for the MIM top plates. The PDK MIM has its top plate on TopMetal1, so C7 ("no
   TopMetal1/TopMetal2 inside the block") cannot hold with MIM. Recommended reading, taken here: no TopMetal2; TopMetal1
   only on MIM plates and their tabs. The core ring on TopMetal2 may pass over the block. Needs the coordinator's confirmation.
4. **Top-level parasitics are not in the post-layout netlist.** The full-block extraction did not finish (2 h 33 min). The
   output routing to the south pins and the VCM1 divider are therefore without wiring capacitance. Both channel
   instances use the same channel extraction, so channel-to-channel differences from the top-level routing are not
   simulated. Next step: extract the top cell with the channels as black boxes, or with an abstract.
5. No wiring resistance (kpex CC). The supply routing is 0.3 µm Metal2–Metal4; EM/IR not run.
6. Area 0.0953 mm² is above the S6 estimate for `r1_afe` (0.069 mm²) and inside the task limit 0.10 mm².
7. The input pairs (`MN1`/`MN2` of each OTA) are adjacent with end dummies, not interdigitated or common-centroid.
8. Post-layout runs cover tt, ss (settling, noise) and ffx (loops) only. Pole matching at ss, the cross corners other than
   ffx, the transient and overload decks are not run on the extracted netlist.
9. No LEF or abstract view. No block-level fill.
10. The netlist of record still has "revision D" in its header comment line (content is revision E; sha256 unchanged here).

### Failures and mistakes (layout)

| # | What happened | Class | Record |
| --- | --- | --- | --- |
| 1 | The first extraction kept the TopMetal1 top plate over the removed MIM. kpex counted the plate overlap as a capacitor between the two MIM terminals (for example 104 fF `outp`–`outn`), on top of the `cap_cmim` model (f_c −2.5 % in the first deck). Found by reading the largest capacitors; `pex_prepare.py` now removes TopMetal1 inside the MIM; run `pex-20261021-a` and `r1afe-post-20261021e-pexa` (stopped) are superseded. | verification-gap | `<G1_RESULTS_ROOT>/r1_afe/pex-20261021-a/` |
| 2 | The full-block flat kpex was started without an estimate of its run time; it ran 2 h 33 min without a result and was stopped. The channel alone took about 30 min. | estimation | open issue 4 |
| 3 | The first kpex was started as a background job with the default 30 min limit. The shell was stopped; the container kept running. Its output directory was renamed for a moment while it still ran, and then renamed back. | process-hygiene | — |
| 4 | `flow/run.sh` does not pass environment variables into the container. The first "split" campaign ran on the schematic netlist; it was stopped and restarted with `flow/run.sh env R1AFE_NETLIST=…`. | tooling | `sim/run_afe.py` header comment |
| 5 | The first `post` campaign had two settling levels, too few for the linear fit; it was stopped and restarted with five. | planning | — |
| 6 | The layout regeneration check first wrote into a directory that did not exist (exit 1); repeated after `mkdir`. | process-hygiene | — |
| 7 | Router: the many-pin nets (`c1`–`c4`, `vdd`) failed in the first pass; rip-up with history costs added. Only three tracks were left between the guard ring and the sine channel; a 12.8 µm south routing band was added. | planning | `layout/maze_router.py` |
| 8 | DRC TM1.b: the TopMetal1 tab did not reach the inset PCell top plate (it would also have been an open). The tab now starts at the plate centre. | functional-bug | `reports/layout-dev4/drc.log` |
| 9 | DRC V4.c1 (Via4 without Metal4 cover on unrouted MIM pins) and M2.b (0.015 µm and 0.175 µm notches between router pads and gate rails). Fixed: Metal4 pads always drawn; gate rails 0.40 µm; same-net pads bridged. | functional-bug | `reports/layout-dev4/drc.log` |
| 10 | LVS: the last `RD2` segment was 0.02 µm longer than the others (the PCell rounds lengths to three digits). The split now uses equal segments on the 5 nm grid and the `rppd` body is copied and stretched, not taken from the PCell. | numerical | `reports/layout-dev4/lvs.log` |
| 11 | First floorplan: stacked `S2` resistors made the array 155 µm tall; changed to single slots (80 µm). | estimation | — |
| 12 | Host Python 3.8 has no dict `|` operator; the size pass had too small a grid ("pin has no usable node"); `klayout -b` output was buffered. Fixed in the generator. | tooling | — |
| 13 | Waits written as `sleep` chains were blocked by the harness; replaced by condition loops. | process-hygiene | — |

---

## Revision E (2026-10-21, track T3 revision E) — schematic record

Netlist of record: `schematic/r1_afe.spice` (revision E, sha256 `4a84a3d8…9e46`). Revision D is kept as
`schematic/r1_afe_revD.spice` (sha256 `f32486ce…146b`). Revision E fixes open issue 1 of revision D (the ffx cross
corner: ff, 3.0 V, 125 °C). Only compensation values changed. There is no topology change, no bias change and no
change to the ADC interface. All numbers are **simulated** (ngspice-46, IHP SG13G2 `84374023`), schematic level.
LSB = 1.8 V / 4096 = 0.439 mV. Built against: same as revision D (PDK commit checked by `flow/run.sh`; image
`sha256:ddeb6957…bab2`; `G1_CPUSET=106-108`).

### What changed (revision D → E)

| Instance | Parameter | Revision D | Revision E | Effect |
| --- | --- | --- | --- | --- |
| `XA1` (OTA1) | `WCCB`, switched Miller part (square side) | 20.4 µm | **24 µm** | DM1 at ffx ×1: 52.8° → 56.7° with no f_c change (the fix named in revision D) |
| `XA1` (OTA1) | `LRZ`, Miller zero resistor (rppd, w = 1 µm) | 13 µm | **21 µm** | main CM1 and DM1 lever: ffx CM1 ×32 54.3° → 61.2°, DM1 ×1 → 74° (f_c −0.7 %) |
| `XCX1`, `XCX2` (OTA1) | cross-coupled Miller caps (square side) | 13 µm | **15 µm** | CM1 +1.1°, f_c +0.5 % (the cap subtracts for DM) |
| `XA2` (OTA2) | `LRZ`, Miller zero resistor | 6 µm | **10 µm** | ffx CM2 ×32 59.6° → 61.6° |

Unchanged: `WCC` 25 µm, `WCS` 22/14 µm, all device sizes, bias, gain strings, output network. The edits are in the
netlist header (revision E block). `sim/apply_reve.py` writes the three `rz1_21+cxs15+rz2_10` edits from `devvar()`; `WCCB` was set by hand.

How the values were found (development screens, all at ffx CM 0.5/2.5 V and ss CM 0.5 V, ×1/×8/×32, plus ss f_c;
`sim/run_afe.py` campaign `dev:stbe:<variants>`): `dev-reve-01` screened cross cap, Rz, CM sense cap and Miller cap
(the CM sense cap and a larger Miller cap are not useful: f_c 0.986 MHz at `cc1_27`). `dev-reve-02` and `-03` went to
larger Rz and to OTA2 Rz. `dev-reve-04` showed that settling into the T/H does not depend on the Rz values (total error
0.383/0.385/0.387 LSB). `dev-reve-05` (after the campaign) gives the gain margins of the Rz steps; see open issue 1.

### Margins at the seven corners (worst loop-gain PM, degrees; ×1 and ×32, input CM 0.5 and 2.5 V; `r1afe-stbx-*`)

| Corner | DM1 D → E | CM1 D → E | DM2 D → E | CM2 D → E |
| --- | --- | --- | --- | --- |
| tt | 66.9 → 78.3 | 64.4 → 75.6 | 71.5 → 78.7 | 65.1 → 68.2 |
| ss | 65.5 → 80.6 | 62.4 → 70.8 | 73.8 → 80.8 | 66.0 → 69.0 |
| ff | 65.3 → 76.2 | 70.5 → 76.7 | 68.0 → 74.8 | 62.7 → 65.7 |
| sf | 67.7 → 78.5 | 64.6 → 77.2 | 71.1 → 78.3 | 65.0 → 68.1 |
| fs | 66.2 → 78.1 | 64.3 → 73.3 | 72.0 → 79.1 | 65.3 → 68.3 |
| ssx (ss, 3.6 V, −40 °C) | 76.2 → 70.5 | 78.2 → 83.2 | 75.6 → 84.7 | 69.3 → 73.5 |
| **ffx (ff, 3.0 V, 125 °C)** | **52.8 → 72.5** | **54.3 → 62.3** | 67.9 → 72.9 | **59.6 → 61.6** |

Limits: DM ≥ 55°, CM ≥ 60°. Every cell passes. The smallest margin is CM2 at ffx (61.6°, +1.6°) and CM1 at ffx (62.3°, +2.3°).
One cell fell: DM1 at ssx (76.2° → 70.5°, still 15° above the limit).

### Status (revision E, run suffix `20261021e`)

Evidence: `sim/runs/<run-id>/run.json` (question, result, disposition, netlist sha256 `4a84a3d8…`), `sim/results/<run-id>.json`,
reduced numbers in `sim/results/summary-20261021e.json` (small) and `sim/results/reduction-full-20261021e.json` (output of
`report_afe.py`); raw decks, logs and waveforms in `<G1_RESULTS_ROOT>/r1_afe/<run-id>/`, frozen inputs in `…/<run-id>/frozen/`.
All 14 campaigns ran with no failed job. Revision-D values are in brackets.

| Check | Criterion | Status | Evidence (run id) |
| --- | --- | --- | --- |
| Loop-gain method (toy loop) | matches an exact return ratio | **passed** (relative error 4.7e-8) | `r1afe-stbval-20261021e` |
| Stage-1 DM loop, tt/ss/ff, CM 0.5/2.5/2.8 V, six-step coverage | PM ≥ 55° | **passed**: worst 68.0° [64.4°] | `r1afe-stb-20261021e` |
| Stage-1 CM loop | PM ≥ 60° | **passed**: worst 70.8° [62.4°] | `r1afe-stb-20261021e` |
| Stage-2 DM loop | PM ≥ 55° | **passed**: worst 74.5° [67.7°]. **Gain margin fell to 7.0 dB** [10.0 dB] (no limit set; open issue 1) | `r1afe-stb-20261021e` |
| Stage-2 CM loop | PM ≥ 60° | **passed**: worst 64.4° [61.3°], GM ≥ 23.4 dB | `r1afe-stb-20261021e` |
| CMFB-node breaks | informational | **not applicable** (`pm_valid = false`, as in revision D) | `r1afe-stb-20261021e` |
| Loop gain at the seven corners, ×1 and ×32, CM 0.5/2.5 V | DM ≥ 55°, CM ≥ 60° | **passed** at all seven, including ffx (table above). ×8 at ffx was checked only in the screens (CM1 ×8 67.6°, DM1 ×8 74.9°, `dev-reve-03`); the campaign does not cover ×8 at the cross corners | `r1afe-stbx-20261021e`, `dev-reve-03` |
| Anti-alias f_c | ≥ 1.0 MHz | **passed**: min 1.017 MHz [1.020] (ss, ×32); peaking ≤ 0.00002 dB. Not measured at the cross corners (the `ac` campaign covers tt/ss/ff) | `r1afe-ac-20261021e` |
| Output swing, output CM | 1.44 Vpp; 0.600 V ± 30 mV | **passed**: gain steps within 0 to 1.41 % of ideal; output CM 0.5935–0.5973 V | `r1afe-ac-20261021e`, `r1afe-tran-20261021e` |
| Gain steps, ratio error | recorded | **passed**: step-ratio error ≤ 1.41 % [1.41 %] | `r1afe-ac-20261021e` |
| CM-step transient, tt/ss/ff, ×1/×32 | no sustained oscillation (≤ 1 mV pp); detects `dev-revb-02` | **passed**: ≤ 0.24 mV pp; `dev-revb-02` 1490 mVpp. Recorded: pin step settles to 5 mV in ≤ 600 ns [596], ≤ 3 excursions | `r1afe-cmstep-20261021e` |
| Settling into the T/H, total error | ≤ 0.25 LSB (INTERFACES.md) | **failed** (unchanged open issue 2): worst 0.39 LSB [0.38] (tt ×32) | `r1afe-settle_adc-20261021e` |
| Settling, non-linear residual | ≤ 0.25 LSB (accepted criterion) | **passed**: ≤ 0.005 LSB; linear part −0.023 % to +0.024 % | `r1afe-settle_adc-20261021e` |
| Noise ×32 input-referred | ≤ 35 µV, ≥ 5 % margin at ss | **passed**: 31.0 µV ss [31.0] | `r1afe-noise-20261021e` |
| Noise ×1 output | ≤ 0.41 LSB | **passed**: 164 µV = 0.37 LSB [0.37] | `r1afe-noise-20261021e` |
| THD at 100 kHz | ≤ 0.1 % | **passed**: worst 0.025 % [0.025] | `r1afe-tran-20261021e` |
| Pole matching, 20 MC per corner | \|Δf3\| ≤ 1 % | **passed**, margin 0.024 %: worst 0.976 % (ss) [0.961 %], σ ≤ 0.36 %; phase mismatch ≤ 0.078° | `r1afe-ac_mc-20261021e` |
| Temperature −40/27/125 °C | f_c ≥ 1 MHz | **passed**: 1.369 MHz [1.371]; gain spread ≤ 0.53 % | `r1afe-temp-20261021e` |
| Input CM 0–3.3 V with stock pad | gain within 2 %; pad < 1 µA at 2.8 V | **passed**: ≤ 1.54 %; ≤ 4.1 nA | `r1afe-cm-20261021e` |
| PSRR (20 MC, tt) | ≥ 40 dB | **passed**: worst 54.3 dB (20 kHz), 54.7 dB (1 MHz) [54.3, 54.7] | `r1afe-psrr-20261021e` |
| Input overload ±1.0 V | recorded | **recorded**: ×32 recovery to 1 LSB ≤ 1240 ns [1236] | `r1afe-overload-20261021e` |
| Source impedance 0/100/300/1000 Ω | recorded | **recorded**: at 1 kΩ ×1 −2.8 %, ×32 −18.8 % (same as revision D) | `r1afe-rsrc-20261021e` |
| Development screens | — | **recorded** (not part of the campaign of record) | `dev-reve-01…05` |
| Gain-switch transients, bias from r1_bgr, c1..c4 level shifters | — | **not run** | — |
| Layout, DRC, LVS, PEX, post-layout | — | **run** after this record: see "Layout (revision E)" | `reports/layout-20261021-a/`, `reports/pex-20261021-b/` |

Regression list (revision-D list, 17 rows): every row re-run; 16 passed or recorded as in revision D, the settling total error stays
**failed** (it failed in revision D and is a coordinator item). No row that passed in revision D fails. Two rows lost margin:
stage-2 DM gain margin (10.0 → 7.0 dB) and pole matching (0.961 → 0.976 %, limit 1 %).

### Area and current (revision E)

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.1006 mm² (MOS 0.0286, rppd 0.0329, MIM 0.0391); revision D 0.0994 | **estimated**, `sim/area_estimate.py` → `sim/results/area_estimate_revE.json` |
| of which revision E | ≈ +0.0012 mm² (MIM +0.0011: `WCCB` and cross caps; rppd +0.0001: longer Rz) | estimated |
| VDDA current, both channels | 1.71–2.00 mA (tt 1.76–1.95, ss 1.71–1.90, ff 1.93–2.00), same as revision D | simulated, `r1afe-ac-20261021e` |

### Open issues (revision E)

1. **Stage-2 DM gain margin is 7.0 dB (ff, ×1, hold load) and 5.5 dB at ssx** (revision D 10.0 and 9.8 dB). The longer OTA2 Rz
   (6 → 10 µm) raises the PM and lowers the GM. The screen `dev-reve-05` shows the trade: OTA2 Rz 8 µm gives GM 11.0 dB (min over
   ffx and ss) and CM2 60.6° at ffx; 10 µm gives 9.2 dB and 61.6°; 6 µm gives 11.7 dB and 59.5° (fails). Stage-1 DM GM also fell
   (15.5 → 11.0 dB). The CM2 margin at ffx is thin whatever the Rz value. No GM limit exists in the specification. A next revision should set one
   (suggest ≥ 6 dB) and choose between OTA2 Rz 8 and 10 µm after a full run.
2. **Settling total error 0.39 LSB** against 0.25 LSB in INTERFACES.md. Unchanged from revision D. The coordinator decision stands.
3. **Pole-matching margin is 0.024 %** (0.976 % of 1 %), and f_c margin is 1.7 % (1.017 MHz). Layout will move both. The longer Rz adds a little to the mismatch (σ 0.356 → 0.363 %).
4. ×8 at the cross corners and f_c at the cross corners are not in the campaigns of record (screens only).
5. CM-step ringing, source impedance, interfaces not designed, `vcm2`, VCM1 and bias: as revision D (issues 4 and 5).
6. Checks marked **not run** in the status table.

### Failures and mistakes (revision E)

| # | What happened | Class | Record |
| --- | --- | --- | --- |
| 1 | The screens printed PM and f_c only. The gain margin of the stage-2 DM loop fell from 10.0 to 7.0 dB (5.5 dB at ssx) because of the OTA2 Rz choice, and it was seen only in the campaign. A rerun with OTA2 Rz 8 µm did not fit the time budget. | verification-gap | `dev-reve-03`, `dev-reve-05`, open issue 1 |
| 2 | The OTA2 Rz was chosen from the CM2 PM alone (monotonic in Rz) with no second criterion; the largest screened value (10 µm) was taken. | planning | `dev-reve-03` |
| 3 | The campaigns of record cover cross corners at ×1 and ×32 only. The ×8 CM1 margin at ffx (57.7° in revision D) was checked in the screens, not in the campaign; the CM1 ×8 value is not in the regression list. | verification-gap | `r1afe-stbx-20261021e` |
| 4 | `report_afe.py` took the revision from the suffix letter (`c`, `d`); the letter `e` fell through to the revision-A/B reductions (the first call also failed for a missing `G1_RESULTS_ROOT`). Fixed in `report_afe.py` lines 11–12. | tooling | `report_afe.py` |
| 5 | `report_afe.py` writes `summary-<suffix>.json` as a 150 kB file. The small summary required by the task took that name; the full reduction was renamed `reduction-full-20261021e.json`. | process-hygiene | `sim/results/` |
| 6 | The report prints PSRR for the nominal corners as 190–265 dB (numerical zero of the differential path). Only the mismatch rows (`tt_mc`) are meaningful. Same as revision D; not fixed. | tooling | `summary` psrr table |
| 7 | Revision D expected a CM1 fix from the cross cap (+0.9° at ffx). At 13 → 15 µm it gave only +1.1°. Rz was the larger lever (+7° for +8 µm). A plan with cross cap and Miller cap only would not reach 60° (the larger Miller cap fails f_c, 0.986 MHz). | estimation | `dev-reve-01` |
| 8 | A first background wait command used `sleep` in a chain and was blocked; the three waits ended by the time limit, not by the job. No effect on results. | process-hygiene | — |

### Files (revision E additions)

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision E netlist of record |
| `schematic/r1_afe_revD.spice` | revision D netlist (runs `r1afe-*-20261020d`) |
| `sim/run_afe.py` | driver; new `devvar()` terms `rz1_<um>`, `rz2_<um>`, `cs2_<um>`, `cc2_<um>`; new `dev:stbe` kind |
| `sim/apply_reve.py` | writes the Rz and cross-cap edits into the netlist |
| `sim/report_afe.py` | suffix letter `e` handled like `d` |
| `sim/results/summary-20261021e.json`, `reduction-full-20261021e.json`, `area_estimate_revE.json` | small summary; full reduction; area estimate |
| `sim/runs/r1afe-*-20261021e/`, `sim/runs/dev-reve-0*/` | run records |

Reproduce: `G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`, then
`sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh 20261021e` and `cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py 20261021e`.

---

# Revision D record (superseded by revision E)

## Revision D (2026-10-20, track T3 revision D)

Netlist of record: `schematic/r1_afe.spice` (revision D, sha256 `f32486ce…146b`). Revision C is kept as
`schematic/r1_afe_revC.spice`; its record follows below ("Revision C record"). All numbers are **simulated**
(ngspice-46, IHP SG13G2 `84374023`), at schematic level. LSB = 1.8 V / 4096 = 0.439 mV (D16) unless stated.

### What changed (revision C → D)

| # | Change | Why | Evidence (screen) |
| --- | --- | --- | --- |
| 1 | Stage-2 input string 17.5 kΩ → 19.44 kΩ (`LS2` 74.79 µm): gain 36/35 and 144/35 | D16: 1.44 Vpp differential output = 80 % of the ADC ±0.9 V full scale | `dev-revd-ocm-01` (variant `base`) |
| 2 | OTA2 bias references `XMB0 XMB1 XMB4 XMC3 XMC4` 4/1 µm → 8/2 µm | Open issue 3. The cause of the rev-C output-CM error was the mirror length: the OTA2 sinks (l = 2 µm) mirrored l = 1 µm references, so the mirror ratios moved with the corner and the CMFB pair had to absorb the difference. The fixed/CMFB sink split only made it visible (less CMFB gm). | `dev-revd-ocm-01` (`l2`) |
| 3 | OTA1 Miller cap fixed part 22 → 25 µm square, plus cross-coupled caps `XCX1` (cz1 → outn) and `XCX2` (cz2 → outp), 13 µm square | Open issue 2. A cross cap adds to the Miller cap for CM and subtracts for DM. The stage-1 CM loop gets more compensation at ×8/×32, while the DM compensation (and f_c) stays nearly the same. | `dev-revd-cm1-02`, `dev-revd-cm1ac-02/03`, `dev-revd-comb-ac-02` |
| 4 | OTA1 NMOS input pair 80 → 160 µm wide (l = 2 µm, ng 32) | Open issue 5: flicker noise at ×32 | `dev-revd-noise-01` (`np2`) |
| 5 | OTA2 output stage `W2P/W2N` 80/40 → 120/60 µm (+50 % current); output per-side caps `WCOS` 18.3 → 30 µm | Open issue 4: smallest worst-case settling error that was found inside the cost limit | `dev-revd-settle-01…05` |

Driver and flow changes: `sim/run_afe.py` freezes the netlist, every template and itself into
`$G1_RESULTS_ROOT/r1_afe/<run-id>/frozen/` at campaign start and simulates only those copies (`run.json` field
`netlist_sha256`, `frozen_inputs`). It also adds the D16 LSB, the 1 % overload threshold of 1.44 V, the `dev:<kind>:<variants>`
development campaign (`devvar()` lists every variant as netlist edits), subckt-scoped edits, cross corners `sf fs ssx ffx`,
the campaign `stbx`, an overshoot count in the CM-step reduction, and a validity flag `pm_valid` for loop-gain results.
The flag is false when the broken-loop phase rises more than 30° above its DC value (right-half-plane pole), and the
reduction then counts the margin as failed. New helpers: `sim/dev_summary.py` (development-sweep summary) and
`sim/apply_revd.py` (writes the screened variant into the netlist of record, so the netlist is exactly what was screened).
`sim/report_afe.py` has the revision-D LSB, the noise-margin criterion, the `stbx` reduction and the CM-step overshoot fields.

### Built against (revision D)

Same as revision C (table below): PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (checked by `flow/run.sh`
before every run), ngspice-46 (container build of 2026-07-27, banner read into each `run.json`), container image
`sha256:ddeb6957…bab2`. The cross corners use the PDK sections `mos_sf`/`mos_fs` (`cornerMOShv.lib`, listed in the
container on 2026-10-20). Run with `G1_CPUSET=106-108`, `G1_CPUS=3`.

### Status (revision D, run suffix `20261020d`)

Evidence: `sim/runs/<run-id>/run.json` (question, result, disposition, input sha256), `sim/results/<run-id>.json`,
reduced numbers in `sim/results/summary-20261020d.json`; raw decks, logs and waveforms in `<G1_RESULTS_ROOT>/r1_afe/<run-id>/`.

| Check | Criterion | Status | Evidence (run id) |
| --- | --- | --- | --- |
| Output swing (D16) | 1.44 Vpp differential at full input | **passed**: gain ×1 1.012–1.028 (36/35 = 1.029; TG and string tolerance), ×32 32.16–32.66; output 1.43–1.46 Vpp at 1.4 Vpp input; outputs 0.238–0.955 V in the THD runs | `r1afe-ac-20261020d`, `r1afe-tran-20261020d` |
| Output CM, all gains, corners, input CM | 0.600 V ± 30 mV | **passed**: 0.5935–0.5973 V at tt/ss/ff, every step, input CM 0.5/2.5/2.8 V (revision C 0.577–0.648 V); 0.594–0.597 V in the THD runs | `r1afe-ac-20261020d` |
| Stage-1 CM loop (OTA1, output break) | PM ≥ 60° at every step, tt/ss/ff, input CM 0.5/2.5/2.8 V, track and hold load | **passed**: worst 62.4° (ss, ×32, CM 0.5 V); ×8 worst 66.2 | `r1afe-stb-20261020d` |
| Stage-1 DM loop | PM ≥ 55° | **passed**: worst 64.4° (ff, ×8), GM ≥ 15.5 dB | `r1afe-stb-20261020d` |
| Stage-2 DM loop | PM ≥ 55° | **passed**: worst 67.7° (ff, ×1, hold load), GM ≥ 10.0 dB | `r1afe-stb-20261020d` |
| Stage-2 CM loop | PM ≥ 60° | **passed**: worst 61.3° (ff, ×16, hold load), GM ≥ 21.7 dB | `r1afe-stb-20261020d` |
| CMFB-node breaks (`cmfb1`, `cmfb2`) | informational (not a valid Nyquist break, see revision C finding 2) | **not applicable**: flagged `pm_valid = false` by the new check, as expected | `r1afe-stb-20261020d` |
| Loop gain at cross corners, ×1 and ×32, input CM 0.5/2.5 V | same PM limits at tt, ss, ff, sf, fs, ssx (ss, 3.6 V, −40 °C), ffx (ff, 3.0 V, 125 °C) | **failed at ffx**: dm1 52.8° (×1, CM 0.5 V), cm1 54.3° (×32, CM 2.5 V), cm2 59.6° (×32); **passed** at tt, ss, ff, sf, fs, ssx (worst: sf/fs cm1 64.3°, ss cm1 62.4°, ff cm2 62.7°) | `r1afe-stbx-20261020d`; candidate fix `dev-revd-ffx-02` |
| Anti-alias f_c | ≥ 1.0 MHz at every step, corner, input CM | **passed**: min 1.020 MHz (ss, ×32, CM 0.5 V); peaking ≤ 0.0001 dB | `r1afe-ac-20261020d` |
| CM-step transient (pin CM 2.45→0.6→2.45 V, vcm2 +50 mV, VDDA −0.2 V, full-scale sine), tt/ss/ff, ×1/×32 | no sustained oscillation (≤ 1 mV pp before the next event); the test flags `dev-revb-02` | **passed**: ≤ 0.24 mV pp; `dev-revb-02` 1490 mVpp. Recorded (not a criterion here, see the trade-off table): pin step settles to 5 mV in ≤ 596 ns, up to 3 excursions beyond 5 mV at ×32 (large signal: 200–360 mV stage-1 CM excursion); vcm2 step ≤ 1 overshoot, ≤ 82 ns to 2 % | `r1afe-cmstep-20261020d` |
| Settling into the r1_adc T/H (2.8 pF/side, top plate 0 V, 250 ns), 5 levels, tt/ss/ff, ×1/×32 | total error ≤ 0.25 LSB (INTERFACES.md) | **failed**: worst 0.38 LSB (tt ×32); ss ×1 0.37, ss ×32 0.28, ff ×32 0.23 LSB. Revision C: 1.29 LSB (at its 0.488 mV LSB) | `r1afe-settle_adc-20261020d` |
| Same, non-linear residual after a linear gain/offset fit | ≤ 0.25 LSB (accepted criterion, see settling decision) | **passed**: ≤ 0.005 LSB; linear part a gain error of −0.023 % to +0.024 %, equal in both channels | `r1afe-settle_adc-20261020d` |
| Noise ×32, input-referred, 1 Hz–100 MHz | ≤ 35 µV rms with ≥ 5 % margin at ss (≤ 33.25 µV) | **passed**: 31.0 µV ss (11 % margin), 26.1 tt, 23.3 ff | `r1afe-noise-20261020d` |
| Noise ×1, output | ≤ 0.41 LSB rms (180 µV at the D16 LSB) | **passed**: 164 µV = 0.37 LSB (ss); 145 tt, 132 ff | `r1afe-noise-20261020d` |
| THD at 100 kHz, 1.44 Vpp out, ×1/×32, tt/ss/ff | ≤ 0.1 % | **passed**: worst 0.025 % (−72.0 dB, ss ×1) | `r1afe-tran-20261020d` |
| Gain steps ×1–×32, both channels | steps present; ratio error recorded | **passed**: step-ratio error ≤ 1.41 % (×32) | `r1afe-ac-20261020d` |
| Pole matching, 20 MC samples per corner, every step | \|Δf3\| ≤ 1 % | **passed**: worst 0.961 % (ss), σ ≤ 0.36 %; phase mismatch at 100 kHz ≤ 0.078°; gain mismatch ≤ 1.01 % (removed by GAIN_RATIO). Margin 0.04 % | `r1afe-ac_mc-20261020d` |
| Temperature −40/27/125 °C at tt | f_c ≥ 1 MHz; gain recorded | **passed**: f_c min 1.371 MHz (125 °C, ×32); gain spread ≤ 0.53 % (×32) | `r1afe-temp-20261020d` |
| Input CM 0–3.3 V with the stock analog pad | gain within 2 %; pad current < 1 µA at 2.8 V | **passed**: gain variation ≤ 1.54 % (ss ×32); pad current ≤ 4.1 nA at 2.8 V, 13 nA at 3.0 V | `r1afe-cm-20261020d` |
| PSRR from VDDA, 20 kHz and 1 MHz (20 MC samples, tt), at the 1.44 Vpp swing | ≥ 40 dB | **passed**: worst 54.3 dB (20 kHz), 54.7 dB (1 MHz). Recorded: VDDA → output CM −41.5 to −43.1 dB at 20 kHz (revision B −58 to −61 dB), −28 to −31 dB at 1 MHz; the `l2` bias change raised the low-frequency CM supply coupling (10 mV ripple → ≈ 85 µV CM, no DM effect) | `r1afe-psrr-20261020d` |
| Input overload ±1.0 V differential, recovery | recorded (1 LSB = 0.439 mV, 1 % = 14.4 mV) | **recorded**: ×32 recovery to 1 LSB ≤ 1236 ns (ss), to 1 % ≤ 882 ns; ×1 ≤ 842 ns to 1 LSB. Output CM falls to 0.148 V during ×32 overload (revision C 0.06 V) | `r1afe-overload-20261020d` |
| Source impedance 0/100/300/1000 Ω per pin | gain change recorded | **recorded**: at 1 kΩ ×1 −2.4 to −2.8 %, ×8/×32 −16.6 to −18.8 %; at 100 Ω ≤ 2.3 % | `r1afe-rsrc-20261020d` |
| Loop-gain method check (toy loop) | matches an exact return ratio | **passed** (re-run, independent of the netlist) | `r1afe-stbval-20261020d` |
| Gain-switch transients, bias from r1_bgr, c1..c4 level shifters | — | **not run** | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

### Settling decision (item 4; deviation from INTERFACES.md for the coordinator)

INTERFACES.md (AFE → ADC) asks for a total settling error ≤ 0.25 LSB in the 250 ns track window. Revision D does
**not** meet it. The worst total error is 0.38 LSB (tt ×32). The output-stage option was tried first, inside the cost
limit of 1 mA and 0.02 mm². OTA2 output current ×1.5 or ×2 and per-side reservoir caps of 30 or 40 µm reached 0.12–0.30 LSB
at ss ×32 alone. But at three corners the worst total stayed at 0.38 LSB (WCOS 30 µm) or 0.79 LSB (WCOS 40 µm). The error is
the sum of two terms with opposite signs, an RC tail through R_o and the OTA2 recovery from the CDAC kick. A
cancellation at one corner does not hold at the others. A switched OTA2 Cc reached 0.20 LSB, but it made OTA2
marginally stable (DM2 PM 39.8°) and was rejected. Revision C's development data needed +0.8 mA for 0.36 LSB (old LSB).

The decision is therefore the fallback that the task allows: the linear part (a gain error of −0.023 % to +0.024 %,
equal in both channels, stable within a chip at a given corner) is calibrated by the ADC/host gain correction (the per-step GAIN_RATIO
registers). The accepted criterion is the non-linear residual, ≤ 0.25 LSB; simulated ≤ 0.005 LSB. Residual risk: the
linear part drifts with temperature by up to about 0.05 % (≈ 0.4 LSB at full scale, tt→ss spread) if the gain calibration is done at one
temperature only. **Coordinator action**: change the AFE → ADC row of INTERFACES.md from "settling ≤ 0.25 LSB" to "non-linear
settling residual ≤ 0.25 LSB; linear settling gain error ≤ 0.03 % removed by the gain calibration", or reject and
ask for an output buffer (estimated > 1 mA).

### Item 3 trade-off (stage-1 CM phase margin vs f_c)

| Netlist | CM1 PM ×8 / ×32, worst over tt/ss/ff and input CM (°) | f_c min (MHz) | Note |
| --- | --- | --- | --- |
| Revision C | 54.1 / 54.3 | 1.023 | failed PM |
| D16 + `l2`, no stage-1 change | 54.1 / 54.5 | 1.034 | `dev-revd-cm1-01` |
| Cross Miller `cx26.3_14.4` (alone) | 68.3 / 64.4 | 0.977 | failed f_c |
| **Revision D** (`cx25_13` + `np2`) | 66.2 / 62.4 | 1.020 | both met at tt/ss/ff; ffx cross corner 54.3° (×32) failed |

Both targets are met at tt/ss/ff, so the CM-step fallback acceptance is not used. The CM-step data are recorded in the status table.

### Regression check list (every item that passed in revision C, re-run in revision D)

| Revision-C pass | Revision-D result | Run |
| --- | --- | --- |
| Loop-gain method (toy loop) | passed | `r1afe-stbval-20261020d` |
| Stage-1 DM PM ≥ 55° (rev C 68.0°) | passed, 64.4° (lower: cross caps, still > 55°) | `r1afe-stb-20261020d` |
| Stage-2 DM PM ≥ 55° (65.6°) | passed, 67.7° | `r1afe-stb-20261020d` |
| Stage-2 CM PM ≥ 60° (63.2°) | passed, 61.3° (lower, margin 1.3°) | `r1afe-stb-20261020d` |
| Loop-gain coverage (tt/ss/ff, CM 0.5/2.5/2.8 V, six steps, track and hold load) | passed, same coverage | `r1afe-stb-20261020d` |
| CM-step test, no sustained oscillation, detects `dev-revb-02` | passed | `r1afe-cmstep-20261020d` |
| Gain steps present, ratio error recorded (1.70 %) | passed, 1.41 % | `r1afe-ac-20261020d` |
| f_c ≥ 1 MHz (1.023 MHz) | passed, 1.020 MHz (margin 2.0 %) | `r1afe-ac-20261020d` |
| Pole matching ≤ 1 % (0.96 %) | passed, 0.961 % | `r1afe-ac_mc-20261020d` |
| THD ≤ 0.1 % (0.032 %) | passed, 0.025 % | `r1afe-tran-20261020d` |
| Settling non-linear residual (0.082 LSB) | passed, 0.005 LSB | `r1afe-settle_adc-20261020d` |
| Noise ×32 ≤ 35 µV (34.8 µV) | passed, 31.0 µV | `r1afe-noise-20261020d` |
| Noise ×1 ≤ 0.41 LSB (0.36 LSB at 0.488 mV) | passed, 0.37 LSB at 0.439 mV | `r1afe-noise-20261020d` |
| Temperature f_c ≥ 1 MHz (1.371 MHz) | passed, 1.371 MHz | `r1afe-temp-20261020d` |
| Input CM with pad: gain ≤ 2 %, pad current < 1 µA (1.56 %, 49 nA) | passed, 1.54 %, 4.1 nA | `r1afe-cm-20261020d` |
| PSRR ≥ 40 dB (51.0 dB) | passed, 54.3 dB | `r1afe-psrr-20261020d` |
| Overload, source impedance (recorded) | recorded | `r1afe-overload-20261020d`, `r1afe-rsrc-20261020d` |

Rule for later revisions: a change is not done until every row of this list is re-run and still passes. The output-CM
failure of revision C was a regression of this kind (revision B passed, revision C failed, and no list caught it).

### Area and current (revision D)

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.099 mm² (MOS 0.029, rppd 0.033, MIM 0.038); revision C 0.091 | **estimated**, `sim/area_estimate.py` → `sim/results/area_estimate_revD.json` |
| of which item 5 (noise, `np2`) | ≈ +0.003 mm² (MOS) | estimated; limit 0.01 mm² |
| of which item 4 (settling: output stage ×1.5, WCOS 30 µm) | ≈ +0.004 mm²; +0.2 mA | estimated / simulated; limit 0.02 mm², 1 mA |
| of which item 2 (`l2`), item 3 (cross Miller) | ≈ +0.0002 mm² (MOS), ≈ +0.0025 mm² (MIM) | estimated |
| VDDA current, both channels | 1.71–2.00 mA (tt 1.76–1.95, ss 1.71–1.90, ff 1.93–2.00); revision C 1.53–1.86 mA | simulated, operating points in `r1afe-ac-20261020d` |
| Power | 5.1–7.2 mW | simulated current × VDDA |

### Open issues (revision D)

1. **Cross corner ffx (ff, 3.0 V, 125 °C) fails**: dm1 52.8° (×1, CM 0.5 V), cm1 54.3° (×32, CM 2.5 V), cm2 59.6°.
   Candidate fix for dm1: OTA1 switched Miller part 20.4 → 24 µm (`ccb24`, dm1 → 56.7°, f_c unchanged,
   `dev-revd-ffx-02`). cm1 and cm2 at ffx need a further change (the larger cross cap gives only +0.9°). Not applied:
   the campaign of record was running.
2. **Settling total error 0.38 LSB** against 0.25 LSB in INTERFACES.md: the decision above needs the coordinator
   (interface change or output buffer).
3. **Stage-2 CM PM margin is 1.3°** (61.3°, ff ×16 hold load) and f_c margin is 2 % (1.020 MHz). Layout parasitics
   at the OTA2 output and at the stage-1 summing nodes will move both.
4. **CM-step large-signal ringing**: the 1.85 V pin-CM step at ×32 gives up to 3 excursions beyond 5 mV and settles in
   ≤ 596 ns (no sustained oscillation). Head CM steps of this size are not expected in operation.
5. Revision-C open issues 6–7 stay open: source impedance (5 kΩ input units at ×8–×32), interfaces not designed here
   (PGA_GAIN decoder and level shifters, `vcm2` from r1_adc, bias from r1_bgr), VCM1 from VDDA.
6. Checks marked **not run** in the status table.

### Failures and mistakes (revision D)

| # | What happened | Class | Record |
| --- | --- | --- | --- |
| 1 | Revision C attributed the output-CM error to the OTA2 fixed/CMFB sink split. The cause was the OTA2 mirror length (l = 2 µm sinks and sources from l = 1 µm references). Revision B had the same error at a smaller size (+28 mV ss). The split only made it larger. | estimation | `dev-revd-ocm-01` |
| 2 | Revision C failed output CM after revision B passed it; no regression list existed. | regression | regression list above |
| 3 | CM-only Miller caps cz → vcms (`cmm8/14/20`) formed a local positive loop. The broken-loop return ratio had a right-half-plane pole, and the Bode PM came out above 360°. The idea was wrong. | functional-bug | `dev-revd-cm1-01` |
| 4 | The loop-gain reduction did not detect a right-half-plane pole and printed PM > 360° without a warning. Fixed: `pm_valid` flag; an invalid margin counts as failed. | verification-gap | `run_afe.py` `stb_post` |
| 5 | The cross-Miller arithmetic (DM cap = F² − X² kept at 22² µm²) predicted no f_c change; f_c fell 3–6 %. | estimation | `dev-revd-cm1ac-02`, `-03` |
| 6 | Switched OTA2 Cc (`c2sw`) was screened for settling before its loop gain. It gave 0.12–0.20 LSB, but DM2 PM fell to 39.8° (at high frequency the stage-2 feedback factor is set by Cf2 and is near 1 at every step). Two combined campaigns were spent on it. | planning | `dev-revd-settle-01…03`, `dev-revd-comb-*-01` |
| 7 | Settling screens at one corner (ss ×32) suggested 0.12–0.14 LSB; at three corners the same variants gave 0.38–0.79 LSB (cancellation of two opposite terms). | verification-gap | `dev-revd-settle-04`, `-05` |
| 8 | First `dev_summary.py` split variant names at `_`, and a shell filter (`grep -v cm2`) also removed every `cm2.5` line; a summary was misread for one step (no wrong decision taken). | tooling | — |
| 9 | Run `dev-revd-ffx-01` aborted before any job: the variant name `cxs14.5` matched the `cx` branch first. Re-run as `-02`. | tooling | `runs/dev-revd-ffx-01/run.json` |
| 10 | Revision C ran campaigns on the live netlist (`r1afe-settle_adc-20261020c` aborted after an edit). Fixed: per-campaign frozen copies. | process-hygiene | `run_afe.py` `freeze()` |
| 11 | Two campaigns shared CPUs 106–108 for 6 minutes (`dev-revd-ffx-02` next to `20261020d`); the allocation was not exceeded, wall time only. | planning | — |
| 12 | "The two mixed corners" in the task is ambiguous. Taken as the MOS corners sf and fs (3.3 V, 27 °C); the supply/temperature cross terms ssx and ffx were added. | spec-ambiguity | `r1afe-stbx-20261020d` |

### Files (revision D additions)

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision D netlist of record |
| `schematic/r1_afe_revC.spice` | revision C netlist (runs `r1afe-*-20261020c2`) |
| `sim/run_afe.py` | driver (freeze, D16 LSB, `dev:` campaigns, `devvar()`, `stbx`, cross corners, `pm_valid`) |
| `sim/report_afe.py` | reductions (revision D LSB and criteria, `stbx`, CM-step overshoots) |
| `sim/run_all.sh` | campaign set, revision D default list |
| `sim/dev_summary.py`, `sim/apply_revd.py` | development-sweep summary; writes the screened variant into the netlist |
| `sim/results/summary-20261020d.json`, `sim/results/area_estimate_revD.json` | reduced numbers and area estimate of revision D |
| `sim/runs/r1afe-*-20261020d/`, `sim/runs/dev-revd-*/` | run records (campaign of record; development screens) |

Reproduce: `G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT`, then
`sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh 20261020d` and `cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py 20261020d`.

---

# Revision C record (superseded by revision D)

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT` before every run; copied into each `run.json` |
| ngspice | ngspice-46 (container build of 2026-07-27) | `ngspice -v` banner, read by `sim/run_afe.py` into each `run.json` |
| Container image | `sha256:ddeb6957…bab2` (`tapeoutbench-eda:latest`) | identity verified by `flow/run.sh` |
| Models | `cornerMOShv.lib`, `cornerMOSlv.lib`, `cornerRES.lib`, `cornerCAP.lib`, `cornerDIO.lib`; PSP 103 / r3_cmc OSDI (`sim/.spiceinit`) | deck headers (`sim/common_head.inc`) |
| IO cell | `sg13g2_IOPadAnalog` from `libs.ref/sg13g2_io/spice/sg13g2_io.spi` (stock, with the `dantenna` diodes) | `sim/tb_afe_cm.cir` |
| xschem / KLayout / CACE | not used in this step | — |

The IHP `TO_Nov2024` BG/OTA was not used (single-ended; this block needs a fully differential OTA), so it is not
cloned into `third_party/`. The G1 `g1_sense` OTA (`designs/g1-guardian/blocks/g1_sense/sim/netlist/g1_ota.spice`)
is the style reference for bias and cascode generation; no G1 file is copied.

## What it is

Two identical channels (sine `XSIN`, cosine `XCOS`). Each channel has two inverting, fully differential stages and
an output R-C:

```
 SIN_P/N pads              stage 1: PGA (rail-to-rail OTA1)          stage 2: filter + level shift (OTA2)      to r1_adc T/H
 (0.5-2.8 V CM)         Rf1 = 40k || Cf1 1.44 pF (pole ~2.8 MHz)    Rf2 = 20k || Cf2 2.85 pF (pole ~2.8 MHz)
      o--[n1 x 40k]--[TG]--+--|\                 +--[1 or 4 x 14k]--[TG]--+--|\              R_o 3k
                           |  |OTA1>-- out CM 1.0 V ---                   |  |OTA2>-- out CM --/\/\--+-- OUT_P/N
      o--[n1 x 40k]--[TG]--+--|/      (VDDA x 0.30)                       +--|/   0.6 V (vcm2)        |   C_o 3 pF diff
                     n1 = 1, 2, 4, 8                       gain 8/7 or 32/7                            + 0.5 pF/side
```

- Overall gain = step × 8/7 (revision C, D11), so 1.4 Vpp at ×1 and 43.75 mVpp at ×32 give **1.6 Vpp differential**
  at the output. Revision B used 10/7 (2.0 Vpp). D16 (2026-10-20, after the revision-C campaigns started) sets the
  ADC full scale to ±0.9 V and the AFE target to 1.44 Vpp: revision C keeps 8/7, so the ADC sees 1.6 Vpp = 89 % of
  its full scale (open issue 1).
- Gain steps: stage 1 uses n1 parallel 40 kΩ units against one 40 kΩ feedback unit. Every unit, including the
  feedback unit, has the same transmission gate in series, so the TG on-resistance cancels in the ratio. Stage 2
  uses one or four 17.5 kΩ strings against 20 kΩ (revision B: 14 kΩ).

| PGA_GAIN code | Step | n1 (stage 1) | stage 2 | c1 c2 c3 c4 |
| --- | --- | --- | --- | --- |
| 0 | ×1 | 1 | 8/7 | 0 0 0 0 |
| 1 | ×2 | 2 | 8/7 | 1 0 0 0 |
| 2 | ×4 | 4 | 8/7 | 1 1 0 0 |
| 3 | ×8 | 8 | 8/7 | 1 1 1 0 |
| 4 | ×16 | 4 | 32/7 | 1 1 0 1 |
| 5 | ×32 | 8 | 32/7 | 1 1 1 1 |

- Anti-alias filter: one real pole per stage, set by Rf·Cf and independent of the gain step, plus the OTA
  closed-loop poles and the output R-C (≈ 6 MHz). The two channels are matched by layout symmetry of identical
  rppd units and MIM capacitors.
- Input common mode: in an inverting stage the OTA input sees (V_in,cm·G + V_out,cm)/(G + 1). At ×8 this follows
  the pin almost fully (0.5–2.8 V), so OTA1 has NMOS and PMOS input pairs (rail-to-rail) into one folded cascode.
  OTA2 sees an almost constant input CM (0.84–0.94 V) and has a PMOS pair only (lower noise).
- Level shift: stage 1 runs at 1.0 V output CM, stage 2 at 0.6 V. The resistor network carries
  (1.0 − 0.6) V / (R_in2 + R_f2) ≤ 15 µA per side (revision C). Revision A first used 1.65 V for stage 1. The 51 µA level-shift
  current then starved the stage-1 output device (THD 2.9 % at ff, run `dev-quick2-06`).
- Revision-C compensation (from the loop-gain analysis): OTA1 Miller capacitance 22 µm square fixed plus 20.4 µm
  square switched in by `c3b` (connected for n1 < 8: ×1, ×2, ×4, ×16; open at ×8 and ×32), zero resistor 3.4 kΩ,
  CMFB sense capacitors 22 µm square (lead at the CM sense node), PMOS-pair tail 90 µA (was 60 µA). OTA2: CMFB pair
  32/1, fixed sink 20 µm (from `ibias`) and CMFB sink 10 µm (the CMFB controls part of the sink current, not all),
  sense capacitors 14 µm square, Cc 18 µm square, zero resistor 1.6 kΩ. The OTA1 subcircuit has two new ports
  `cen cenb` (driven by `c3b c3` inside the channel); the top-level ports are unchanged.
- Output common mode 0.6 V: **assumption** from the r1_adc spec row (1.2 V domain, 2.4 Vpp differential FS) and the
  r1_adc schematic of 2026-10-20 (`../r1_adc/schematic/r1_adc.spice`: top-plate sampling on the CDAC, PMOS
  comparator input for a CM falling from 0.6 V toward 0 V). `vcm2` is a port. It must come from the r1_adc
  reference (VREF/2), not from this block.
- Bias: 10 µA into each OTA (`ib_s1`, `ib_s2`, `ib_c1`, `ib_c2`) from r1_bgr. The testbenches use ideal sources.
- Gain controls `c1..c4` are 3.3 V signals. The decoder from `PGA_GAIN` and the 1.2 V → 3.3 V level shifters are
  not in this block (open issue 6).

Ports of `r1_afe` (`schematic/r1_afe.spice`, unchanged in revision C): `sinp sinn cosp cosn` (pads), `souts_p souts_n soutc_p soutc_n`
(to the T/H), `vcm2` (0.6 V), `ib_s1 ib_s2 ib_c1 ib_c2` (10 µA each, sunk), `c1 c2 c3 c4`, `vdd` (VDDA), `vss`.
Connect the AFE input to the `pad` terminal of `sg13g2_IOPadAnalog`, not to `padres`. The 587 Ω secondary
resistor would add to the 5 kΩ input units without a matching feedback part.

## Status (revision C, run suffix `20261020c2`; LSB = 2.0 V / 4096 = 0.488 mV unless stated)

All numbers are **simulated** (ngspice-46, IHP SG13G2 `84374023`). Evidence: `sim/runs/<run-id>/run.json` and
`sim/results/<run-id>.json`; reduced numbers in `sim/results/summary-20261020c2.json`.

| Check | Criterion | Status | Evidence (run id) |
| --- | --- | --- | --- |
| Loop-gain method | Tian double injection matches an exact return ratio | **passed**: max relative error 4.7e-8, 10 Hz–1 GHz | `r1afe-stbval-20261020c` |
| Stage-1 differential loop (OTA1, broken at its outputs) | PM ≥ 55° | **passed**: worst PM 68.0° (ff, ×8), worst GM 14.8 dB | `r1afe-stb-20261020c2` |
| Stage-1 common-mode loop (CMFB and the CM path through the input pairs) | PM ≥ 60° | **failed**: worst PM 54.3° (ss, ×32, input CM 2.5 V), GM ≥ 16.2 dB. The u3 netlist reached ≥ 64.1° but failed f_c (see row "Anti-alias f_c"; open issue 2) | `r1afe-stb-20261020c2`; u3: `r1afe-stb-20261020c` |
| Stage-2 differential loop (OTA2) | PM ≥ 55° | **passed**: worst PM 65.6° (ff, ×1, hold load), worst GM 10.8 dB | `r1afe-stb-20261020c2` |
| Stage-2 common-mode loop | PM ≥ 60° | **passed**: worst PM 63.2° (ss, ×16, CM 0.5 V), GM ≥ 22.0 dB | `r1afe-stb-20261020c2` |
| Loop-gain coverage | tt/ss/ff, input CM 0.5/2.5/2.8 V, all six steps, track load (100 Ω + 2.8 pF) and hold load | **passed**: 12 jobs × 6 steps × 6 breaks; input CM 1.65 V and the input-node cross-check breaks ran on u3 only | `r1afe-stb-20261020c2`, `r1afe-stb-20261020c` |
| Method check on revision B | revision B and the `dev-revb-02` variant that oscillated | **recorded**: revision B worst CM PM 13.2° (ss ×32), DM PM 16.2° (×1); `dev-revb-02` CM PM −11.1° (tt ×32), so the analysis predicts the oscillation | `r1afe-stb_revb-20261020c` |
| CM-step transient (pin CM 2.45→0.6→2.45 V, vcm2 +50 mV, VDDA −0.2 V, full-scale 100 kHz sine), tt/ss/ff, ×1/×32 | no sustained oscillation: CM ≤ 1 mV pp before the next event; the test must flag `dev-revb-02` | **passed**: ≤ 0.31 mV pp; pin-CM step settles to 5 mV in ≤ 614 ns; `dev-revb-02` shows a sustained 1.49 Vpp stage-1 CM oscillation | `r1afe-cmstep-20261020c2` |
| Gain steps ×1–×32, both channels, tt/ss/ff, CM 0.5/2.5/2.8 V | steps present; ratio error recorded | **passed**: step-ratio error ≤ 1.70 % (×32) vs 2^k; host calibration per step | `r1afe-ac-20261020c2` |
| Anti-alias f_c | ≥ 1 MHz at every step, corner, CM | **passed**: min 1.023 MHz (ss, ×32, CM 0.5 V); peaking ≤ 0.0001 dB | `r1afe-ac-20261020c2` |
| Pole matching, 20 MC samples per corner (tt/ss/ff), every step | \|Δf3\| ≤ 1 % | **passed**: worst 0.96 % (ss), σ ≤ 0.43 %; phase mismatch at 100 kHz ≤ 0.080°; gain mismatch ≤ 1.18 % (removed by GAIN_RATIO) | `r1afe-ac_mc-20261020c2` |
| THD at 100 kHz, 1.6 Vpp out, ×1 and ×32, tt/ss/ff | ≤ 0.1 % | **passed**: worst 0.032 % (−70.0 dB, ss ×1); outputs 0.179–1.041 V | `r1afe-tran-20261020c2` |
| Settling into the INTERFACES.md T/H (2.8 pF/side, top plate 0 V, 250 ns), 5 levels (±FS, ±FS/2, FS/4) | total error ≤ 0.25 LSB | **failed**: error at full scale ≤ 1.29 LSB (ss ×32), 0.25 LSB (tt ×1). With the D16 LSB (1.8 V/4096 = 0.439 mV): ≤ 1.44 LSB | `r1afe-settle_adc-20261020c2` |
| Same, after removing a linear gain/offset fit | non-linear residual ≤ 0.25 LSB | **passed**: ≤ 0.082 LSB (0.091 LSB at the D16 LSB); the linear part is a gain error ≤ 0.079 % that is the same in both channels | `r1afe-settle_adc-20261020c2` |
| Noise ×32, input-referred, 1 Hz–100 MHz | ≤ 35 µV rms | **passed (small margin)**: 34.8 µV ss, 28.1 µV tt, 24.8 µV ff | `r1afe-noise-20261020c2` |
| Noise ×1, output | ≤ 0.41 LSB rms | **passed**: 178 µV = 0.36 LSB (ss); 0.41 LSB at the D16 LSB | `r1afe-noise-20261020c2` |
| Temperature −40/27/125 °C at tt (3.3 V) | f_c ≥ 1 MHz; gain recorded | **passed**: f_c min 1.371 MHz (125 °C, ×32); gain spread ≤ 0.59 % (×32) | `r1afe-temp-20261020c2` |
| Input overload: ±1.0 V differential (2 Vpp), 10 µs each polarity, then +FS/2 | recovery time recorded | **recorded**: ×32 recovery to 1 LSB ≤ 1232 ns (ss), to 1 % ≤ 872 ns; ×1 ≤ 840 ns. Output CM falls to 0.06 V during ×32 overload | `r1afe-overload-20261020c2` |
| Source impedance 0/100/300/1000 Ω per pin | gain change recorded | **recorded**: at 1 kΩ, ×1 −2.1 to −2.8 %, ×8–×32 −14.7 to −18.8 % (5 kΩ input units); 100 Ω: ≤ 2.3 % | `r1afe-rsrc-20261020c2` |
| Input CM 0–3.3 V with the stock analog pad | gain within 2 %; pad current < 1 µA at 2.8 V | **passed**: gain variation ≤ 1.56 %; pad current ≤ 49 nA at 2.8 V | `r1afe-cm-20261020c2` |
| PSRR from VDDA, 20 kHz and 1 MHz (20 MC samples, tt) | ≥ 40 dB (derived in revision B) | **passed**: worst 51.0 dB | `r1afe-psrr-20261020c2` |
| Output CM | 0.6 V ± 30 mV (limit set in revision B) | **failed**: 0.577–0.648 V (ss +48 mV). Revision B: 0.600–0.628 V. Cause: the OTA2 fixed-sink split that lowers the CM loop gain (open issue 3) | `r1afe-ac-20261020c2` |
| Output swing 1.44 Vpp (D16, ±0.9 V ADC full scale) | stage-2 gain ≈ 36/35 | **not run**: D16 arrived during the final campaign; revision C keeps 8/7 (1.6 Vpp = 89 % of ±0.9 V) | — |
| Supply-corner cross terms, sf/fs MOS corners, gain-switch transients | — | **not run** | — |
| Bias from r1_bgr, level shifters for c1..c4 | — | **not run** (blocks not available) | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

Corners: tt = mos_tt/res_typ/cap_typ, 3.3 V, 27 °C; ss = mos_ss/res_wcs/cap_wcs, 3.0 V, 125 °C; ff = mos_ff/res_bcs/
cap_bcs, 3.6 V, −40 °C.

### Stability findings (revision C)

1. Revision B was far from the targets. The stage-1 differential loop had a PM of 15–17° (GM 2.5 dB) at ×1 at all
   corners. The closed-loop AC check could not see this, because the loop crosses unity near 80 MHz, where the
   closed-loop response is already about 30 dB down. The stage-1 CM loop had a PM of 13° at ss ×32. The CMFB
   variant `dev-revb-02` had a negative CM margin, which matches its oscillation in the transient runs.
2. The CMFB return ratio at the CM sense node has a DC phase of 180° at several operating points. When the PMOS-pair
   tail of the rail-to-rail OTA1 loses headroom (OTA input CM 1.7–2.3 V), the input pairs form a positive CM loop
   with a gain above 1. A break at the CMFB input therefore does not give a valid Nyquist test. The CM criterion uses
   the break at the OTA outputs, which contains all CM paths. The DM break at the outputs gives the same result as
   the break at the inputs (cross-check in `r1afe-stb-20261020c`).
3. Fixes: a larger Miller capacitor and zero resistor (DM1); CM-sense feed-forward capacitors (they cancel the pole
   of the 200 kΩ sense resistors and the CMFB-pair gate); and in OTA2, a CMFB that controls only part of the sink
   current (CM2 changes from 30° to 63°). The full Miller capacitor reduced f_c at ×8/×32 with input CM 0.5 V
   (only the PMOS pair is active) to 0.836 MHz. Part of the capacitor is therefore switched off at n1 = 8. This
   costs CM1 margin at ×8/×32 (54° instead of 64°).
4. Development sweeps: `dev-stbsweep1..6-01`, `dev-fcsweep-01`, `dev-ccsw-01` to `dev-ccsw4-01` (each `run.json` gives
   the question and the result).

### Numbers (simulated, revision C)

Gain and f3 (AC, input CM 2.5 V; f3 min over CM 0.5/2.5/2.8 V and all corners in the last column):

| Step | gain tt | f3 tt (MHz) | f3 ss (MHz) | f3 ff (MHz) | f3 min (MHz) |
| --- | --- | --- | --- | --- | --- |
| ×1 | 1.134 | 1.652 | 1.297 | 2.119 | 1.286 |
| ×2 | 2.263 | 1.623 | 1.271 | 2.082 | 1.238 |
| ×4 | 4.514 | 1.565 | 1.204 | 2.014 | 1.144 |
| ×8 | 9.017 | 1.543 | 1.177 | 1.998 | 1.125 |
| ×16 | 18.031 | 1.462 | 1.111 | 1.889 | 1.038 |
| ×32 | 36.008 | 1.439 | 1.081 | 1.874 | 1.023 |

Noise (1 Hz–100 MHz): ×1 output 157/178/142 µV rms (tt/ss/ff); ×32 input 28.1/34.8/24.8 µV rms; ×32 input density at
1 kHz / 100 kHz / 1 MHz at ss: 171 / 29 / 19 nV/√Hz. At ss the ×32 margin is 0.6 %. The 8/7 stage-2 gain and the
OTA2 changes moved it from 35.3 to 33.7 µV (u3), and the switched Miller capacitor and the larger PMOS tail moved it
back to 34.8 µV. The input pair and the first-stage resistors were not changed, so this item has no area cost.

THD at 100 kHz (1.6 Vpp out): tt 0.012 / 0.009 %, ss 0.032 / 0.027 %, ff 0.007 / 0.006 % (×1 / ×32).

Settling into the r1_adc T/H, 250 ns track (error at the end of track; LSB 0.488 mV):

| Corner | ×1 error at FS (LSB) | ×32 error at FS (LSB) | ×32 gain error (%) | non-linear residual, worst (LSB) |
| --- | --- | --- | --- | --- |
| tt | 0.25 | 0.97 | 0.057 | 0.082 |
| ss | 0.22 | 1.29 | 0.079 | 0.045 |
| ff | 0.12 | 0.51 | 0.030 | 0.065 |

The error at the end of track is the sum of a slow under-settling tail and an overshoot left by the kick (the 2.8 pF
CDAC charges from 0 V on each side; only 0.5 pF per side of the output network is a CM reservoir). In the
development sweeps (`dev-settlesweep1-01`, `dev-settlesweep2-01`, ss, +FS), a reservoir or OTA2 output-stage changes
reduce the ×32 error to 0.36–0.52 LSB. The 0.36 LSB case needs three times the OTA2 output current (+0.8 mA). The
low values in some variants come from cancellation of the two terms with opposite signs between ×1 and ×32, so they
are not robust. Revision C keeps the revision-B output network.

## Area and current (revision C)

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.091 mm² (MOS 0.025, rppd 0.033, MIM 0.034) | **estimated**, `sim/area_estimate.py` → `sim/results/area_estimate_revC.json` (revision B: 0.0835 mm²). The +0.007 mm² is MIM: the OTA1 Miller and CM-sense capacitors and the OTA2 sense capacitors |
| VDDA current, both channels | 1.53–1.86 mA (tt 1.59–1.78, ss 1.53–1.72, ff 1.78–1.86) | simulated, operating points in `r1afe-ac-20261020c2`. The OTA1 PMOS tail adds about 0.06 mA to revision B |
| Power | 4.6–6.7 mW | simulated current × VDDA |

## Open issues (revision C)

1. **D16 output target 1.44 Vpp (±0.9 V ADC full scale) is not applied.** Revision C keeps stage-2 gain 8/7 (1.6 Vpp
   = 89 % of full scale). To apply D16, set R_in2 to 19.44 kΩ (gain 36/35 and 144/35), then re-run the gain-step,
   settling, loop-gain (stage 2) and noise decks.
2. **Stage-1 CM loop PM 54.3° at ×8/×32 (target 60°)**, with GM ≥ 16 dB. The CM-step test shows no ringing problem
   (settling ≤ 614 ns, ≤ 0.31 mV residual). Candidate fixes: a CMFB with its own compensation, or a
   rail-to-rail input stage whose tail current does not depend on the input CM (it now forms a positive CM loop near
   the PMOS-pair cut-off).
3. **Output CM 0.577–0.648 V** (limit ±30 mV set in revision B). This comes from the OTA2 fixed/CMFB sink split. A
   bandgap-referenced fixed sink, or a smaller fixed fraction with retuned sense caps, would restore the accuracy.
   Confirm the ADC input CM tolerance with the r1_adc owner.
4. **Settling: the total error at full scale is ≤ 1.29 LSB**, and it is linear: the residual is ≤ 0.082 LSB and both
   channels have the same gain error. If the per-step GAIN_RATIO calibration is not accepted as the remedy, an
   output buffer per side or about 0.8 mA more OTA2 output current is needed (see the settling paragraph).
5. **×32 noise margin is 0.6 % at ss** (34.8 µV). To add margin: input units of 20 kΩ (halves the input impedance)
   or a larger NMOS pair for flicker noise.
6. **Source impedance**: the 5 kΩ input units at ×8–×32 give −16.6 % gain at 1 kΩ (tt). The effect is the same in
   both channels for equal head impedance, but it depends on the temperature of the head.
7. Revision-B items 5–8 (step accuracy, interfaces not designed here, input impedance, VCM1 from VDDA) stay open.
8. Checks marked **not run** in the status table.

Run-record notes: the revision-C first pass (`r1afe-*-20261020c`, u3 netlist without the switched capacitor) is
kept as superseded. `r1afe-settle_adc-20261020c` was aborted after the netlist changed during the campaign. The
`r1afe-stb_revb-20261020c` run and the revision-B rows of `r1afe-cmstep-20261020c` remain valid.

## Files

| Path | Content |
| --- | --- |
| `schematic/r1_afe.spice` | revision C source (netlist of record): OTA1 (`r1_afe_ota`, with the switched Miller part), OTA2 (`r1_afe_ota2`), TG, inverter, resistor units, stage sides, channel, top |
| `schematic/r1_afe_revB.spice` | revision B source (runs `r1afe-*-20261020b`), superseded |
| `schematic/r1_afe_revA.spice` | revision A source (runs `r1afe-*-20261020a`) |
| `sim/common_head.inc`, `sim/gain_codes.inc` | model/corner header and gain-code table, inserted into every deck |
| `sim/tb_afe_ac.cir` | (a) gain, −3 dB, phase, peaking at every step, both channels; with `NMC > 1` the mismatch loop |
| `sim/tb_afe_tran.cir` | (b) 100 kHz full-scale sine, THD (fourier), swing, CM ripple |
| `sim/tb_afe_noise.cir` | (c) noise at every step (×1, ×32 required), spectra to the bulk directory |
| `sim/tb_afe_cm.cir` | (d) input CM 0–3.3 V with the stock analog pad on all four pins |
| `sim/tb_afe_psrr.cir` | (e) PSRR from VDDA at 20 kHz and 1 MHz |
| `sim/tb_afe_settle.cir`, `sim/tb_afe_settle_adc.cir` | 2 MSPS track-and-hold load: generic model (revisions A/B) and r1_adc-matched model (LSB a substitution since revision C) |
| `sim/tb_afe_stb.cir` | loop gain (Tian), six breaks: stage-1/2 DM and CM at the OTA outputs, CMFB sense node, stage-1 inputs; probes inserted by `run_afe.py` into a copy of the netlist |
| `sim/tb_stb_toy.cir` | validation of the loop-gain formula against an exact return ratio |
| `sim/tb_afe_cmstep.cir` | CM-step transient (pin CM, vcm2, VDDA steps with a full-scale sine) |
| `sim/tb_afe_overload.cir` | 2 Vpp input overload and recovery |
| `sim/tb_afe_rsrc.cir` | gain and f3 vs source impedance (derived from `tb_afe_ac.cir`) |
| `sim/stb_print.py`, `sim/stb_worst.py`, `sim/ccsw_summary.py` | print helpers for the loop-gain development runs |
| `sim/run_afe.py` | driver: campaigns, deck rendering, parallel ngspice, `results/<run-id>.json`, `runs/<run-id>/run.json` |
| `sim/run_all.sh` | the campaign set (revision C default list; `CAMPAIGNS=` selects) |
| `sim/report_afe.py`, `sim/summarize.py` | reduction to the numbers above; fills question/result/disposition in `run.json` |
| `sim/area_estimate.py` | area estimate |
| `sim/results/summary-20261020c2.json` | all reduced numbers of revision C (first pass: `summary-20261020c.json`; revision B: `summary-20261020b.json`; revision A: `summary-20261020a.json`) |
| `sim/results/area_estimate_revC.json` | area estimate of revision C (revision B: `area_estimate_revB.json`) |
| `sim/runs/*/run.json` | one record per run. `dev-*` runs are development iterations on earlier netlists, labelled superseded |
| `sim/dev/` | three early hand decks (smoke, CM check, device currents) used before the driver existed |

`sim/run_afe.py`, `sim/report_afe.py` and `sim/run_all.sh` were edited after the `20261020b` runs to remove a machine
path (usage text and an environment default only). The sha256 in each `run.json` refers to the version that ran.

Raw decks, logs, waveforms and noise spectra: `$G1_RESULTS_ROOT/r1_afe/<run-id>/` (bulk storage, not in git).

Revision C changed `sim/run_afe.py` (per-job netlist edits, loop-gain probes, post-processing, new campaigns),
`sim/report_afe.py` (revision-C reductions), `sim/tb_afe_settle_adc.cir` (LSB substitution) and `sim/area_estimate.py`
(optional netlist argument). Each `run.json` records the sha256 of the inputs that ran, and the netlist edits of each job.
In the revision-C result files the bulk-root path was replaced by `$G1_RESULTS_ROOT` after the runs (the driver now
writes it that way). The loop-gain probes and development variants are applied to a copy of the netlist in the raw directory
(`<job>_netlist.spice`). The netlist of record is not edited for them.

Reproduce (repository root):

```
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
sh designs/r1-joint/blocks/r1_afe/sim/run_all.sh <suffix>        # revision C: 20261020c2
cd designs/r1-joint/blocks/r1_afe/sim && python3 report_afe.py <suffix>
```

`run_all.sh` sets `G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim`, requires the bulk
`G1_RESULTS_ROOT`, then calls `flow/run.sh python3 run_afe.py <campaign> r1afe-<campaign>-<suffix>`.

## Revision B record (superseded by revision C)

Kept as history. Netlist `schematic/r1_afe_revB.spice`, runs `r1afe-*-20261020b`. The LSB in this record is 2.4 V / 4096.

### Status (revision B)

| Check | Criterion | Status | Evidence (run id → `sim/runs/<id>/run.json`) |
| --- | --- | --- | --- |
| Gain steps ×1–×32, both channels, tt/ss/ff, input CM 0.5/2.5/2.8 V | steps present; ratio error recorded | **passed** (step-ratio error ≤ 1.87 % vs ideal 2^k; calibrated by the host) | `r1afe-ac-20261020b` |
| Anti-alias f_c ≥ 1 MHz at every step, corner, CM | f3 ≥ 1 MHz | **passed**, min 1.057 MHz (ss, ×32, CM 0.5 V); no peaking (max 0.000 dB) | `r1afe-ac-20261020b` |
| Pole matching between channels, 20-sample MC (`mm_ok=1`, mismatch sections of MOS, rppd, MIM) at tt/ss/ff, every step | \|Δf3\| ≤ 1 % | **passed**, worst 0.895 % (tt ×32), σ ≤ 0.40 %; phase mismatch at 100 kHz ≤ 0.067° | `r1afe-ac_mc-20261020b` |
| THD and swing, 100 kHz full scale (2.0 Vpp out), ×1 and ×32, tt/ss/ff | THD ≤ 0.1 % (−60 dB), set in this step from the angle budget (H3 0.1 % → 0.06° el) | **passed**, worst 0.054 % (−65.4 dB, ss ×1); outputs 0.105–1.117 V; CM ripple ≤ 0.03 mV | `r1afe-tran-20261020b` |
| Noise ×1 (output, 1 Hz–100 MHz) | ≤ 240 µV rms (0.41 LSB): AFE keeps chain ENOB ≥ 11 with an ENOB-11.5 SAR | **passed**, worst 205 µV rms (0.35 LSB, ss) | `r1afe-noise-20261020b` |
| Noise ×32 (input-referred) | ≤ 35 µV rms: σ_φ ≤ 0.1° el per sample at 40 mVpp (S1 allocates 0.15° el to electronics) | **failed (marginal)**: 35.3 µV ss; 28.6 µV tt, 25.3 µV ff | `r1afe-noise-20261020b` |
| Input CM 0–3.3 V, operation inside 0.5–2.8 V, stock `sg13g2_IOPadAnalog` on all pins | gain within 2 % of its 1.65 V value; pad current < 1 µA at 2.8 V (limits set in this step) | **passed**: gain variation ≤ 1.62 %; output CM unchanged | `r1afe-cm-20261020b` |
| Pad ESD-diode leakage up to 3.0 V (spec open item 4) | record | **recorded**: 2.8 V: ≤ 4.1 nA; 3.0 V: ≤ 13 nA (ss, VDDA 3.0 V, 125 °C); 3.3 V at VDDA 3.0 V: 34 µA (diode forward) | `r1afe-cm-20261020b` |
| PSRR from VDDA at 20 kHz and 1 MHz | no spec limit; derived ≥ 40 dB set after the run (10 mVpp ripple below the ×32 input noise) | **passed against the derived limit**: worst 54.9 dB (MC, tt); symmetric netlist > 200 dB | `r1afe-psrr-20261020b` |
| Settling into a 2 MSPS T/H, generic model (2 pF/side, reset to 0.6 V, 250 ns track) | non-linear residual ≤ 0.5 LSB | **passed**: error at +FS ≤ 0.75 LSB, of which all but ≤ 0.056 LSB is a linear gain error (≤ 0.045 %) | `r1afe-settle-20261020b` |
| Settling into the r1_adc-matched T/H (2.8 pF/side CDAC, top plate reset to 0 V, 250 ns track) | non-linear residual ≤ 0.5 LSB | **failed (marginal)**: residual 0.506 LSB (tt ×32), error at +FS ≤ 1.94 LSB | `r1afe-settle_adc-20261020b` |
| CM loop stability (output and stage-1 CM ripple in the full-scale transients) | no oscillation | **passed** at tt/ss/ff ×1 and ×32. Two earlier variants oscillated (`dev-quick-03`, `dev-revb-02`); see open issue 3 | `r1afe-tran-20261020b` |
| Output CM | 0.6 V ± 30 mV (set in this step) | **passed**: 0.600–0.628 V | `r1afe-ac-20261020b` |
| Loop-gain phase margin (Middlebrook / stb) of OTA1 and OTA2, differential and CM | — | **not run**. Only closed-loop peaking and transient CM ripple are checked | — |
| Temperature sweep beyond the corner temperatures (−40 °C ff, 27 °C tt, 125 °C ss) | — | **not run** | — |
| Supply-corner cross terms (ss at 3.6 V, ff at 3.0 V), sf/fs MOS corners | — | **not run** | — |
| Overload recovery (input above full scale for the selected step), gain-switch transients | — | **not run** | — |
| Input-source impedance (head output impedance against the 5–40 kΩ input units) | — | **not run** | — |
| Bias from r1_bgr (ideal 10 µA sources here), digital level shifters for c1..c4 | — | **not run** (blocks not available) | — |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |

Revision A (`schematic/r1_afe_revA.spice`, runs `r1afe-*-20261020a`) failed pole matching (1.52 %) and ×32 noise
(40.6 µV, ss). Revision B fixed both, the second only to the margin shown above. Revision A was not run with the
r1_adc-matched T/H. Its records stay as history (disposition "superseded").

### Numbers (simulated, revision B, run suffix `20261020b`)

Corners: tt = mos_tt/res_typ/cap_typ, 3.3 V, 27 °C; ss = mos_ss/res_wcs/cap_wcs, 3.0 V, 125 °C;
ff = mos_ff/res_bcs/cap_bcs, 3.6 V, −40 °C. Input CM 2.5 V (AC) or 2.45 V (transients: pins stay ≤ 2.8 V at 1.4 Vpp).
Load 2 pF per output unless the T/H model is used.

Gain and −3 dB bandwidth (AC, input CM 2.5 V; sine and cosine identical in the nominal runs):

| Step | gain tt | f3 tt (MHz) | f3 ss (MHz) | f3 ff (MHz) | f3 min over CM 0.5/2.5/2.8 V, all corners (MHz) |
| --- | --- | --- | --- | --- | --- |
| ×1 | 1.411 | 1.655 | 1.301 | 2.120 | 1.296 |
| ×2 | 2.816 | 1.644 | 1.292 | 2.107 | 1.279 |
| ×4 | 5.618 | 1.623 | 1.269 | 2.081 | 1.241 |
| ×8 | 11.225 | 1.575 | 1.216 | 2.029 | 1.164 |
| ×16 | 22.437 | 1.530 | 1.188 | 1.967 | 1.151 |
| ×32 | 44.814 | 1.472 | 1.121 | 1.906 | 1.057 |

Phase at 100 kHz (both channels, CM 2.5 V): −4.1° (ff ×1) to −7.8° (ss ×32). It depends on the gain step and the corner,
and it is common to both channels.

Channel matching, 20 mismatch samples per corner (two seeds × 10), every step:

| Corner | worst \|Δf3\| (%) | σ(Δf3) (%) | worst \|Δphase\| at 100 kHz (°) | worst \|Δgain\| (%) |
| --- | --- | --- | --- | --- |
| tt | 0.895 (×32) | 0.40 | 0.066 | 0.97 |
| ss | 0.829 (×32) | 0.40 | 0.067 | 1.06 |
| ff | 0.606 (×32) | 0.28 | 0.034 | 0.91 |

The S1 budget uses 0.06° el at 100 kHz for 1 % pole matching. The simulated worst phase difference of 20 samples
is 0.067°, so the 1 % criterion and the 0.06° figure do not agree exactly. The gain difference (≤ 1.06 %) is
removed by the GAIN_RATIO calibration.

Noise (1 Hz–100 MHz, source impedance 0):

| Corner | ×1 output (µV rms / LSB) | ×1 input (µV rms) | ×32 input (µV rms) | ×32 input density at 1 kHz / 100 kHz / 1 MHz (nV/√Hz) |
| --- | --- | --- | --- | --- |
| tt | 180 / 0.31 | 127 | 28.6 | 124 / 22 / 16 |
| ss | 205 / 0.35 | 146 | 35.3 | 172 / 29 / 19 |
| ff | 163 / 0.28 | 115 | 25.3 | 100 / 17 / 13 |

At ×32 the 1 Hz–100 kHz part is mostly flicker noise of the stage-1 path. The NMOS input pair is the active pair at
the usual 2.5 V head CM.

Transient, 100 kHz, 2.0 Vpp differential output (THD of both channels identical):

| Corner | THD ×1 | THD ×32 | output range (V) | output CM (V) |
| --- | --- | --- | --- | --- |
| tt | 0.022 % (−73.4 dB) | 0.025 % (−72.1 dB) | 0.118–1.105 | 0.612 |
| ss | 0.054 % (−65.4 dB) | 0.050 % (−66.0 dB) | 0.138–1.117 | 0.627 |
| ff | 0.011 % (−79.0 dB) | 0.018 % (−75.1 dB) | 0.105–1.096 | 0.600 |

Track-and-hold settling, 250 ns track (2 MSPS), error at the end of track for +FS input (LSB = 0.586 mV differential):

| Model | ×1 tt/ss/ff | ×32 tt/ss/ff | linear gain error ×32 (worst) | non-linear residual (worst) |
| --- | --- | --- | --- | --- |
| generic (2 pF, reset 0.6 V) | 0.07 / 0.08 / 0.03 | 0.43 / 0.75 / 0.18 | 0.045 % | 0.056 LSB |
| r1_adc-matched (2.8 pF, reset 0 V) | 0.38 / 0.30 / 0.17 | 1.94 / 1.81 / 1.37 | 0.116 % | 0.506 LSB |

The error repeats identically every cycle, and it is almost proportional to the output. It therefore acts as a gain
error that is equal in both channels to within the matching above. The residual is computed from +FS, −FS and +FS/2.

Input CM sweep with the stock pad (×1 and ×32): gain varies ≤ 1.62 % across 0.5–2.8 V. The cause is the
transmission-gate on-resistance, which changes with the summing-node voltage while the feedback TG does not see the
same voltage. Pin current into the AFE: −11 µA (0.5 V) to +43 µA (2.8 V) per pin at ×32 (5 kΩ effective input
unit), −6 to +26 µA at ×1 (40 kΩ); worst values over the three corners.

PSRR (input-referred, A_dm / A_VDDA): with mismatch ≥ 54.9 dB at 20 kHz and 1 MHz, ×1 and ×32 (tt, 20 samples).
VDDA to output CM: −58 to −61 dB at 20 kHz and −25 to −28 dB at 1 MHz. The VCM1 divider is VDDA-referred, and its
2 pF filter pole is ≈ 0.5 MHz.

### Area and current

| Item | Value | Basis |
| --- | --- | --- |
| Area, both channels with VCM1 divider | ≈ 0.084 mm² (MOS 0.025, rppd 0.032, MIM 0.027) | **estimated**: drawn device area from the netlist × overhead (MOS ×4, rppd ×2, MIM ×1.3), `sim/area_estimate.py` → `sim/results/area_estimate_revB.json`. No layout. Budget in S3: 0.06–0.08 mm² |
| Revision A area (w = 2 µm resistors) | ≈ 0.123 mm² | same script on `schematic/r1_afe_revA.spice` |
| VDDA current, both channels | 1.53–1.79 mA (tt 1.59–1.71, ss 1.53–1.66, ff 1.75–1.79), depends on gain step and input CM | simulated, operating points in `r1afe-ac-20261020b` |
| Power | 5.0–6.4 mW (S3 estimate for the AFE: ≈ 4.3 mW, uncertain) | simulated current × VDDA |

### Open issues

1. **×32 noise at ss is 35.3 µV rms against 35 µV** (marginal). Remedies: lower the flicker of the stage-1 path
   (longer CMFB-controlled sinks gave −2 µV in `dev-revb-01` but made the CM loop oscillate, see 3), more OTA1 input-pair
   current, or a 4 % lower f_c (the ss ×32 margin is 5.7 %).
2. **Settling into the r1_adc-matched T/H: residual 0.506 LSB at tt ×32** (marginal). The T/H model is my reading of
   the r1_adc schematic of 2026-10-20 (2.8 pF CDAC per side, top plate near 0 V at the start of track). Confirm the
   track time, the start-of-track top-plate voltage and the sampling capacitance with the r1_adc owner. A larger
   C_o (now 3 pF differential + 0.5 pF per side) or a longer track time reduces the kick.
3. **CM-loop stability of OTA1 is fragile.** It oscillated (stage-1 CM ≈ 1.3–1.5 Vpp) when the folding-node
   capacitance grew (`dev-quick-03`, `dev-revb-02`). It was found only in transients, because AC with a differential
   stimulus does not excite the CM loop. A CM loop-gain (stb) analysis with phase margin at all corners is not run
   and is needed before layout. Layout parasitics at `fn`/`fp` will move it.
4. **Area ≈ 0.084 mm² and power 5.0–6.4 mW exceed the S3 estimates** (0.06–0.08 mm², ≈ 4.3 mW). The largest items
   are the four OTAs (≈ 0.4 mA each), the rail-to-rail stage-1 OTA, the 200 kΩ CMFB sense resistors and the MIM
   filter and output capacitors.
5. **Gain step accuracy** is 1.9 % at ×32 relative to 32 × (×1 gain), and gain varies 1.6 % with input CM (TG
   on-resistance). This is not a matching problem, because both channels see the same CM and code. The host
   calibration must be repeated per gain step (S1 register set: GAIN_RATIO and OFFSET per step, not one value).
6. **Interfaces not designed here**: the PGA_GAIN → c1..c4 decoder (table above) with 1.2 V → 3.3 V level shifters;
   `vcm2` (0.6 V) from the r1_adc reference; four 10 µA bias currents from r1_bgr (ideal in all runs; bias-path
   PSRR not included).
7. **Input impedance** is 40 kΩ (×1) down to 5 kΩ (×8 to ×32) per pin to a virtual ground near the pin CM. DC pin
   current is up to 43 µA at 2.8 V CM. Heads with a kΩ-level source impedance get a gain error, equal in both
   channels to first order. Not simulated with a source impedance.
8. **VCM1 is derived from VDDA** (1.0 V at 3.3 V; 0.91–1.09 V over 3.0–3.6 V). This is acceptable for the stage-1
   CM, but a bandgap-derived reference would remove the VDDA → CM path at 1 MHz.
9. Checks marked **not run** in the status table: loop-gain margins, temperature sweep, cross corners, overload and
   gain-switch transients, source impedance, layout and post-layout.
