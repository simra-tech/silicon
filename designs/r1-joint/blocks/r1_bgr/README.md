# r1_bgr — compact bandgap reference with PTAT current (R1)

State (2026-10-20): **schematic simulated** (revision r1). Layout not run. All numbers are
simulated (ngspice 46, schematic level); nothing is measured.

## What it is

The G1 Sep-19 op-amp-less cascoded HBT bandgap (`designs/g1-guardian/blocks/g1_bgr/xschem/g1_bgr.spice`,
sha256 `fa925507…`), re-proportioned for mismatch (PLAN.md D5). Outputs: `vref` (1.045 V), `iptat`
(4.2 µA PTAT leg), and the mirror rails `pbias`/`pcasc` for the T2F. Monitor pins `vbe`, `dvbe`.
Supply: VDDA 3.0–3.6 V (thick-oxide `sg13_hv_*` MOS, `npn13G2`, `rppd`, `rhigh`).

Why the G1 cell was not enough: the PDK HBT mismatch model draws **one 10 % area factor per instance,
independent of `Nx`** (`sg13g2_hbt_mod_mismatch.lib`: `qarea = agauss(1, 0.1, 1)`). Only separate unit
instances average it. The Sep-19 cell (Q1 = 1 unit, Q2 = 8 units) gave σ(V<sub>REF</sub>) = 1.84 %.
BGR586 averaged by copying the whole loop (301 HBT, 0.148 mm²). r1_bgr averages only the ΔV<sub>BE</sub>
pair and adds a mirror current ratio, which raises ΔV<sub>BE</sub> and lowers the PTAT gain:

| Item | G1 Sep-19 | r1_bgr |
| --- | --- | --- |
| Q1 / Q2 / Q3 unit instances | 1 / 8 / 1 | **12 / 48 / 4** |
| Q1-branch mirror legs (current ratio) | 1 (1:1) | **8 (8:1)** |
| ΔV<sub>BE</sub> = V<sub>T</sub> ln(M·N2/N1) at 27 °C | 55.1 mV (ln 8) | **91.1 mV** (ln 32) |
| R1 / R2 (`rppd`, w = 1 µm) | 51.5 / 315 µm | **84 / 347.5 µm** |
| RB / RX / start-up | 500 / 192 µm, kick on `pbias` | unchanged |
| Unit PMOS leg (mirror + cascode) | 10/4 µm, ≈ 4.1 µA | unchanged (T2F legs stay compatible) |
| `r4` 1:4 test mode | yes | **removed** (not in the R1 interface) |

Expected mismatch budget before simulation (1σ on V<sub>REF</sub>): HBT pair 3.5 mV, Q3 1.3 mV,
R1/R2 1.0 mV, mirror 0.5 mV → 3.9 mV (0.37 %). Simulated: 4.18 mV (0.40 %).

Pins: `vdd vss vref iptat pbias pcasc vbe dvbe`.

## Files

| Path | What |
| --- | --- |
| `schematic/gen_r1_bgr.py` | netlist generator (parameters n1, n2, n3, m, r1, r2, rb, rx) |
| `schematic/r1_bgr.spice` | frozen netlist, sha256 `c19a7425d605906962724fdda21add8ae3926dc9a097c6f835a16f05f92c0c26` (108 devices: 66 `npn13G2`, 26 HV PMOS, 11 HV NMOS, 5 resistors) |
| `sim/tb_r1_bgr.spice.tmpl`, `sim/run_bgr.py`, `sim/.spiceinit` | testbench template and runner (suites `size temp mc psrr startup op`) |
| `sim/probe/` | unit-device mismatch probe |
| `sim/results/<run-id>.json` | summaries; `sim/runs/<run-id>/run.json` per run; raw decks, logs, waveforms at `<G1_RESULTS_ROOT>/r1_bgr/<run-id>/` |

Loads in every deck (as on G1): `iptat` sinks into a 1.0 V source, `vref` carries 1 pF.
Corner names: `hbt_typ/bcs/wcs`, `mos_tt/ss/ff`, `res_typ/bcs/wcs`.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` in the container (checked by `flow/run.sh`) |
| ngspice | 46 (KLU), PSP 103 and R3 via OSDI | `ngspice -v` in the container |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| xschem / KLayout | not used (netlist generator; no layout) | — |

Command (from the repository root): `G1_CPUSET=116,117 G1_CPUS=2 G1_WORKDIR=designs/r1-joint/blocks/r1_bgr/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> flow/run.sh python3 run_bgr.py <suite> <run-id>`.

## Status

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| Unit-device mismatch probe | record | run: PMOS 10/4 σ(I) 0.41 %, `rppd` 1×51.5 µm 0.31 %, HBT 10 % per instance (model) | `bgr-probe-mismatch-20261020` |
| R2 for zero TC and V<sub>REF</sub> 1.045 V | record | run: R2 = 347.5 µm | `bgr-size-20261020-d` |
| V<sub>REF</sub> at tt/27 °C | 1.045 V | **passed**: 1.0449 V (3.0 / 3.3 / 3.6 V identical to 0.01 mV) | `bgr-temp-20261020-b` |
| TC box −40…125 °C, nominal | ≤ 30 ppm/°C | **passed**: 8.4 ppm/°C | same |
| TC box, 27 process corners × 3 supplies | ≤ 30 ppm/°C | **failed** 9/81: hbt_wcs + res_bcs gives 34.4–35.1 ppm/°C; other 72 runs 8.3–25.8 | same |
| V<sub>REF</sub> spread over corners | record | 1.0359–1.0558 V at 27 °C (±0.95 %) | same |
| Supply current | ≤ 100 µA | **passed**: 51.8 µA tt/27 °C; max 79.6 µA (res_bcs, 125 °C) over 81 runs × −40…125 °C | same, `bgr-op-20261020-b` |
| Mismatch, 50 samples, 27 °C, 3.3 V | σ(V<sub>REF</sub>) ≤ 0.5 % | **passed**: σ 4.18 mV = 0.40 %, range 1.0332–1.0546 V, 50/50 completed | `bgr-mc-20261020-b` |
| TC under mismatch (same 50 samples) | ≤ 30 ppm/°C | **passed**: 50/50, mean 13.4, max 27.6 ppm/°C | same |
| `iptat` | record | 4.20 µA at 27 °C (3.71–4.81 µA over res corners); σ 1.08 % (MC) | `bgr-temp-…-b`, `bgr-mc-…-b` |
| Start-up, 5 corner/temperature points × {1 ms, 10 µs} ramp to 3.0 V | starts, ends 0.95–1.15 V | **passed** 10/10; 1 % settled 0.55–0.66 ms (1 ms ramp), 7.9–8.7 µs (10 µs ramp); overshoot ≤ 1.115 V (ss/−40 °C, 10 µs ramp) | `bgr-startup-20261020-b` |
| PSRR 20 kHz / 1 MHz (tt27, ss125 @3.0 V, ff−40 @3.6 V, tt27 @3.0 V, tt125 @3.0 V) | no limit specified | **run**: 20 kHz −54.2…−56.8 dB; 1 MHz −26.1…−27.3 dB; DC ≤ −100 dB | `bgr-psrr-20261020-b` |
| Device headroom (5 corners × −40/27/125 °C × 3.0/3.6 V) | record | run, 30/30 converged: mirror V<sub>DS</sub> ≥ 0.42 V, Q2 V<sub>CE</sub> 0.51–0.83 V | `bgr-op-20261020-b` |
| Loop stability (AC loop gain / phase) | — | **not run** | — |
| Noise | — | **not run** | — |
| Mismatch at −40 / 125 °C and at corners | — | **not run** (TC per sample covers −40…125 °C at tt only) | — |
| Load: ADC reference buffer, r1_safe DAC, T2F with r1_bgr rails | — | **not run** | — |
| Layout, DRC, LVS, PEX | — | **not run** | — |
| Runs `bgr-size-20261020-a/b/c`, `bgr-temp-20261020-a` | — | **invalid**, kept as record: RB generated as 130 µm instead of 500 µm (unit error in the runner) | `sim/runs/*/run.json` |

## Area and current

| Quantity | Value | Basis |
| --- | --- | --- |
| Area | **≈ 0.016–0.020 mm² (estimated)** | G1 Sep-19 macro 84 × 124 µm (laid out) plus: HBT array 66 active + dummies (≈ 8 × 13 units at 6.3 × 6.7 µm, +≈ 40 µm height), a second mirror row and cascode row for the 7 extra legs (+≈ 25 µm), 7 extra NMOS 20/1 (+≈ 5 µm): ≈ 84 × 195 µm. Resistor area unchanged within 6 %. Not laid out. |
| Comparison | Sep-19 0.0104 mm², BGR586 0.148 mm² | G1 README |
| VDDA current | 51.8 µA (tt/27 °C), 35.5–79.6 µA over corners and −40…125 °C | simulated |

Current split at tt/27 °C (4.2 µA per unit leg): Q1 branch 8 legs 33.6 µA, Q2, cascode bias, `vref`, `iptat`
and start-up detector one leg each.

## Open issues

1. **Corner TC** fails 30 ppm/°C at hbt_wcs + res_bcs (35 ppm/°C). It is a shift of the zero-TC point
   with no trim. Options: a 2-bit tap on R2 (±1 % range), or accept, because the ADC full scale is
   absorbed by host weights and the AFE gain register (spec D11). Owner decision.
2. **Q2 current density** is 0.088 µA per unit at 27 °C (Q1 2.8 µA, Q3 1.05 µA). The model card states
   V<sub>BE</sub> 0.65–0.96 V as its fitted range; Q1 runs at 0.56–0.78 V and Q2 at about 0.44–0.71 V (V<sub>BE1</sub> − ΔV<sub>BE</sub>) over corners and −40…125 °C. The
   ΔV<sub>BE</sub> at low density is a model extrapolation. G1 Sep-19 ran Q2 at 0.5 µA per unit.
3. **PSRR at 1 MHz** is about −26 dB (10 mV ripple gives ≈ 0.5 mV on `vref`). The ADC reference
   buffer and its MIM decoupling must filter it; a `vref` RC filter is not in this revision.
4. `vref` is unbuffered (≈ 90 kΩ source). Every consumer needs a buffer (INTERFACES: ADC reference buffer).
5. Start-up overshoot to 1.115 V with a 10 µs supply ramp at ss/−40 °C settles in 8.6 µs; check the
   reference buffer input range.
6. The `r4` HBT-ratio test mode of G1 is removed. If the T2F RATIO mode is wanted on R1, it must come back.
7. Loop stability, noise, mismatch at corners, joint T2F simulation with these rails, and layout: not run.
