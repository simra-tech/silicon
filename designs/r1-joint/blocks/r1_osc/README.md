# R1_OSC — 30 MHz RC relaxation oscillator (revision 2: schematic r2 and layout r2d)

## Revision 2 (T1, 2026-10-21): schematic change and layout r2d, closed post-layout

State: **schematic revision 2 and layout r2d are DRC-, antenna- and LVS-clean. Post-layout (full RC) meets the D13
window at code 22, the ss reach and the 2 % step at all five corners.** The fast-corner code-0 target (≤ 41 MHz) is
not met and cannot be met with any RC trim (see "Open issues (revision 2)", R2-1). Nothing is measured. All numbers
are **simulated** (ngspice 46, PDK models as in "Built against").

**Reset code: `OSC_TRIM` = 22 (unchanged).** Post-layout code 22 gives 30.30 MHz at tt / 1.2 V / 27 °C
(window 29.4–30.6 MHz for 30 MHz ± 2 %; D13 window 28–32 MHz). `r1_ctrl` keeps the reset value 22.

**Binding number for the `r1_ctrl` STA:** 56.37 MHz at ff / 1.32 V / −40 °C, code 0 (post-layout). At the reset
code 22 the ff value is 39.53 MHz (≤ 42 MHz). The target "code 0 ≤ 41 MHz at ff" fails by design (R2-1).

### What changed

| Item | Revision 1 (layout k) | Revision 2 (layout r2d) | Reason |
| --- | --- | --- | --- |
| Fixed bank capacitor CF (`C_FIX_SIDE`) | 28.55 × 28.55 µm (≈ 1.23 pF) | **26.70 × 26.70 µm (≈ 1.07 pF)** | larger trim range per code: ss code-0 reach with code 22 still at 30 MHz |
| Timing resistor RA/RB | `rppd` 1 × 48.3 µm | **unchanged**, 1 × 48.3 µm | see "Design steps": with the switches at the banks the RA/RB cut of L1 is no longer needed |
| Trim unit, switches, comparator, latch, divider | — | unchanged | — |
| Trim switches (layout) | one row group at the bottom, 25–60 µm of wire to the banks | **one switch column per bank, directly west of the unit array**; drain on the bit line, p+ tap column | L2: bit-node wiring 14–23 fF made the trim non-binary |
| Bit-node wiring C (PEX) | 14.2–22.7 fF | **1.1–2.6 fF** | same |
| Channel tracks | 28 (10 bit tracks) | 19 (bit tracks removed, `osc_clk` added) | — |
| `osc_clk` pin | east edge (Metal3 under the channel) | **west edge**, lowest Metal4 channel track | S7 floorplan constraint (coordinator, 2026-10-21) |
| Macro | 154.4 × 118.4 µm = 0.01828 mm² | **148.2 × 110.4 µm = 0.01636 mm²** (−10.5 %) | — |

Netlist of record: `schematic/r1_osc.spice` sha256 `00c73f748d86f2cbf5081d5c4c5fe298bd5213bf9ba2ae63bf4b0ea802c91c02`
(revision 1 kept as `schematic/r1_osc_rev1.spice`, sha256 `d9d84501f5a18d5621ef9b6243d41172209fd738fe359d6067557669525cd949`).
Layout of record: `layout/r1_osc.gds` (layout r2d) sha256 `7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971`,
generator `layout/r1_osc_layout.py` sha256 `c80061077826532d8fb7cb376e280f7de68bf7172431b26a9742ccfe4ca16102`,
LVS CDL sha256 `600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa`.
PEX of record: `pex-rc-20261021-r2d`, PEX netlist sha256 `c6d76aac02c310790dbea47e8362a6f663f070edaa097eea7b5711aff2184c77`
(220 R, 428 C, 372 fF; in the results root, not in the tree).
xschem sheets re-generated from `gen_r1_osc.py`: `compare_netlists.py` 8 sub-circuits, 0 differences.

### Design steps (schematic → layout → RC extraction)

1. Layout first, with the revision-1 sizes: switch columns at the banks (layout r2b, PEX `pex-rc-20261021-r2b`).
   Post-layout tt: code 0 38.45 MHz, code 22 27.97 MHz, step 3→4 1.60 % (layout k: 2.52 % at the carries); ss code 0
   29.30 MHz (`sim/runs/r2-whatif-v0-20261021`). The carry error is gone. Reach still fails.
2. Model from step 1 (half period linear in code: 0.221 ns per code; fixed part ≈ 49.7 units incl. wiring; loop delay
   2.05 ns tt, 3.30 ns ss): ss code 0 ≥ 32 MHz with tt code 22 ≤ 30.6 MHz needs f(0)/f(22) ≥ 1.37 at tt, i.e. a
   step of ≈ 1.8–1.9 % at code 0. A shorter RA/RB lowers this ratio (more of the period is loop delay): RA/RB × 0.85
   gave ss code 0 / tt code 22 = 1.040 against 1.048 at × 1.0 (`r2-whatif-v85-20261021`). So the knob is CF, not RA/RB.
3. What-if CF 26.4 / 26.7 / 27.0 µm on PEX r2b (`r2-whatif-cf*-20261021`): tt code 22 30.72 / 30.31 / 29.92 MHz,
   ss code 0 33.33 / 32.72 / 32.13 MHz. Chosen: **26.70 µm** (balances the 30.6 MHz window edge and the 32 MHz reach).
4. Schematic revision 2 written, layout regenerated (r2c), PEX r2c, full post-layout campaign started.
5. The S7 constraint (all signal pins west) came during step 4. Layout r2d moves `osc_clk` to the west edge. PEX r2d:
   `osc_clk` wiring 3.0 → 14.7 fF; coupling to `va`, `vb`, `vth`, `vbn` ≤ 0.09 fF each. tt trim r2d vs r2c: −0.03 to
   −0.05 %. All post-layout numbers of record below are on r2d; the r2c runs are kept as superseded.

### Status (revision 2)

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| xschem sheets vs SPICE source (revision 2) | 0 differences | **passed**: 8 sub-circuits, 0 differences | `schematic/compare_netlists.py`, `schematic/xschem_netlist/r1_osc.spice` |
| DRC, main + maximal, deep, density off | 0 markers | **passed**: 0 | `layout/runs/layout-drc-20261021-r2d` |
| Antenna | 0 markers | **passed**: 0 | `layout/runs/layout-ant-20261021-r2d` |
| LVS vs netlist of record (dummies excluded, as layout k) | match | **passed**: 34 NMOS, 19 PMOS, 5 `rppd`, 13 `cap_cmim`, 1 `dpantenna`; 43 nets | `layout/runs/layout-lvs-20261021-r2d` |
| Pins: 9 Metal3 pins at the edge, all signal pins west (S7) | as layout k, `osc_clk` west | **passed** (table "Pins") | `layout/runs/layout-pins-20261021-r2d` |
| Bounding box | ≤ 154.4 × 118.4 µm (preferred ≤ 148.2 × 110.4 µm) | **passed**: 148.2 × 110.4 µm = 0.01636 mm² | `layout/r1_osc_layout_meta.json`, `layout/runs/layout-gen-20261021-r2d` |
| Routing Metal1–Metal4, Metal5/TopMetal1 only on MIM plates; MIM plates, dummies, guard ring and `vss` shields as layout k | as layout k | **not run** as a separate check (by construction in the generator; LVS and DRC pass) | `layout/r1_osc_layout.py` |
| Density | — | **not applicable** at block level (waived; chip-level fill) | — |
| PEX (full RC) | extracted | **passed** | `layout/runs/pex-rc-20261021-r2d` |
| Post-layout code 22, tt | 30 MHz ± 2 % (29.4–30.6 MHz) | **passed**: 30.30 MHz | `sim/runs/r2-postd-trim32-tt-20261021` |
| Post-layout code 22, tt | 28–32 MHz (D13) | **passed**: 30.30 MHz | same |
| Post-layout reach, ss / 1.08 V / 125 °C, code 0 | ≥ 32 MHz | **passed**: 32.70 MHz (margin 2.2 %) | `sim/runs/r2-postd-reach-20261021` |
| Post-layout trim, 32 codes, tt, ss / 1.08 V / 125 °C, ff / 1.32 V / −40 °C | monotonic, step ≤ 2 % | **passed**: max step 1.89 / 1.84 / 1.92 % | `r2-postd-trim32-tt-20261021`, `r2-postd-reach-20261021` |
| Post-layout trim, 32 codes, ss / 1.08 V / −40 °C and ff / 1.32 V / 125 °C | monotonic, step ≤ 2 % | **passed**: max step 1.84 / 1.90 % | `sim/runs/r2-postd-cross-20261021` |
| Post-layout ff / 1.32 V / −40 °C, code 0 | ≤ 41 MHz | **failed**: 56.37 MHz (not reachable, R2-1; binding number for the STA) | `sim/runs/r2-postd-reach-20261021` |
| Post-layout ff / 1.32 V / −40 °C, code 22 | ≤ 42 MHz (D13 STA) | **passed**: 39.53 MHz | same |
| Post-layout loop delay | ≤ 3–4 ns | **passed**, small margin: max 3.74 ns (ss / 1.08 V / −40 °C and 125 °C, code 31) | trim32, reach and cross runs |
| Post-layout duty, 5 × 32 codes | 50 % (no limit specified) | 48.66–49.44 % (record) | same |
| Post-layout IDD | record | 229.9 µA (tt, code 22); 168.2–316.6 µA over 5 × 32 points | same |
| Post-layout jitter, tt, code 22 (white noise, gear) | ≤ 280 ps over 30 cycles (S5) | **passed**: σ period 11.6 ps, σ 30 cycles 64.2 ps (6 µs, 170 periods; no-noise floor 0.007 / 0.03 ps) | `sim/runs/r2-postd-jitter-20261021` |
| Post-layout start-up at reset code 22, tt and ss / 1.08 V / 125 °C (and ff / 1.32 V / −40 °C) | starts, correct frequency | **passed**: first edge 17.1 / 22.3 / 13.1 ns after `en`; en tied high: first edge 0.503 / 0.541 / 0.496 µs into the 1 µs ramp | `sim/runs/r2-postd-startup-20261021` |
| Schematic revision 2, 32 codes at the 5 corners (pre-layout reference) | record | ran: tt code 22 32.69 MHz, ss code 0 36.80 MHz, step max 2.01–2.05 % at code 0→1 (the schematic alone is not the design point: CF is sized with the extracted wiring, which adds ≈ 8 % to the period) | `sim/runs/r2-sch-trim32-tt-20261021`, `r2-sch-reach-20261021`, `r2-sch-cross-20261021` |
| Post-layout mismatch MC (tt, ss reach), PVT points other than the 5 corners, supply step / ripple, comparator noise, jitter at ss / ff, LEF | — | **not run** | — |
| Measurement | — | **not run** | — |

### Post-layout trim curves (layout r2d, full RC)

| Corner | Code 0 | Code 16 | Code 22 | Code 31 | Step min–max (codes of max) | Monotonic | Duty | IDD code 22 | Loop delay max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tt / 1.2 V / 27 °C | 43.03 | 32.93 | 30.30 | 27.06 | 1.15–1.89 % (1→2) | yes | 48.92–49.32 % | 229.9 µA | 2.30 ns |
| ss / 1.08 V / 125 °C | 32.70 | 25.19 | 23.21 | 20.77 | 1.14–1.84 % (1→2) | yes | 48.81–49.25 % | 173.2 µA | 3.74 ns |
| ff / 1.32 V / −40 °C | 56.37 | 43.00 | 39.53 | 35.26 | 1.16–1.92 % (1→2) | yes | 49.02–49.39 % | 304.3 µA | 1.45 ns |
| ss / 1.08 V / −40 °C | 33.41 | 25.74 | 23.72 | 21.23 | 1.13–1.84 % (1→2) | yes | 48.66–49.15 % | 169.2 µA | 3.74 ns |
| ff / 1.32 V / 125 °C | 54.43 | 41.63 | 38.30 | 34.19 | 1.15–1.90 % (1→2) | yes | 49.10–49.44 % | 308.6 µA | 1.59 ns |

Full tt curve (step = (f(k) − f(k+1)) / f(k)):

| Code | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f (MHz) | 43.03 | 42.22 | 41.42 | 40.70 | 39.99 | 39.29 | 38.63 | 38.00 | 37.32 | 36.71 | 36.11 | 35.56 | 35.02 | 34.48 | 33.97 | 33.48 |
| step to next (%) | 1.87 | 1.89 | 1.74 | 1.75 | 1.74 | 1.69 | 1.63 | 1.80 | 1.62 | 1.64 | 1.52 | 1.53 | 1.52 | 1.48 | 1.43 | 1.64 |
| Code | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f (MHz) | 32.93 | 32.46 | 31.99 | 31.56 | 31.13 | 30.71 | 30.30 | 29.92 | 29.50 | 29.12 | 28.74 | 28.39 | 28.05 | 27.70 | 27.37 | 27.06 |
| step to next (%) | 1.43 | 1.45 | 1.35 | 1.36 | 1.35 | 1.32 | 1.28 | 1.40 | 1.28 | 1.30 | 1.21 | 1.22 | 1.22 | 1.19 | 1.15 | — |

### Pre- versus post-layout, revision 1 versus revision 2 (MHz)

| Point | r1 schematic | r1 post (layout k) | r2 schematic | r2 post (layout r2d) | r2 post vs r2 schematic |
| --- | --- | --- | --- | --- | --- |
| tt / 1.2 V / 27 °C, code 0 | 42.24 | 37.11 | 47.73 | 43.03 | -9.9 % |
| tt / 1.2 V / 27 °C, code 22 | 30.03 | 27.54 | 32.69 | 30.30 | -7.3 % |
| tt / 1.2 V / 27 °C, code 31 | 26.86 | 25.09 | 28.97 | 27.06 | -6.6 % |
| ss / 1.08 V / 125 °C, code 0 | 32.61 | 28.36 | 36.80 | 32.70 | -11.1 % |
| ss / 1.08 V / 125 °C, code 22 | 23.27 | 21.15 | 25.32 | 23.21 | -8.3 % |
| ss / 1.08 V / 125 °C, code 31 | 20.84 | 19.29 | 22.46 | 20.77 | -7.5 % |
| ff / 1.32 V / −40 °C, code 0 | 54.88 | 48.39 | 62.05 | 56.37 | -9.2 % |
| ff / 1.32 V / −40 °C, code 22 | 38.94 | 35.86 | 42.40 | 39.53 | -6.8 % |
| ff / 1.32 V / −40 °C, code 31 | 34.81 | 32.67 | 37.55 | 35.26 | -6.1 % |
| ss / 1.08 V / −40 °C, code 0 | 33.41 | not run | 37.70 | 33.41 | -11.4 % |
| ss / 1.08 V / −40 °C, code 22 | 23.86 | not run | 25.95 | 23.72 | -8.6 % |
| ss / 1.08 V / −40 °C, code 31 | 21.37 | not run | 23.03 | 21.23 | -7.8 % |
| ff / 1.32 V / 125 °C, code 0 | 53.19 | not run | 60.10 | 54.43 | -9.4 % |
| ff / 1.32 V / 125 °C, code 22 | 37.81 | not run | 41.16 | 38.30 | -7.0 % |
| ff / 1.32 V / 125 °C, code 31 | 33.82 | not run | 36.47 | 34.19 | -6.3 % |
| Step max, all codes | 1.81 % | 2.63 % | 2.05 % | 1.92 % | — |

### Start-up and jitter (layout r2d, full RC, reset code 22)

| Corner | First edge after `en` rises | f after enable | `osc_clk` max while `en` = 0 (supply ramp) | First edge, `en` tied to `vdd` (1 µs ramp) |
| --- | --- | --- | --- | --- |
| tt / 1.2 V / 27 °C | 17.1 ns | 30.30 MHz | 81 mV | 0.503 µs |
| ss / 1.08 V / 125 °C | 22.3 ns | 23.21 MHz | 85 mV | 0.541 µs |
| ff / 1.32 V / −40 °C | 13.1 ns | 39.53 MHz | 75 mV | 0.496 µs |

The second enable gives the same delay and frequency. While `en` = 0 after running, `osc_clk` stays at or below 0.1 mV.
Revision 1 (schematic, code 16): 15.6 / 20.2 / 12.1 ns and 34–45 mV during the ramp. The ramp glitch on `osc_clk`
is about twice as large (more `osc_clk` wiring); it stays far below the logic threshold.

| Jitter, tt / 1.2 V / 27 °C, code 22 | Run | Mean period | σ period | σ over 30 cycles |
| --- | --- | --- | --- | --- |
| Revision 1 schematic, 15 µs | `r1b-jitter` | 33.300 ns | 14.9 ps | 103 ps |
| Layout k, 6 µs | `post-jitter-20261021-b` | 36.304 ns | 12.8 ps | 39.1 ps |
| **Layout r2d, 6 µs** | `r2-postd-jitter-20261021` | 32.997 ns | **11.6 ps** | **64.2 ps** |
| Layout r2d, no noise (floor) | same, case `ref` | 33.012 ns | 0.007 ps | 0.03 ps |

The 6 µs runs have about 5 independent 30-cycle windows, so the 30-cycle σ is uncertain by tens of percent (L6 of
revision 1). Against the S5 budget (280 ps over ≈ 30 cycles) the margin is 4.4 ×.

### Pins (layout r2d, S7)

| Pin | Layer | Edge | Position (µm, centre) | Layout k |
| --- | --- | --- | --- | --- |
| `osc_clk` | Metal3 | **west** | x 0–1.5, y 21.15 | east edge |
| `en` | Metal3 | west | y 25.15 | west, y 32.35 |
| `trim0` … `trim4` | Metal3 | west | y 25.95, 26.75, 27.55, 28.35, 29.15 | west, y 33.15 … 36.35 |
| `vdd` | Metal3 bar | north (full width) | y 108.4–110.4 | north |
| `vss` | Metal3 bar | south (full width) | y 0–2 | south |

### Commands (revision 2)

From the repository root (POSIX sh):

```
G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
python3 designs/r1-joint/blocks/r1_osc/schematic/gen_r1_osc.py designs/r1-joint/blocks/r1_osc/schematic/r1_osc.spice
sh designs/r1-joint/blocks/r1_osc/layout/run_checks.sh 20261021-r2d
flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_osc/layout/pin_check.py \
  -rd gds=designs/r1-joint/blocks/r1_osc/layout/r1_osc.gds -rd ref=designs/r1-joint/blocks/r1_osc/layout/r1_osc_layout_k.gds
sh designs/r1-joint/blocks/r1_osc/layout/run_pex.sh 20261021-r2d 20261021-r2d
G1_CPUS=3; export G1_CPUS; G1_WORKDIR=designs/r1-joint/blocks/r1_osc; export G1_WORKDIR
P=<G1_RESULTS_ROOT>/r1_osc/pex-rc-20261021-r2d/r1_osc_pex.spice
flow/run.sh python3 sim/run_osc30.py trim32 <run-id> --jobs 3 --netlist $P
flow/run.sh python3 sim/run_osc30.py reach <run-id> --jobs 3 --netlist $P
flow/run.sh python3 sim/run_osc30.py probe <run-id> --jobs 3 --netlist $P --probe "ss:1.08:-40:0 ... ff:1.32:125:31"
flow/run.sh python3 sim/run_osc30.py startup <run-id> --jobs 3 --code 22 --netlist $P
flow/run.sh python3 sim/run_osc30.py jitter <run-id> --jobs 2 --cases "noise ref" --code 22 --tstop 6u \
  --method gear --en 12.2e-9 --netlist $P
python3 designs/r1-joint/blocks/r1_osc/sim/summarize_r2.py
```

The campaign script used is `<G1_RESULTS_ROOT>/r1_osc/r2d-campaign.sh` (one runner call per run id). New in this
step: `layout/pin_check.py`, `sim/summarize_r2.py` (writes `sim/results/summary_r2.json`), runner option
`startup --code N`. Frozen revision-1 files: `schematic/r1_osc_rev1.spice`, `layout/r1_osc_layout_k.py`,
`layout/r1_osc_layout_k.gds`, `layout/r1_osc_lvs_k.cdl`, `layout/r1_osc_layout_meta_k.json`. A re-run of `r1_osc_layout_k.py`
writes `r1_osc_layout_k.gds` byte-identical (sha256 `0b98903c…c0059`, checked 2026-10-21).

Built against: as in "Built against" below (PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container image
`sha256:ddeb6957…`, ngspice-46, KLayout 0.30.9, kpex 0.3.12, xschem 3.4.8RC). Each `run.json` records them.

### Open issues (revision 2)

- **R2-1. ff code 0 ≤ 41 MHz cannot be met together with the ss reach** (spec-ambiguity). Code 0 is the same
  capacitor at both corners, so f(ff, 0) / f(ss, 0) is fixed by PVT: 1.72 post-layout (56.37 / 32.70 MHz),
  1.68 at schematic level in revision 1. ≥ 32 MHz at ss and ≤ 41 MHz at ff would need ≤ 1.28. As the task
  states for this case, the ss reach and the tt window are kept. **Binding number for the `r1_ctrl` STA:
  56.37 MHz at ff / 1.32 V / −40 °C, code 0** (revision 1 schematic: 54.88 MHz; layout k: 48.39 MHz). At the reset
  code 22 the fastest corner gives 39.53 MHz (≤ 42 MHz). Codes 0 … 17 exceed 42 MHz at ff / −40 °C
  (code 17: 42.38 MHz, code 18: 41.75 MHz; revision 1 schematic: codes 0 … 16). D13 already says such codes are flagged by `OSC_COUNT`, not prevented; the host must not write
  them at the fast corner. Owner of `r1_ctrl`: confirm that the STA closes at 42 MHz with this rule, or close at
  56.4 MHz.
- **R2-2. ss reach margin.** 32.70 MHz at code 0 is 2.2 % above 32 MHz. Local mismatch at this point was
  σ 0.78 % in revision 1 (`r1a-mcreach`, schematic); mean − 3σ ≈ 31.9 MHz (*estimated*, the MC was not re-run
  on revision 2 or on the PEX netlist). Not run: `mcreach` on the PEX netlist.
- **R2-3. tt window margin.** Code 22 gives 30.30 MHz, 1.0 % above 30 MHz and 1.0 % below the 30.6 MHz edge of
  the ± 2 % window. The code-to-code step is 1.3–1.4 % around code 22, so a ± 1 code error moves it out of ± 2 %
  but stays inside the D13 window 28–32 MHz.
- **R2-4. Loop delay at ss / 1.08 V / 125 °C** is up to 3.74 ns at code 31 (revision 1 schematic 2.32 ns; layout k 3.91 ns). The
  limit is "≤ 3–4 ns". It costs reach margin, and it is mostly row-group wiring (unchanged from layout k).
- **R2-5. Duty** is 48.6–49.4 % post-layout (schematic 49.7–49.9 %). `vb` has ≈ 10 fF more wiring than `va`
  (32.4 vs 22.2 fF: the `vb` riser passes bank A). No duty limit is specified (open issue 4 of revision 1).
- **R2-6. `osc_clk` now crosses the macro** (west pin, S7) on the lowest channel track, above the resistor block.
  Extracted coupling to `va`, `vb`, `vth`, `vbn` ≤ 0.09 fF each; the tt curve moved −0.03 to −0.05 % (r2c → r2d).
  The pin moved from the east to the west edge and the `en` / `trim` pins moved down by 7.2 µm: the chip-level
  floorplan must use the new pin table.
- **R2-7. Not run on revision 2:** PVT points other than the five corners, mismatch MC (tt and ss reach), supply
  step and ripple, comparator noise, jitter at ss/ff and with 1/f noise, LEF/abstract, density at block level
  (waived as in layout k). MIM bottom-plate parasitics are still not modelled (L3 of revision 1).
- **R2-8. Area.** 0.01636 mm² (−10.5 % against layout k). The S6 option C10 (0.012 mm²) is not reached: the
  resistor block and CTH (west half) and the two banks are unchanged in size.

### Failures and mistakes (revision 2)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | First switch-column layout (r2a): Gat.b × 4 (switch gate straps 0.11–0.16 µm from the next gate) and M2.d / M3.d × 12 each (0.30 µm via pads below minimum area) | estimation | `layout/runs/layout-drc-20261021-r2a` |
| 2 | r2a antenna: Ant.b on the two bit-0 switch gates (`trim0`): the new 50 µm riser to bank B was not counted. Fixed with 0.20 µm risers and trim0 next to the switches | estimation | `layout/runs/layout-ant-20261021-r2a` |
| 3 | The revision-1 recommendation (L1: RA/RB ≈ 41 µm) was based on the layout-k parasitics. With the switches at the banks it lowers the reach ratio; the right knob is CF. The what-if `v80` was built but not run (chain stopped) | estimation | `sim/runs/r2-whatif-v85-20261021`, `r2-whatif-cf*-20261021` |
| 4 | The task target "ff code 0 ≤ 41 MHz" is not reachable with any RC trim (f(ff,0)/f(ss,0) is fixed by PVT); recorded as R2-1 | spec-ambiguity | this section |
| 5 | S7 (osc_clk on the west edge) arrived after layout r2c and during its post-layout campaign; trim32-tt, reach and cross on r2c (≈ 55 min of 3 CPUs) are superseded | coordination | `sim/runs/r2-post-*-20261021`, `<G1_RESULTS_ROOT>/r1_osc/r2-campaign.out` |
| 6 | Campaign script not executable (exit 126); relaunched | tooling | `<G1_RESULTS_ROOT>/r1_osc/r2d-campaign.out` |
| 7 | A `find /` for the antenna deck ran past 2 min and was stopped; foreground wait loops hit the 10 min tool limit several times | tooling | session |
| 8 | The generator docstring was edited after the r2c run, so the generator sha256 in `layout-gen-20261021-r2c/run.json` differs from the file; a re-run gave the same GDS sha256 (`6b6bc0ee…`). r2d records the final generator | process-hygiene | `layout/runs/layout-gen-20261021-r2d` |

*The sections below describe revision 1 (schematic r1 and layout k). They are kept as the record of that revision.*

## Revision 1 (schematic r1, layout k)

State on 2026-10-21: **schematic sized and simulated; layout DRC-clean and LVS-clean; post-layout simulation fails
two targets** (reach at ss/1.08 V/125 °C and trim step ≤ 2 %; see "Layout"). Nothing is measured. Every number in
this file is **simulated** with ngspice 46 and the PDK models named below, unless it is marked *estimated*.

## What it is

The internal clock of R1 (specification row `r1_osc`, study S5 option (a)). It is the G1 R0.95 oscillator
(`../../../g1-guardian/blocks/g1_osc/`) re-tuned from 10 MHz to 30 MHz:

- Ping-pong RC relaxation oscillator in the 1.2 V core domain. Each half period, one `cmim` bank charges from
  `vdd` through an `rppd` resistor. The other bank is held at 0 V by an NMOS switch.
- A continuous-time comparator per bank (NMOS-input 5-T pair, PMOS mirror, two inverters) compares the ramp
  with `vdd`/2. The threshold comes from a 2 × 100 kΩ `rppd` divider with a 1 pF `cmim` hold capacitor and
  the G1 antenna diode.
- An SR latch toggles on each crossing. Its output is `osc_clk` (50 % duty by symmetry) and it drives the reset
  switches. Half period = R·C·ln 2 + loop delay.
- `en` = 0 forces the latch to Q = 0, holds both banks at 0 V and holds `osc_clk` low.

Changes from G1 R0.95 (sizes in `schematic/gen_r1_osc.py`):

| Item | G1 R0.95 | R1 r1 |
| --- | --- | --- |
| Timing resistor RA/RB | `rppd` 1 × 111.15 µm (≈ 29 kΩ) | `rppd` 1 × 48.3 µm (≈ 12.6 kΩ, *estimated* from 70 Ω + 260 Ω/µm) |
| Fixed bank capacitor | 31.65 × 31.65 µm (1.50 pF) | 28.55 × 28.55 µm (≈ 1.23 pF) |
| Trim | 4 bit, 100 fF LSB, one square cap per bit | 5 bit, 25 fF unit cap (4.03 × 4.03 µm), bit *b* = 2^*b* units (`m`); range 0 … 775 fF |
| Trim switches | 4 µm / 0.13 µm each | 0.5 / 0.5 / 1 / 2 / 4 µm (bit 0 … 4), L = 0.13 µm |
| Comparator bias | RBIAS 134.3 µm (≈ 20 µA), tail = 1 × reference | RBIAS 80 µm (≈ 30 µA, *estimated*), tail = 2 × reference (≈ 60 µA per comparator, *estimated*) |
| Output inverter | 1 µm / 0.5 µm | 4 µm / 2 µm |
| Threshold divider, hold cap, antenna diode, latch, enable | — | unchanged |

Ports: `en trim0 trim1 trim2 trim3 trim4 osc_clk vdd vss`. All in the 1.2 V core domain. `trim[4:0]` is
`OSC_TRIM`; a higher code gives a lower frequency.

**Reset code: 22, not the mid code 16.** At tt/1.2 V/27 °C, code 22 gives 30.03 MHz and code 16 gives 32.59 MHz.
The reason is in "Open issues", item 1. The `r1_ctrl` register `OSC_TRIM` must reset to 22.

## Files

| Path | Content |
| --- | --- |
| `schematic/gen_r1_osc.py` | Writes the SPICE source `schematic/r1_osc.spice`. All device sizes are here. |
| `schematic/r1_osc.spice` | SPICE source as simulated (`.subckt r1_osc` and its sub-cells). `mm_ok=1` on every device for the mismatch decks. |
| `schematic/gen_r1_osc_xschem.py` | Writes the xschem sheets and symbols `schematic/r1_osc*.sch/.sym`. Adapted from the G1 generator. Reads the sizes from `gen_r1_osc.py`. |
| `schematic/netlist_xschem.sh`, `schematic/xschem_netlist/r1_osc.spice` | Headless xschem netlist of the sheets. |
| `schematic/compare_netlists.py` | Device-by-device comparison of the two netlists. Result: 8 sub-circuits, 0 differences. |
| `sim/tb_osc30.cir` | Frequency, duty, IDD and loop delay at one PVT point and one trim code. |
| `sim/tb_osc30_psrr.cir` | 10 mV supply step, 10 mV-peak ripple at 20 kHz and at 1 MHz. |
| `sim/tb_osc30_startup.cir` | Supply ramp with `en` low, `en` toggle, and a second instance with `en` tied to `vdd`. |
| `sim/tb_osc30_mc.cir` | Local mismatch sample (`*_mismatch` sections, `.option seed`). |
| `sim/tb_osc30_cmpnoise.cir` | DC trip point, `.ac` and `.noise` of one comparator at the threshold. |
| `sim/tb_osc30_jitter.cir` | Transient noise (`trnoise` at the comparator inputs and across RA/RB). |
| `sim/run_osc30.py` | Runner (suites, deck expansion, parallel jobs, post-processing, `run.json`). |
| `sim/summarize.py`, `sim/results/summary_r1.json` | Collected checks and numbers of revision r1. |
| `sim/runs/<run-id>/` | Per run: `run.json`, `results.json`, `results.csv`, netlist snapshot. |
| `layout/r1_osc_layout.py` | Layout generator (KLayout Python, PDK PCells). Writes `layout/r1_osc.gds`, `layout/r1_osc_lvs.cdl`, `layout/r1_osc_layout_meta.json`. |
| `layout/r1_layout_lib.py` | Drawing library. Copy of the G1 `g1_osc` layout library (two header lines added). |
| `layout/r1_osc.gds` | Revision 1: layout k (now frozen as `layout/r1_osc_layout_k.gds`; `r1_osc.gds` is layout r2d, see "Revision 2"), sha256 `0b98903c7e04bbdaec6cbef6e60f610d2f6a5b993ebc158a09294e2c2db0c059`. Written without GDS timestamps, so a re-run gives the same hash. |
| `layout/r1_osc_lvs.cdl` | LVS reference: the netlist of record in CDL form. The 44 dummy MIM units are not in it (see "Layout"). |
| `layout/run_checks.sh`, `layout/write_runjson.py` | Generator + PDK DRC + antenna + LVS, and the `run.json` writer. |
| `layout/pex_input.py`, `layout/run_pex.sh`, `layout/pex_build.py` | Extraction (method of `r1_bgr`): kpex coupling C, KLayout `RNetExtractor` wiring R, MIM re-inserted. |
| `layout/runs/<run-id>/` | `run.json` (and `DISPOSITION.txt` for failed runs) of every layout and PEX run. |

Expanded decks, logs and raw waveforms are in the bulk results root under `r1_osc/<run-id>/` (`run.json` field
`raw_results`). They are not in the tree.

## How to run

From the repository root:

```
G1_CPUSET=100-102; export G1_CPUSET; G1_CPUS=3; export G1_CPUS
G1_WORKDIR=designs/r1-joint/blocks/r1_osc; export G1_WORKDIR
G1_RESULTS_ROOT=<bulk results root>; export G1_RESULTS_ROOT
python3 designs/r1-joint/blocks/r1_osc/schematic/gen_r1_osc.py designs/r1-joint/blocks/r1_osc/schematic/r1_osc.spice
flow/run.sh python3 sim/run_osc30.py trim32 <new-run-id>
```

Suites: `quick`, `trim32`, `corners27 [--code N]`, `reach`, `psrr`, `startup`, `mc`, `mcreach`, `cmpnoise`,
`jitter [--code N --tstop T --en V/rtHz]`. Each run id must be new.

## Built against

| Item | Version | How it was established |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches; also read into every `run.json` |
| Container | `tapeoutbench-eda:latest`, image `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | image identity check in `flow/run.sh` |
| ngspice | ngspice-46 | `ngspice -v` in the container, recorded in every `run.json` |
| xschem | 3.4.8RC | `xschem --version`, `schematic/xschem_netlist/xschem_version.txt` |
| KLayout | 0.30.9 (layout generator, PDK DRC/antenna/LVS decks, `RNetExtractor` for wiring R) | `klayout -v` in the container, recorded in `layout/runs/*/run.json` |
| kpex | 0.3.12 (2.5D coupling capacitance only) | `kpex --version` in the container, recorded in `layout/runs/pex-rc-*/run.json` |
| LibreLane, CACE | not used | — |

Models: `cornerMOSlv.lib mos_tt|mos_ss|mos_ff`, `cornerRES.lib res_typ|res_wcs|res_bcs`,
`cornerCAP.lib cap_typ|cap_wcs|cap_bcs`, `cornerDIO.lib dio_tt`; the mismatch decks use the `*_mismatch` sections
of the same corner. Corner sets: tt = mos_tt/res_typ/cap_typ, ss = mos_ss/res_wcs/cap_wcs,
ff = mos_ff/res_bcs/cap_bcs. Load on `osc_clk`: 50 fF. Transient step 20 ps.

## Status

| Check | Status | Evidence (`sim/runs/…`) |
| --- | --- | --- |
| Trim, 32 codes, tt/1.2 V/27 °C: monotonic, step ≤ 2 % | **passed** (step 1.16–1.80 %) | `r1a-trim32-tt` |
| Trim, 32 codes, ss/1.08 V/125 °C and ff/1.32 V/−40 °C: monotonic, step ≤ 2 % | **passed** (1.15–1.78 %, 1.17–1.81 %) | `r1a-reach` |
| Trim, 32 codes, ss/1.08 V/−40 °C and ff/1.32 V/125 °C: monotonic, step ≤ 2 % | **passed** (1.15–1.78 %, 1.16–1.80 %; 33.41 and 53.19 MHz at code 0; run 2026-10-21) | `r1d-trim32-cross` (`run.json` written by hand, see "Layout", failure 14) |
| Reach ≥ 32 MHz at ss/1.08 V/125 °C | **passed**, 32.61 MHz at code 0 (margin 1.9 %) | `r1a-reach` |
| Reach ≥ 32 MHz at ss/1.08 V/125 °C under local mismatch, 50 samples | **passed** for 50/50 (min 32.04 MHz); mean − 3σ = 31.76 MHz (open issue 3) | `r1a-mcreach` |
| 30 MHz at the mid code 16, tt | **failed** by design choice: 32.59 MHz; 30.03 MHz is at code 22 (open issue 1) | `r1a-trim32-tt` |
| Loop delay (comparator + latch) ≤ 3–4 ns, all 27 corners, codes 16 and 22 | **passed**, max 2.20 ns (2.32 ns at ss/1.08/125 code 31) | `r1a-corners27-c16`, `r1a-corners27-c22`, `r1a-reach` |
| Duty 50 %, 27 corners | **passed**, 49.77–49.88 % | same |
| Duty under mismatch | 48.6–51.3 % over 50 samples (no limit specified) | `r1a-mc50` |
| PVT at code 16 and code 22 (tt/ss/ff × 1.08/1.2/1.32 V × −40/27/125 °C, 27 points each) | **passed** (all ran; numbers below) | `r1a-corners27-c16`, `r1a-corners27-c22` |
| Full 32-code trim at all 27 PVT points | **not run** | — |
| Supply step and ripple | **ran** (numbers below; no limit specified) | `r1a-psrr` |
| Start-up (supply ramp, enable toggle), 3 corners | **passed** | `r1a-startup` |
| Mismatch MC, 50 samples, tt, code 16 | **passed** (ran, 0 failures) | `r1a-mc50` |
| Comparator `.noise` | **passed** (ran) | `r1b-cmpnoise` (`r1a-cmpnoise`: failed, deck echo error) |
| Transient-noise jitter, code 22, tt (white noise) | **passed** against the S5 budget: σ period 14.9 ps, σ 30 cycles 103 ps (≤ 280 ps) | `r1b-jitter`, floor `r1c-jitter-ref` (`r1a-jitter` and the `r1b-jitter` ref case: failed, timestep too small with `trnoise`) |
| Jitter at ss/ff corners, jitter with 1/f noise | **not run** | — |
| xschem sheet vs SPICE source | **passed** (0 differences) | `schematic/compare_netlists.py` |
| Layout, DRC, antenna, LVS, PEX | **passed** (layout k: DRC 0, antenna 0, LVS match) | `layout/runs/layout-{drc,ant,lvs}-20261021-k`, `layout/runs/pex-rc-20261021-h` |
| Post-layout simulation (trim, reach, PVT points, duty, IDD, jitter) | **failed** 2 targets: reach at ss code 0 and step ≤ 2 % (details in "Layout") | `post-trim32-tt-20261021`, `post-reach-20261021`, `post-jitter-20261021-b` |
| Measurement | **not run** | — |

Tuning runs `tune01-quick` … `tune04-probe` and deck checks `smoke01`, `mcseed02` are kept in `sim/runs/` with
their dispositions.

## Results (simulated)

### Trim curve, tt / 1.2 V / 27 °C (`r1a-trim32-tt`)

| Code | 0 | 4 | 8 | 12 | 16 | 20 | 22 | 24 | 28 | 31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f (MHz) | 42.24 | 39.33 | 36.79 | 34.57 | 32.59 | 30.84 | 30.03 | 29.26 | 27.84 | 26.86 |

Step between adjacent codes: 1.80 % (code 0→1) falling to 1.16 % (code 30→31). Duty 49.78–49.86 %.
IDD 229.9–233.5 µA. Loop delay (va crosses vth → bank B released) 1.17–1.40 ns; comparator alone 0.90–1.12 ns.

### Trim reach at the extreme corners (`r1a-reach`)

| Corner | Code 0 | Code 16 | Code 22 | Code 31 | Step range | Loop delay max | IDD max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ss / 1.08 V / 125 °C | 32.61 MHz | 25.24 MHz | 23.27 MHz | 20.84 MHz | 1.15–1.78 % | 2.32 ns | 175 µA |
| ff / 1.32 V / −40 °C | 54.88 MHz | 42.28 MHz | 38.94 MHz | 34.81 MHz | 1.17–1.81 % | 0.85 ns | 311 µA |

### PVT at fixed code (`r1a-corners27-c16`, `r1a-corners27-c22`)

| Code | tt/1.2/27 | min (corner) | max (corner) | Spread | IDD range |
| --- | --- | --- | --- | --- | --- |
| 16 | 32.59 MHz | 25.24 MHz (ss/1.08/125) | 42.28 MHz (ff/1.32/−40) | −22.6 / +29.7 % | 170–311 µA |
| 22 | 30.03 MHz | 23.27 MHz (ss/1.08/125) | 38.94 MHz (ff/1.32/−40) | −22.5 / +29.7 % | 169–310 µA |

At tt, code 22: −40 / 27 / 125 °C give 30.35 / 30.03 / 29.46 MHz (−2.9 % over the range). 1.08 / 1.2 / 1.32 V give
29.55 / 30.03 / 30.39 MHz (≈ 12 %/V around 1.2 V). The RC corners (res and cap ±10 % each) set most of the spread.

### Supply sensitivity, tt / 27 °C, code 16 (`r1a-psrr`)

| Case | Result |
| --- | --- |
| 10 mV step | +117 ppm/mV (32.594 → 32.632 MHz) |
| 20 kHz, 10 mV peak | +110 ppm/mV (regression of each period on the supply, quarter ripple period) |
| 1 MHz, 10 mV peak | FM amplitude 373 ppm/mV, phase +54°; f 32.47–32.72 MHz |

10 mV of slow ripple moves f by ≈ 0.12 % (S5 estimate 0.17 %). At 1 MHz the FM is 3.2 × larger (open issue 5).

### Start-up and enable (`r1a-startup`, code 16)

| Corner | First edge after `en` rises | f after enable | `osc_clk` max while `en` = 0 (ramp) | First edge, `en` tied to `vdd` (1 µs ramp) |
| --- | --- | --- | --- | --- |
| tt / 1.2 / 27 | 15.6 ns | 32.594 MHz | 38 mV | 0.502 µs |
| ss / 1.08 / 125 | 20.2 ns | 25.237 MHz | 45 mV | 0.508 µs |
| ff / 1.32 / −40 | 12.1 ns | 42.284 MHz | 34 mV | 0.486 µs |

The second enable gives the same first-edge delay and frequency. While `en` = 0 after running, `osc_clk` stays
below 1 µV.

### Mismatch (`r1a-mc50`: tt / 1.2 V / 27 °C, code 16, 50 samples)

| Quantity | Mean | σ | Range |
| --- | --- | --- | --- |
| f | 32.52 MHz | 0.227 MHz (0.70 %) | 32.11–32.98 MHz |
| Duty | 49.83 % | 0.54 % | 48.57–51.31 % |
| IDD | 231.1 µA | 0.4 µA | 230.1–232.0 µA |
| Loop delay | 1.32 ns | 0.19 ns | 1.01–1.97 ns |
| vth | 600.0 mV | 0.45 mV | 599.1–601.0 mV |

Slow-corner reach under mismatch (`r1a-mcreach`, ss/1.08 V/125 °C, code 0, 50 samples): mean 32.52 MHz,
σ 0.254 MHz (0.78 %), range 32.04–32.98 MHz. No sample is below 32 MHz, but mean − 3σ = 31.76 MHz.

### Comparator noise (`r1b-cmpnoise`, tt / 1.2 V / 27 °C, inputs at 0.6 V)

Gain to the first-stage output 22.7 dB, −3 dB at 0.44 GHz. Input-referred noise 33.1 / 15.3 / 12.2 nV/√Hz at
1 / 10 / 100 MHz. Output noise 1 kHz–1 GHz 3.96 mV rms, which is 0.29 mV rms referred through the DC gain.
With a ramp slope of ≈ 29 mV/ns at the threshold this is ≈ 10 ps per crossing (*estimated*).

### Jitter (`r1b-jitter`, tt / 1.2 V / 27 °C, code 22)

Transient noise with `trnoise` sources (white only): 12.2 nV/√Hz in series with the + input of each comparator
(from `r1b-cmpnoise`) and 4kT/R current across RA and RB; noise sample time 50 ps; 15 µs, 439 periods.

| Case | Run | Mean period | σ period | σ over 30 cycles |
| --- | --- | --- | --- | --- |
| Noise | `r1b-jitter` | 33.300 ns (30.03 MHz) | 14.9 ps (449 ppm) | 103 ps |
| No noise (numerical floor, max step 50 ps) | `r1c-jitter-ref` | 33.307 ns | 1.1 ps | 5.3 ps |

Against the S5 budget for the ≈ 1 µs (≈ 30-cycle) sample-to-latch window: 1.39 ns rms allowed (13 × margin),
0.28 ns to stay below 12-bit angle quantisation (2.7 × margin). The σ over 30 cycles is larger than √30 × σ period
(82 ps), so successive periods are positively correlated. With 439 periods, the σ-period estimate has ≈ ±3 %
statistical uncertainty and the 30-cycle estimate ≈ ±20 % (*estimated*). 1/f noise is not included (open issue 6).

## Area and current

Area (*estimated*, no layout):

| Part | Drawn | Footprint estimate |
| --- | --- | --- |
| MIM, two banks: 2 × (815 µm² fixed + 31 × 16.24 µm² units) | 2 637 µm² (2 × 2.0 pF at code 31) | ≈ 3 470 µm² with 0.6 µm spacing and enclosure |
| MIM, threshold hold cap 26 × 26 µm | 676 µm² | ≈ 740 µm² |
| `rppd`, w = 1 µm: 2 × 48.3 (RA/RB) + 2 × 384.3 (divider) + 80 (bias) = 945 µm | 945 µm² | ≈ 1 900 µm² at 2 µm pitch |
| MOS (≈ 70 devices) and local routing | — | ≈ 1 500 µm² |
| Sum of footprints | — | ≈ 7 600 µm² |
| Macro at the G1 packing ratio (G1: 0.0228 mm² for ≈ 9 600 µm² of footprint, ratio 2.4) | — | **≈ 0.018 mm²** |

G1 R0.95 used 4 679 µm² of MIM; R1 uses 3 313 µm². A tighter layout than G1 could reach ≈ 0.012 mm².

Current (simulated): 231 µA at tt/1.2 V/27 °C (code 16 and code 22), 169–311 µA over the 27 PVT points. Main
parts (*estimated*): two comparator tails ≈ 2 × 60 µA, bias reference ≈ 30 µA, bank charging
C·V·2f ≈ 1.78 pF × 0.64 V × 60 MHz ≈ 68 µA, divider 6 µA.

## Layout (T1, 2026-10-21)

Layout of record: **layout k** (`layout/r1_osc.gds`, sha256 `0b98903c…c0059`, generator sha256 `e0394750…6b73e`).
PEX of record: `pex-rc-20261021-h` (PEX netlist sha256 `86ce652d…36b8a`). Netlist of record:
`schematic/r1_osc.spice` sha256 `d9d84501…5cd949` (unchanged in this step).

### Commands

From the repository root (POSIX sh):

```
G1_CPUSET=100-102; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
sh designs/r1-joint/blocks/r1_osc/layout/run_checks.sh 20261021-k
sh designs/r1-joint/blocks/r1_osc/layout/run_pex.sh 20261021-k 20261021-h
G1_CPUS=1; export G1_CPUS; G1_WORKDIR=designs/r1-joint/blocks/r1_osc; export G1_WORKDIR
P=<G1_RESULTS_ROOT>/r1_osc/pex-rc-20261021-h
flow/run.sh python3 sim/run_osc30.py trim32 <run-id> --jobs 1 --netlist $P/r1_osc_pex.spice
flow/run.sh python3 sim/run_osc30.py reach <run-id> --jobs 1 --netlist $P/r1_osc_pex.spice
flow/run.sh python3 sim/run_osc30.py jitter <run-id> --jobs 1 --cases "noise ref" --code 22 --tstop 6u \
  --method gear --en 12.2e-9 --netlist $P/r1_osc_pex.spice
```

DRC: PDK `run_drc.py --run_mode=deep --no_density` (main + `sg13g2_maximal` tables) and `--antenna_only`.
LVS: PDK `run_lvs.py --run_mode=deep`. Outputs go to `<G1_RESULTS_ROOT>/r1_osc/<run-id>/`.

### Floorplan

Macro 154.4 × 118.4 µm = **0.01828 mm²** (estimate before layout: ≈ 0.018 mm²; the tighter ≈ 0.012 mm² of C10
is not realised). `vss` bar (Metal3) at the bottom edge, `vdd` bar (Metal3) at the top edge, p+ guard ring
(Activ + pSD + Metal1) 1.0 µm inside the edge.

- **Bottom (y 2–20 µm), east half:** five device row groups from west to east: trim switches (10 NMOS),
  comparator A (+ bias diode), latch and enable logic (+ reset switches RA, RB), comparator B, output buffer.
  Each comparator is in one group with its PMOS partners. Inter-group nets: `ca`, `cb`, `qn_b`.
- **Metal4 channel (y 21–43 µm):** 28 horizontal tracks at 0.8 µm pitch. `va`, `vb`, `vth` and `vbn` are
  separated by `vss` shield tracks (`vbn | vss | va | vss | vb | vss | vth`). The shields join `vss` at three points.
- **West (x 3–53 µm):** `rppd` block: bias resistor, the 16-segment threshold divider, RA and RB, and `rppd`
  dummies at both ends. The threshold hold cap (26 × 26 µm `cmim`) is above it.
- **North-east:** trim banks A and B. Each bank is a 9 × 6 grid of 4.03 µm unit caps at 5.9 µm pitch plus the
  28.55 µm fixed cap. Bits 0…4 use 1/2/4/8/16 units. The grid edge (column 0, rows 0 and 5) has 22 dummy units per
  bank in the same orientation; their plates connect to `vss`.
- **Timing R and C vs output buffer:** the buffer is the eastmost group. `osc_clk` runs on Metal3 below the channel
  to the east edge. Extracted coupling from `osc_clk` to `va`, `vb`, `vth`: 0 (no capacitor in the PEX netlist);
  its largest coupling is 0.78 fF to `qn_b`.
- **Pins (Metal3, at the edge):** `en`, `trim0`…`trim4` on the west edge; `osc_clk` on the east edge; `vdd` and
  `vss` bars. An antenna diode (`dpantenna`) is on the `vth` gate input of comparator A.
- **Metals:** all routing is on Metal1–Metal4. Metal5 and TopMetal1 are used only for the MIM plates and the
  plate-to-plate joins inside a bank (this is the interpretation of "Metal1–Metal4 only" that was recorded).

Shield effect (layout j → layout k, PEX `pex-rc-20261021-g` → `-h`): `vb`–`vth` coupling 8.2 → 0.57 fF;
`va`–`vbn` 5.5 → 0.91 fF.

### Extraction method

The method of `r1_bgr`. kpex 0.3.12 (2.5D) gives the coupling capacitance. kpex cannot process the MIM layers, so
`pex_input.py` removes them from its input. KLayout `RNetExtractor` gives the wiring resistance (Metal1
0.110 Ω/sq, Metal2–Metal4 0.088 Ω/sq, 9 Ω per via cut). `pex_build.py` re-inserts the 13 `cap_cmim` devices at
their attach points. It writes three views: full RC (`r1_osc_pex.spice`), wiring C with R shorted
(`r1_osc_pex_c.spice`), and devices + MIM only (`r1_osc_pex_dev.spice`). PEX `-h` totals: 223 R, 498 C,
486 fF. Net totals: `va` 28.4, `vb` 39.0, `vth` 34.8, bit nodes 14.2–22.7, `ca` 14.8, `q` 22.6 fF.

### Status (layout and post-layout)

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| DRC, main + maximal, deep, density off | 0 markers | **passed**: 0 | `layout/runs/layout-drc-20261021-k` |
| Antenna | 0 markers | **passed**: 0 | `layout/runs/layout-ant-20261021-k` |
| LVS vs netlist of record (dummies excluded, see below) | match | **passed**: 34 NMOS, 19 PMOS, 5 `rppd`, 13 `cap_cmim` (65 units), 1 `dpantenna` after combination; 43 nets | `layout/runs/layout-lvs-20261021-k` |
| Density | — | **not applicable** at block level (waived; chip-level fill) | — |
| Pins Metal3 at the edge | 9 pins | **passed** | `layout/r1_osc_layout.py` |
| Area | ≈ 0.018 mm² | **passed**: 0.01828 mm² | `layout/r1_osc_layout_meta.json` |
| PEX (RC) | extracted | **passed** | `layout/runs/pex-rc-20261021-h` |
| Post-layout trim, 32 codes, tt | monotonic, step ≤ 2 % | **failed**: monotonic; step 0.73–2.52 % (> 2 % at codes 3→4, 7→8, 15→16) | `sim/runs/post-trim32-tt-20261021` |
| Post-layout trim, 32 codes, ss/1.08 V/125 °C and ff/1.32 V/−40 °C | monotonic, step ≤ 2 % | **failed**: monotonic; step max 2.41 % (ss), 2.63 % (ff) | `sim/runs/post-reach-20261021` |
| Post-layout reach at ss/1.08 V/125 °C | ≥ 32 MHz at code 0 | **failed**: 28.36 MHz | same |
| Post-layout code 22, tt | 28–32 MHz (D13 window) | **failed**: 27.54 MHz | `sim/runs/post-trim32-tt-20261021` |
| Post-layout code 22, ff/1.32 V/−40 °C | ≤ 42 MHz (STA) | **passed**: 35.86 MHz | `sim/runs/post-reach-20261021` |
| Post-layout duty, 3 × 32 codes | 50 % | **passed**: 49.03–49.52 % | trim32 + reach runs |
| Post-layout loop delay | ≤ 3–4 ns | **passed**, small margin: max 3.91 ns (ss/1.08 V/125 °C, code 31) | `sim/runs/post-reach-20261021` |
| Post-layout IDD | record | 228.0 µA (tt, code 22); 171–307 µA over the 3 corners | trim32 + reach runs |
| Post-layout jitter, tt, code 22 | ≤ 280 ps over 30 cycles | **passed**: σ period 12.8 ps, σ 30 cycles 39.1 ps (6 µs, 154 periods; floor 0.47 ps with gear, 0.38 ps trapezoidal over 15 µs) | `sim/runs/post-jitter-20261021-b`, `sim/runs/post-jitter-ref-20261021` |
| Post-layout PVT points other than tt, ss/1.08/125, ff/1.32/−40; mismatch; start-up; supply ripple | — | **not run** | — |
| LEF / abstract | — | **not run** | — |

### Pre- versus post-layout

Frequencies in MHz. "Devices" = layout devices and MIM, no wiring. "Wiring C" = + wiring capacitance, R shorted.
"Full RC" = PEX of record. Evidence: `r1a-trim32-tt`, `r1a-reach`, `post-attr-r1_osc_pex_dev-20261021`,
`post-attr-r1_osc_pex_c-20261021`, `post-trim32-tt-20261021`, `post-reach-20261021`.

| Point | Schematic | Devices | Wiring C | Full RC | RC vs schematic |
| --- | --- | --- | --- | --- | --- |
| tt/1.2 V/27 °C, code 0 | 42.24 | 42.07 | 37.15 | 37.11 | −12.1 % |
| tt, code 15 | 33.07 | — | — | 30.27 | −8.5 % |
| tt, code 22 | 30.03 | 29.90 | 27.62 | 27.54 | −8.3 % |
| tt, code 31 | 26.86 | 26.74 | 25.17 | 25.09 | −6.6 % |
| ss/1.08 V/125 °C, code 0 | 32.61 | 32.51 | 28.45 | 28.36 | −13.0 % |
| ss, code 22 | 23.27 | 23.19 | 21.24 | 21.15 | −9.1 % |
| ff/1.32 V/−40 °C, code 15 | 42.91 | — | — | 39.45 | −8.1 % |
| ff, code 22 | 38.94 | 38.73 | 35.94 | 35.86 | −7.9 % |
| Loop delay, tt code 22 (ns) | 1.33 | 1.33 | 2.22 | 2.34 | +1.0 ns |
| IDD, tt code 22 (µA) | 230.6 | 229.5 | 234.8 | 228.0 | −1.1 % |
| Duty, tt code 22 (%) | 49.85 | 49.85 | 49.47 | 49.39 | −0.46 pt |
| Trim step, tt (%) | 1.16–1.80 | — | — | 0.73–2.52 | — |
| σ period / σ 30 cycles, tt code 22 (ps) | 14.9 / 103 | — | — | 12.8 / 39.1 | fewer periods (see L6) |

Device parasitics (junctions, MIM model) change the frequency by less than 0.6 %. Wiring capacitance causes the
loss. Wiring resistance adds less than 0.5 %. The loss is larger at code 0 than at code 31, so part of it is
fixed (loop delay +1.0 ns at tt) and part is proportional to C (bank wiring ≈ 50 fF per bank, *estimated* from
the attribution views).

**Reset code.** With layout k, code 22 gives 27.54 MHz at tt. This is outside the D13 window 28–32 MHz. The code
nearest 30.0 MHz is **15** (30.27 MHz at tt; 39.45 MHz at ff/1.32 V/−40 °C, below the 42 MHz STA limit). If
layout k is used without a schematic change, `OSC_TRIM` must reset to 15, not 22. Owner of `r1_ctrl`: decision
needed (this step did not change `r1_ctrl`). Recommended option: the RA/RB change in L1, which keeps 22.

### Open issues (layout)

- **L1. Reach at ss/1.08 V/125 °C fails after layout** (28.36 MHz at code 0; target 32 MHz). The fix is a
  schematic change. What-if runs (PEX netlist with the RA/RB `rppd` length edited; not a design):
  RA/RB × 0.85 (48.3 → 41.1 µm) gives ss code 0 **32.67 MHz**, tt code 22 **31.94 MHz**, ff code 22
  **41.63 MHz** (0.9 % below 42 MHz). RA/RB × 0.75 gives 36.36 / 35.75 / 46.64 MHz (ff fails 42 MHz). Evidence:
  `sim/runs/post-whatif-ra0.85-20261021`, `sim/runs/post-whatif-ra0.75-20261021`. Recommended: RA/RB ≈ 41 µm in
  a schematic revision, then re-generate the layout (only the RA/RB lengths change) and re-run PEX and the
  post-layout suites. The ff margin to 42 MHz is then small.
- **L2. Trim step > 2 % at the carry codes** (3→4, 7→8, 15→16). Cause (*estimated*, not isolated by a run): each
  bit node has 14–23 fF of wiring to its switch. When the switch is off, this capacitance is in series with the
  bit MIM, so an off bit still adds capacitance. This makes the bits non-binary. Fix options: move the trim
  switches next to the banks, or add one unit to bits 2–4. Not done in this step.
- **L3. MIM bottom-plate parasitics.** kpex cannot process MIM. Only the `cap_cmim` model capacitance is in the
  PEX netlist. The plate-to-substrate capacitance of the Metal5 plates is **not modelled**.
- **L4. Metal5 and TopMetal1** carry the MIM plates and the plate joins inside each bank. All signal routing is on
  Metal1–Metal4. If the chip integration needs Metal5 over this block, the bank area must be blocked.
- **L5. LVS and dummies.** The PDK LVS deck deletes two-terminal devices with both terminals on one net. The
  44 dummy MIM units (both plates on `vss`) are not in the extracted netlist, so they are not in the CDL.
  Internal labels (Metal2: `ca cb q qb rsta rstb en_n qn_b`; Metal4: `va vb vth vbn`, `ba0`…`bb4` in the PEX
  input only) name nets for PEX. They are not pins.
- **L6. Jitter statistics.** The post-layout run is 6 µs (154 periods), not 15 µs, because a 15 µs run at the
  50 ps step did not fit the time budget. The σ 30-cycle number uses few independent windows and is less
  reliable than the schematic number. Trapezoidal integration aborts on the PEX netlist with `trnoise`
  (`post-jitter-20261021`); the run of record uses `.option method=gear` (runner option `--method`).
- **L7. Not run:** LEF/abstract, density (block level), post-layout PVT at other points, mismatch, start-up and
  supply ripple on the PEX netlist.

### Failures and mistakes (layout step)

| # | What happened | Class | Evidence |
| --- | --- | --- | --- |
| 1 | DRC: TopMetal1 strap of the fixed cap stopped 0.2 µm past the plate, but the plate TopMetal1 starts 0.415 µm in (TM1.b × 8); a Via3 and a Metal3 pad too small (V3.b, M3.d); a shield track with one connection (M4.d) | estimation | `layout/runs/layout-drc-20261021-a` |
| 2 | Antenna: `trim0`/`trim1` gate ratio 209–216 > 200 on 0.24 µm tracks; fixed with 0.20 µm tracks | estimation | `layout/runs/layout-ant-20261021-a` |
| 3 | LVS: fixed-cap top plate not connected; dummy MIM units (both plates on `vss`) are deleted by the deck but were in the CDL | verification-gap | `layout/runs/layout-lvs-20261021-a` |
| 4 | Generator crash (CDL header string format) | functional-bug | `layout/runs/layout-gen-20261021-b` |
| 5 | Run c clean, but the `vbn` label was off its track, so the net was unnamed in PEX | verification-gap | `layout/runs/layout-gen-20261021-c` |
| 6 | GDS hash changed on each re-generation (GDS timestamps); fixed with a deterministic write | tooling | `layout/runs/layout-gen-20261021-e` |
| 7 | `run_pex.sh` gave kpex a container prefix + absolute path for the schematic | tooling | `layout/runs/pex-in-20261021-b` |
| 8 | First floorplan (one 89 µm device row) put PMOS ≈ 50 µm from their NMOS partners: ≈ 25 fF per node, loop delay 3.9 ns, 25.34 MHz at tt code 22. Four more floorplans (three, four, five row groups) followed | planning | `sim/runs/post-c22-tt-20261021-a`, `post-probe-20261021-c`, `-d-*`, `-g-*` |
| 9 | DRC: `vss` vias in the buffer group 0.31 µm apart near a ring via (13 markers) | regression | `layout/runs/layout-drc-20261021-h` |
| 10 | LVS: the buffer `vss` rail had no via after the group split | regression | `layout/runs/layout-lvs-20261021-i` |
| 11 | Post-layout jitter aborted (timestep too small, trapezoidal + `trnoise`) | numerical | `sim/runs/post-jitter-20261021` |
| 12 | The runner wrote the absolute results path into the `command` field of `run.json`; fixed in the runner and in the existing records | process-hygiene | `sim/run_osc30.py` |
| 13 | Post-layout loss (8–13 %) was predicted from G1 (9–13 %, open issue 3) but no schematic margin was added; reach and the D13 window now fail | planning | this section |
| 14 | The fix for #12 had a bug (`.replace` on a tuple). `r1d-trim32-cross` finished all 64 jobs (rc 0) but crashed before `run.json`; the record was written by hand | regression | `sim/runs/r1d-trim32-cross/run.json` |

## Open issues

1. **30 MHz at the mid code conflicts with the reach and step targets.** With a binary capacitor trim the
   smallest step is at code 0, so f(0)/f(16) ≤ 1 + 16·s. With s = 2 % this is ≤ 1.32. The slow corner
   ss/1.08 V/125 °C is ×0.771 of tt at code 0 (`tune02-probe`, `r1a-reach`). Then ≥ 32 MHz at that corner needs
   f(16, tt) ≥ 32/(0.771 × 1.32) ≈ 31.4 MHz. A higher comparator tail did not change the factor (`tune03-probe`).
   Decision in r1: keep step ≤ 2 % (max 1.81 %) and reach ≥ 32 MHz, and put 30 MHz at code 22.
   Owner of `r1_ctrl`: `OSC_TRIM` reset value 22.
2. **The fast corner cannot be trimmed to 30 MHz.** At ff/1.32 V/−40 °C code 31 gives 34.8 MHz. After trim, the
   frequency is in 30–35 MHz over PVT. The host must write `TIMEOUT_TICKS` from the measured `OSC_COUNT`, as S5
   specifies. STA: 38.9 MHz untrimmed at the reset code; 54.9 MHz if the host writes code 0 at ff.
3. **Reach margin is small, and layout is not included.** The margin at ss/1.08 V/125 °C is 1.9 % nominal and
   2.4 σ of local mismatch (mean − 3σ = 31.76 MHz). G1 lost
   9–13 % of frequency after layout. In R1 the bank parasitic adds to C_fix, so the fixed capacitor must be
   reduced by the extracted bank capacitance after PEX. Re-run `reach` and `trim32` on the extracted netlist.
   Update 2026-10-21: done. After layout, reach fails (28.36 MHz). See "Layout", L1.
4. **Duty under mismatch** is 48.6–51.3 % (50 samples). No duty limit is specified. If the digital block uses
   both edges, specify the limit.
5. **1 MHz supply ripple** gives 3.2 × the DC frequency sensitivity (373 vs 117 ppm/mV). The cause is not analysed.
   The 1.2 V core supply ripple spectrum is not specified.
6. **Jitter deck** uses white noise only (comparator input and 4kT/R). 1/f noise (33 nV/√Hz at 1 MHz) and the
   threshold-divider noise are not in the transient-noise run.
7. Full 32-code trim at all 27 PVT points, and mismatch MC at corners other than tt/code 16 and the ss reach point:
   **not run**.
8. The S5 RTL bench `tb_clkcal` (`OSC_COUNT`, `TIMEOUT_TICKS`, SSI monoflop) belongs to `r1_ctrl`: not run here.
