# R1_OSC — 30 MHz RC relaxation oscillator (revision r1: schematic and layout)

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
| `layout/r1_osc.gds` | Layout of record (layout k), sha256 `0b98903c7e04bbdaec6cbef6e60f610d2f6a5b993ebc158a09294e2c2db0c059`. Written without GDS timestamps, so a re-run gives the same hash. |
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
