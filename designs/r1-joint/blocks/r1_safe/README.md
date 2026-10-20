# r1_safe (analog part) — window comparators with 6-bit threshold DACs

State (2026-10-20): **schematic level, simulated.** No layout, no extraction. All numbers below are
**simulated** (ngspice-46, pinned PDK), at schematic level, with ideal reference sources (marked in each
deck). Nothing is measured. The digital part of r1_safe (blanking, latching, fault logic) is in r1_ctrl and is
not part of this directory.

## What it is

Per sense channel (a, b) there are two continuous-time comparators on the r1_isense differential output
(OUTP − OUTN = Vod):

- **OC** (overcurrent, high side of the window): output high when Vod > Vth(code_hi).
- **NEG** (negative current or phase short, low side of the window): output high when Vod < Vth(code_lo).

```
Vth_od(code) = (2*code - 63)/63 * VREF                    (VREF = 1.05 V: -1.05 V .. +1.05 V, 33.3 mV per code)
Vsh_th(code) = VREF * (1/26 + (2*code - 63)/882)          (shunt-referred through r1_isense G = 14, pedestal VREF/26)
             = -34.6 mV (code 0) .. +115.4 mV (code 63), 2.381 mV per code
```

- **Threshold DAC.** One 63-unit `rppd` string (unit 4 kΩ, w 2 µm, l 30.8 µm, 252 kΩ total, 4.2 µA from VREF) is
  shared by all four comparators. Each comparator has two 64:1 thick-NMOS tree multiplexers on the same code
  bits: REFP = T(code), REFN = T(63 − code). The threshold is a difference of two taps, so it depends on VREF and
  resistor ratios only. The same VREF sets the r1_isense pedestal, so VREF error moves the pedestal and the
  thresholds together.
- **Comparator** (`r1_safe_cmp`): differential-difference input stage with two thick-oxide PMOS pairs
  (w 20 µm, l 2 µm, ng 4), one pair on (INP, INN) and one pair on (REFN, REFP), into one NMOS mirror load
  (w 16 µm, l 4 µm). Each pair has a 40 µA tail and a source-degeneration resistor per side (`rhigh` w 1 µm,
  l 30 µm, about 40 kΩ). The degeneration keeps both pairs linear over the full ±1.05 V threshold range (revision 1
  had no degeneration and failed, see below). Then a gain stage (NMOS w 2 µm, l 2 µm, same current density as the
  mirror), an inverter on 3.3 V and a down-shift to 1.2 V logic (thick-input inverter on VDD, then a thin-oxide
  inverter). Hysteresis: a small current (three series thick PMOS w 0.5 µm, l 8 µm on the bias line)
  is steered by the output to one side of the mirror.
- **NEG** uses the same cell with INP/INN swapped and the code bits inverted (thin-oxide inverters), so
  REFP = T(63 − code_lo), REFN = T(code_lo).
- **Inputs are thick-oxide PMOS gates** (rated 3.3 V). No divider is in the signal path. The r1_isense outputs are
  ≤ VDD by construction, so the input is safe also in overload.
- **Continuous time, no clock.** There is no clock-edge race as in the G1 TRIP comparator (finding F1).
- Code bits are 1.2 V logic from the r1_ctrl registers, level-shifted to 3.3 V in the block (`r1_safe_ls`).

Interface assumptions:

| Item | Assumption in this step |
| --- | --- |
| Input | r1_isense OUTP/OUTN, 0.15–1.02 V each, common mode ≈ 0.57 V |
| VREF | 1.05 V, **buffered** (ideal source here); load 4.2 µA (string) |
| IBIAS | 5 µA PTAT per comparator, four inputs `ibias_oa`, `ibias_na`, `ibias_ob`, `ibias_nb` (ideal sources here) |
| Code bits | 6 + 6 bits per channel, 1.2 V logic, static during operation (a code change is a mux transient) |
| Outputs | `oc_a`, `neg_a`, `oc_b`, `neg_b`, 1.2 V logic, high = threshold crossed, not latched |
| Blanking | done in r1_ctrl: comparator outputs are invalid during r1_isense AZ and ≈ 200 ns after it |

## Status

Netlist of record: `schematic/r1_safe.spice`, revision 2, sha256 prefix `63ac3d0b7961`. Threshold LSB = 33.3 mV Vod
(2.381 mV shunt). Criterion for threshold accuracy: the threshold (centre of the hysteresis band) within ±0.5 LSB
(16.7 mV Vod) of the ideal value. The trip-point error (centre + half the hysteresis) is reported as well.

| Check | Status | Evidence |
| --- | --- | --- |
| Threshold vs code (4, 20, 32, 44, 59), OC and NEG, all four comparators in one netlist, tt/ss/ff, no mismatch | **passed**: centre error ≤ 1.6 mV (tt), ≤ 10.3 mV (ss), ≤ 0.2 mV (ff); 10/10 points per corner | `sim/results/safe-cmp-20261020-r2/` |
| Trip-point error (centre + hysteresis/2), same runs | run (report): ≤ 7.3 mV (tt), ≤ 17.4 mV = 0.52 LSB (ss, NEG code 4), ≤ 4.5 mV (ff) | same |
| Parked comparators (NEG_a at code 0, OC_b at code 63) stay quiet | **passed**, 3 corners | same |
| Delay < 300 ns at 10 % overdrive (OC code 55: 134.9 mV Vod; NEG code 8: 21.8 mV Vod), 10 fF load | **passed**: trip 26–39 ns (OC), 71–178 ns (NEG, worst ss); release 7–13 ns | same |
| Delay at ±1 LSB steps around the OC threshold (report) | run: 43–95 ns trip, 41–58 ns release | same |
| Hysteresis present | **passed**: 8.9–14.6 mV Vod (0.27–0.44 LSB), 0.64–1.04 mV shunt | same |
| Mismatch, 51 samples (`mm_ok=1`), comparator alone at +16.7, +916.7 and −916.7 mV Vod, DC | **failed**: centre error σ 32.1 mV (0.96 LSB), worst 79.5 mV (2.4 LSB); hysteresis σ 0.5 mV | `sim/results/safe-dcmc-20261020-r2/` |
| Mismatch MC of the full threshold path, transient (`tb_safe_mc.cir`, 51 samples) | **not run**: deferred, the DC MC above already fails | — |
| Revision 1 (no degeneration), same corner deck | **failed**: only code 32 (Vth 16.7 mV) resolves; at other codes both pairs saturate and the output does not follow the threshold; parked comparators trip | `sim/results/safe-cmp-20261020-r1/` |
| Two or more comparators switching at the same time on shared string taps | **not run** (the transient solver aborted in development runs `dev-solver-*`; the decks keep switching events apart) | — |
| Joint path r1_isense → r1_safe, AZ blanking | **not run** | — |
| Real VREF buffer and string loading, real bias, level-shifter timing at code change | **not run** (ideal sources) | — |
| Corners ss_cold / ff_hot for the full deck | **not run** (DC development runs only, `dev-dc-03`) | — |
| Layout, DRC, LVS, PEX | **not run** | — |

## Numbers (simulated, schematic level)

| Quantity | tt 27 °C | ss 125 °C | ff −40 °C |
| --- | --- | --- | --- |
| Supplies VDDA / VDD (V) | 3.3 / 1.2 | 3.0 / 1.08 | 3.6 / 1.32 |
| Max threshold (centre) error, 10 points (mV Vod) | 1.6 | 10.3 | 0.2 |
| Max trip-point error (mV Vod / µV shunt) | 7.3 / 522 | 17.4 / 1246 | 4.5 / 325 |
| Hysteresis (mV Vod) | 11.3–11.5 | 14.1–14.6 | 8.9–9.0 |
| OC trip delay, 10 % overdrive (ns) | 29 | 39 | 26 |
| NEG trip delay, 10 % overdrive (ns) | 90 | 178 | 71 |
| IDDA, four comparators, incl. 4 × 5 µA bias inputs (µA) | 398 | 358 | 341 |
| IDD (1.2 V) static (µA) | < 0.1 | < 0.1 | < 0.1 |
| VREF load, string (µA) | 4.2 | 4.2 | 4.2 |

The ss threshold error is systematic and grows with |Vth| (+4.9 mV at code 4 OC to +10.3 mV at code 59 OC). The
NEG delay at ss is long because the effective overdrive is 21.8 mV minus half the hysteresis minus the ss offset
(about 9 mV); overdrive in the deck is measured from the ideal threshold.

## Mismatch: what dominates

The degenerated pairs give the full ±1.05 V range, but every DC drop mismatch in the pair is now an offset:
the offset is about σ(mismatch) × (tail current × degeneration resistance), and that product is set by the range.
Development DC MC runs (12 samples each, seed 1) separate the parts:

| Variant | Centre error σ (mV Vod) | Run |
| --- | --- | --- |
| Revision 2 as built | 32 (51 samples) | `safe-dcmc-20261020-r2` |
| Degeneration resistors 16 × area (w 4, l 120 µm) | 17 | `dev-dcmc-V1` |
| Mirror load 16 × area (w 64, l 16 µm) | 27 | `dev-dcmc-V2` |
| Input pairs 16 × area | 33 | `dev-dcmc-V3` |

So `rhigh` mismatch gives about 27 mV σ and the mirror about 18 mV σ; the input pairs are negligible. Area
alone cannot reach the ±0.5 LSB target (a σ below about 4 mV needs about 50 × the resistor area and 25 × the mirror
area).

## Area (device area, from `schematic/area.py`)

| Item | µm² |
| --- | --- |
| Threshold string (63 `rppd` units) | 3881 |
| Four comparators (MOS 468 + `rhigh` 120 each) | 2352 |
| Eight 64:1 multiplexers, 24 level shifters, 12 inverters | 404 |
| **Total** | **6637 (0.0066 mm²)** |

With an analog layout factor of 3–4: about 0.02–0.027 mm² for the block (four comparators, both channels).

## Open issues

1. **Comparator offset under mismatch (failed, σ ≈ 1 LSB).** Options, in order of recommendation:
   (a) zero-current calibration by r1_ctrl: during the r1_isense AZ window (shunt current zero, Vod at the pedestal
   point), step the code of each comparator and find the toggle code; store the offset in LSB and correct the
   programmed code. No added analog area; residual ±0.5 LSB quantization plus gain error.
   (b) auto-zero of the comparator in the same AZ window (offset stored on capacitors, as in r1_isense).
   (c) `rppd` degeneration with larger area and a larger mirror (area estimate about +15 000 µm²).
   A decision is needed from r1_ctrl/system (calibration time, register for the offset).
2. **ss systematic error** of up to +10.3 mV (0.31 LSB) at the range ends. With mismatch it adds to issue 1.
3. **Simultaneous switching** of comparators that share string taps aborted the transient solver at
   development level (step size). It is not proved that this is only a solver issue. Reference decoupling
   capacitors (`CREF` in `gen_safe.py`) are prepared but not used.
4. **Blanking.** The outputs are not valid during r1_isense AZ and for about 200 ns after it. r1_ctrl must blank.
5. **Ideal sources.** VREF must be buffered and shared with the r1_isense pedestal arms; IBIAS (5 µA PTAT per
   comparator) comes from r1_bgr.
6. **Current.** About 0.4 mA from VDDA for four comparators (40 µA tail each). Revision 1 used 10 µA tails;
   the degeneration needs the higher current for speed (20 µA tails with a long mirror gave 400–820 ns NEG delay,
   `dev-dly-A`).

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| ngspice | ngspice-46 (OSDI PSP 103, `r3_cmc`) | `flow/run.sh ngspice -v` banner, 2026-10-20; `sim/.spiceinit` loads the OSDI models |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| xschem / KLayout / LibreLane / CACE | not used in this step | — |

## Files and reproduction

- `schematic/gen_safe.py` → `schematic/r1_safe.spice` (generated; sizes in the first line). `schematic/area.py`
  gives the device area (`python3 area.py r1_safe.spice r1_safe_an`).
- Decks: `sim/tb_safe_cmp.cir` (generated by `sim/gen_tb_safe_cmp.py`, parameters in `sim/tb_safe_cmp.json`),
  `sim/tb_safe_dcmc.cir`, `sim/tb_safe_mc.cir` (transient MC, not run on revision 2). Analyzers `sim/analyze_*.py`;
  runner `sim/run_deck.py`.
- Campaign: `sh designs/r1-joint/blocks/r1_safe/sim/campaign_20261020.sh` from the repository root (CPU set
  109–111). Raw waveforms: `$G1_RESULTS_ROOT/r1_safe/<run-id>/`.
- `sim/results/<run-id>/run.json` and `summary.json` per run. Runs named `dev-*` are development runs on other
  netlist states (the netlist hash is in `run.json`); they are a record, not evidence. A first transient MC
  (`safe-mc-20261020-r1`, revision 1, code 32 only) was stopped before it completed when revision 1 failed.
