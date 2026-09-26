# BGR586 extraction: AC loop, PSRR, noise and start-up, 2026-09-26

These checks were run on the capacitance extraction of the bandgap on the chip, `g1_bgr586_pex.spice`
(sha256 `01227a3d…`, kpex 2.5D CC, 978 capacitors, LVS clean; see `../README_bgr586_pex.md`). Each result
is compared with the schematic-level netlist 586, rerun here on the same decks and image. The Sep-19 bandgap
is also rerun where it is relevant. **All numbers are simulated.** No model card, rule deck, netlist or
layout was changed.

## Built against

| Item | Value | How established |
| --- | --- | --- |
| Image | `tapeoutbench-eda:latest` = `sha256:ddeb6957…` | `flow/run.sh` identity check |
| PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` COMMIT check |
| ngspice | 46 | log banner |
| Netlists | pex `01227a3d…`; sch 586 `586ffb58…` (329 Sep-19 caps); old Sep-19 `g1_bgr_pex.spice` `72417e07…` | `inputs.json` |

The recorded 2026-09-22 schematic values (`../../qualification/BGR586_REQUIRED_AC_PVT_20260922.md`) came
from image `5fd78498…`. The schematic controls rerun here reproduce them: noise 100.111 µV, PSRR
102.81/81.95 dB, PBIAS min |1+T| 0.6377/0.6341/0.8450. The Sep-19 PBIAS phase margin, 118.98° at 3.75 MHz,
matches `local_stability_summary.json`.

## Fixtures and commands

Each fixture was copied from an existing deck. Only the netlist, the corner and the supply were changed.

- **Tian**: `bgr_local_stability_20260921_01` / `run_586_required_ac.py`. Two-injection probe on the gate
  fanout of PBIAS (156 gate pins) or PCASC (77 gate pins). 1 pF VREF load, ideal 1 V IPTAT termination,
  `ac dec 100 1 1g`. PM = 180° + ∠T at the \|T\| = 1 down-crossing.
- **PSRR/noise**: `bgr_noise_20260921_01/noise.cir`. `ac dec 50 .1 100Meg` with 1 V AC on VDD, and
  `noise v(vref) Vdd` over 1 Hz–10 MHz and over 10 Hz–10 MHz (ngspice `onoise_total`). The trapezoid
  cross-check agrees to 0.02 %.
- **1 ms start-up**: `bgr_loop24q4_hv06_startup2_20260922_r3/typ_tt_typ_27_0.001.cir`. The PWL end value is
  3.3 V (the original is 3.0 V). 1 pF load, `tran 2u 3m uic`. The reference is `.op` at 3.3 V after the
  transient.
- **10 nF pad start-up**: `../../system_checks_20260924/bgr_sys.py` startup deck. Stock
  `sg13g2_IOPadAnalog`, 613 Ω route, 100 kΩ + 2 pF internal load, 10 nF + 1 Ω on the pin, 10 µs ramps,
  15 ms window. The pad-less stand-in (`nopad`) was run alongside.
- **Corners**: tt27 = typ/tt/typ 27 °C, ss125 = wcs/ss/wcs 125 °C, ff-40 = bcs/ff/bcs −40 °C, all at 3.3 V.
  The Tian runs also cover the two historical tuples: slow = wcs/ss/wcs 3.0 V −40 °C, fast = bcs/ff/bcs
  3.6 V 125 °C.

```sh
cd designs/g1-guardian/blocks/g1_bgr/sim/postlayout/bgr586_ac_20260926
python3 run_ac.py gen
BULK=${BULK} python3 run_ac.py run 116-123   # each deck: flow/launch_pinned.sh <cpu> ... ngspice -b <deck>, 1 CPU
python3 run_ac.py analyze                                # -> summary.json
```

Decks are in `decks/` and logs in `logs/` (`orchestrator.log` records nice = 0). Waveforms and
return-ratio JSON are in `${BULK}/bgr586_ac_20260926/`.

## 1. Loop gain, Tian probe (conditional local loops; other loops stay closed)

| corner | cut | PEX: PM @ f<sub>u</sub>; min \|1+T\|; GM | schematic 586 | Sep-19 bandgap |
| --- | --- | --- | --- | --- |
| tt27 | PBIAS | 107.5° @ 8.26 MHz; 0.728; 16.9 dB @ 48 MHz | 109.2° @ 10.4 MHz; 0.638; 11.0 dB | 119.0° @ 3.75 MHz; 0.839 |
| ss125 | PBIAS | 109.5° @ 6.56 MHz; 0.814; no −180° crossing | 111.7° @ 7.96 MHz; 0.769 | 118.4° @ 3.31 MHz; 0.886 |
| ff-40 | PBIAS | 108.5° @ 8.83 MHz; 0.721; 15.7 dB @ 50 MHz | 110.7° @ 10.9 MHz; 0.632; 10.6 dB | 119.4° @ 3.95 MHz; 0.834 |
| slow (3.0 V −40 °C) | PBIAS | 107.4° @ 7.76 MHz; 0.729; 17.1 dB | 107.8° @ 10.1 MHz; 0.634 (recorded 0.634123) | not run |
| fast (3.6 V 125 °C) | PBIAS | 111.8° @ 6.59 MHz; 0.880 | 114.1° @ 7.80 MHz; 0.845 (recorded 0.845034) | not run |
| tt27 / ss125 / ff-40 | PCASC | no unity crossing; max \|T\| 0.485 / 0.335 / 0.504; min \|1+T\| 0.774 / 0.840 / 0.768 | max \|T\| 0.743 / 0.500 / 0.758; 0.714 / 0.819 / 0.707 | 0.480 / 0.380 / 0.490; 0.851 / 0.885 / 0.849 |
| slow / fast | PCASC | no unity crossing; min \|1+T\| 0.781 / 0.907 | 0.718 / 0.910 (recorded 0.718208 / 0.909681) | not run |

- **DC loop gain.** The PBIAS DC loop gain is identical on all three netlists (618 / 636 / 564).
- **Probe does not move the operating point.** The operating point under the probe equals the unmodified
  `.op` (V<sub>REF</sub> 1.04546022 / 1.04855716 / 1.04216545 V).
- **Effect of the extraction.** It lowers f<sub>u</sub> by 16–23 % and PM by 0.4–2.3°. It raises the
  minimum \|1+T\| and the gain margin.
- **PEX PCASC ss125.** The first attempt **failed**: `.op` stuck in dynamic gmin stepping. The deck was
  killed at its 900 s wall bound, and the container ngspice was SIGKILLed by hand at 1247 s. The retry
  (`*_ns`) adds `.nodeset` for all 1053 nodes from `opdump_pex_ss125` (the unmodified PEX `.op`, same
  corner). It converged to the same V<sub>REF</sub>. The number above comes from the retry.
- **Acceptance.** No BGR phase-margin target is recorded. The ≥ 60° criterion belongs to SENSE. Every PBIAS
  PM is ≥ 107°. This is **not** global stability. The pole-zero analysis remains **not run** (failed pilot
  `bgr_pole_pilot_20260921_01`).

## 2. PSRR (rejection = −20 log\|V<sub>REF</sub>/V<sub>DDA</sub>\|, dB) and output noise

| netlist / corner | 10 Hz | 1 kHz | 100 kHz | 1 MHz | 10 MHz | 100 MHz | min 10 Hz–100 MHz | noise 10 Hz–10 MHz (1 Hz–10 MHz), µV RMS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PEX tt27 | 102.57 | 75.27 | 35.29 | 16.24 | 15.06 | 28.78 | 11.43 @ 3.47 MHz | 92.89 (93.35) |
| PEX ss125 | 99.73 | 73.98 | 34.00 | 15.19 | 15.59 | 28.51 | 11.20 @ 3.02 MHz | 111.23 (111.91) |
| PEX ff-40 | 104.62 | 76.53 | 36.54 | 17.34 | 14.72 | 28.65 | 11.81 @ 3.80 MHz | 78.03 (78.35) |
| sch 586 tt27 | 102.76 | 81.95 | 42.00 | 22.66 | 19.17 | 51.80 | 16.47 @ 4.17 MHz | 99.68 (100.11) |
| sch 586 ss125 | 99.87 | 80.63 | 40.69 | 21.52 | 19.70 | 51.04 | 16.21 @ 3.63 MHz | 119.92 (120.55) |
| sch 586 ff-40 | 104.84 | 83.22 | 43.26 | 23.82 | 18.96 | 50.27 | 16.92 @ 4.57 MHz | 83.30 (83.60) |
| Sep-19 tt27 | 102.72 | 75.35 | 35.40 | 18.46 | 27.75 | 66.26 | 17.67 @ 1.58 MHz | 193.96 (196.05) |
| Sep-19 ss125 / ff-40 | 99.88 / 104.76 | 74.06 / 76.59 | 34.12 / 36.63 | 17.88 / 19.21 | 28.60 / 27.16 | 58.95 / 72.38 | 17.46 / 18.01 | 229.80 / 164.90 |

- **PSRR, PEX against schematic.** The extraction equals the schematic at DC. From 1 kHz to 1 MHz it is
  6.4–6.7 dB worse, and at 3–4 MHz the minimum rejection is 5 dB lower. This is the same +7 dB seen when
  the Sep-19 bandgap was extracted. The Sep-19 variants traced it to 2.5D capacitance over n-wells being
  referenced to vss (no well conductor), so above DC the PEX PSRR is a pessimistic bound (`../../README.md`).
- **Noise.** The extraction is 7 % below the schematic. The spectral density is identical below 100 kHz:
  1.76 µV/√Hz at 10 Hz and 132 nV/√Hz at 1 kHz (tt27). BGR586 has about half the noise of the Sep-19
  bandgap.
- **Acceptance.** No PSRR or noise budget is adopted for the BGR, so there is no pass/fail.

## 3. Start-up

**1 ms supply ramp, 0 → 3.3 V, 1 pF VREF load, 3 ms window**

| netlist / corner | V<sub>REF</sub> = 0.93 V | 1 % (0.1 %) settling | overshoot | V<sub>REF</sub> at 3 ms (DC) | I<sub>PTAT</sub> at 3 ms |
| --- | --- | --- | --- | --- | --- |
| PEX tt27 | 0.472 ms | 0.503 (0.530) ms | 0.13 mV | 1.045460 V (1.045460) | 4.134 µA |
| PEX ss125 | 0.489 ms | 0.585 (0.619) ms | 0.12 mV | 1.048557 V (1.048557) | 4.802 µA |
| PEX ff-40 | 0.474 ms | 0.502 (0.508) ms | 3.04 mV | 1.042165 V (1.042165) | 3.670 µA |
| sch 586 tt27 / ss125 / ff-40 | 0.470 / 0.489 / 0.474 ms | 0.504 / 0.585 / 0.503 ms | 0.07 / 0.06 / 2.80 mV | same as PEX to 1 µV | same |

- The Sep-19 extraction took 0.519 ms to reach 0.93 V. That ramp was 0 → 3.0 V, so the times are not
  directly comparable.
- None of the six runs rings. The waveforms are finite, and every run completed with trap.

**10 nF pad fixture** (time from the ramp start to within 1 % (0.1 %) of the DC value):

| corner | PEX, stock pad | PEX, pad-less stand-in | schematic 586 (recorded 2026-09-24) |
| --- | --- | --- | --- |
| tt27 | 1.256 (1.798) ms | 1.241 (1.770) ms | pad 1.26 (1.80), stand-in 1.24 (1.77) ms |
| ss125 | **not converged**: trap "timestep too small" at 52.46 µs on `vr4#branch`; gear at 52.46 µs on `vload#branch` | 1.324 (1.933) ms, see note | pad not converged (52.6 µs); stand-in 1.32 (1.93) ms |
| ff-40 | 1.201 (1.672) ms | 1.188 (1.648) ms | pad 1.20 (1.67), stand-in 1.19 (1.65) ms |

- **No ringing or overshoot.** The overshoot is ≤ 2 nV, and the peak-to-peak over the last 20 % of the
  window is ≤ 0.2 nV.
- **Stock-pad ss125 stall.** It stalls at the same point as on the schematic. This is the known VREF-pad
  secondary-protection diode stall; the attribution was carried over from Sep-19 and is not re-split here.
- **ss125 stand-in, first attempt.** The `.op` did not converge: it sat in dynamic gmin stepping for 9 min
  and was stopped by hand. Log: `logs/pad10n_nopad_pex_ss125.first_attempt_op_stall.log`.
- **ss125 stand-in with `.nodeset`.** The `.op` then converged to V<sub>REF</sub> 1.048557161 V. The `uic`
  transient aborted at 1 ns with trap and with gear, on HBT `XQ1027` (diode-connected, net `n_17`).
- **ss125 stand-in result.** The number in the table comes from the `_noop` deck: the same deck with no
  `.op` and no nodeset, taking its settling reference from the converged nodeset `.op`.
- **Self-heating NaN.** Nearly every log prints the PDK's "temperature limiting function received NaN" once,
  during initialisation. All saved vectors are finite.

## Status

| Check (extraction, 3.3 V) | Criterion | Status |
| --- | --- | --- |
| Tian PBIAS/PCASC, tt27 / ss125 / ff-40 (+ slow/fast tuples) | PM ≥ 60°: not a recorded BGR target | completed 10/10 cuts (PCASC ss125 on the nodeset retry; first attempt **failed**); PBIAS PM 107.4–111.8°; not applicable as acceptance |
| Global stability / pole-zero | — | **not run** |
| PSRR 10 Hz–100 MHz, 3 corners | no budget adopted | completed; not applicable (above DC it is a pessimistic bound) |
| Output noise 10 Hz–10 MHz, 3 corners | no budget adopted | completed; not applicable |
| 1 ms start-up, 1 pF, 3 corners | qualification screen: V<sub>REF</sub> 0.9–1.2 V, I<sub>PTAT</sub> > 1 µA at the end | **passed** 3/3 |
| 10 nF start-up, stock pad, tt27 / ff-40 | spec P4: EN held low ≥ 2 ms (1 % settling < 2 ms) | **passed** (1.256 / 1.201 ms) |
| 10 nF start-up, stock pad, ss125 | same | **failed to converge** (numerical, pad diodes; same as schematic) |
| 10 nF start-up, pad-less stand-in, 3 corners | same | **passed** (1.24 / 1.32 / 1.19 ms); substitutes, not the chip; ss125 via `_noop` |
| Wiring resistance (RC extraction), mismatch, 3.0/3.6 V on PSRR/noise/start-up, real downstream loads | — | **not run** |

## Tool notes

- `flow/launch_pinned.sh` runs under `set -e`. A nonzero exit therefore ends its subshell before `<log>.rc`
  is written, and three `.rc` files were written by hand; each says so. `run_ac.py` now detects this case.
- The timeout kills the `podman run` client but not the containerised ngspice. The two PCASC runs outlived
  their 900 s bound and were killed by hand.
