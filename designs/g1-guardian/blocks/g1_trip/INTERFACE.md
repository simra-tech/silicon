# Analog / digital interface of the breaker path (G1_SENSE, G1_TRIP, G1_GATE, G1_OSC)

Written 2026-09-18 from the schematic-level designs in the four block directories; revised the same
evening for the G1_BGR result **VREF = 1.04 V (not 1.2 V), IPTAT = 4.13 µA PTAT, VREF unbuffered (≈ 88 kΩ)**.
Numbers marked *simulated* come from the decks in `../g1_*/sim/` (nominal `mos_tt`,
27 °C unless stated). Everything else is a design intent the digital macro must match.

## Domains

| Domain | Rail | Who lives there |
| --- | --- | --- |
| 3.3 V analog | `IOVDD`/`VSS` (spec pins 3, 2) | G1_SENSE (both OTAs, resistor network), the SR latch and level shifters of G1_GATE, G1_BGR |
| 1.2 V core | `VDD`/`VSS` | G1_TRIP (DAC switches, comparators), G1_OSC, G1_GATE inputs/outputs, digital macro, pad `c2p`/`p2c` |
| analog pads | `SENSE_P`, `SENSE_N`, `VREF`, `TRIP_SET` | pad ESD to `IOVDD`/`IOVSS`; no level shift |

All signals crossing between the analog blocks and the digital macro are **1.2 V** logic
(rail-to-rail CMOS, static unless stated). No 3.3 V signal reaches the digital macro.

## Signals

| Signal | Width | From → To | Domain | Function and timing |
| --- | :-: | --- | --- | --- |
| `osc_clk` | 1 | G1_OSC → digital | 1.2 V | ~10 MHz system clock, 50 % duty, ±20 % untrimmed (see `../g1_osc/README.md`; post-layout 9.0 MHz at the mid trim code, −10 %, trimmable to 10 MHz at every corner). The digital macro derives `cmp_clk` = `osc_clk`/2 and all timers from it. |
| `osc_en` | 1 | digital → G1_OSC | 1.2 V | 1 = run. Tie high at reset (the macro needs the clock); provided so the scrubber can stop the clock in test. |
| `osc_trim[3:0]` | 4 | digital → G1_OSC | 1.2 V | capacitor trim, code 8 = nominal, ~2.7 %/LSB, static register. |
| `cmp_clk` | 1 | digital → G1_TRIP | 1.2 V | 5 MHz nominal (`osc_clk`/2), 50 % duty. The soft comparator strobes on the **rising** edge, the hard comparator on the **falling** edge (internal inverter), so their kickback and supply transients do not coincide. Both comparators are dynamic: no clock = no decision, outputs hold. |
| `cmp_soft` | 1 | G1_TRIP → digital | 1.2 V | 1 while `ISENSE/2 > V_DAC(soft)`, i.e. shunt voltage above the soft threshold. Updated once per `cmp_clk` rising edge, valid **< 2 ns** after the edge (*simulated*: 0.45–0.70 ns decision at 1–200 mV overdrive, any common mode 0.5–1.0 V; *post-layout* 0.86 ns at 1 mV tt, 1.78 ns at 1 mV ss/1.08 V/−40 °C, `../g1_trip/README.md` "Post-layout") and held by an SR latch until the next rising edge. Sample it on the **falling** edge of `cmp_clk` (or one `osc_clk` later). |
| `cmp_hard` | 1 | G1_TRIP → digital | 1.2 V | same, strobed on the falling edge of `cmp_clk`; sample on the rising edge. Also feeds the G1_GATE fast path directly. |
| `dac_soft[7:0]`, `dac_hard[7:0]` | 8 + 8 | digital → G1_TRIP | 1.2 V | threshold codes, static registers. Threshold in shunt millivolts = `code × 0.1962 mV × (VREF/1.04 V)`; full scale (code 255) = 50.0 mV. The DAC string has 530 units of the buffered VREF and uses taps 255…510 (0.500–1.001 V at the comparator), so the comparator-side LSB is VREF/530 = 1.962 mV, **not** VREF/256; the shunt-referred LSB is that /10 (gain 20 × divider ½). After a code change allow ≥ 1 µs before trusting the comparator (*simulated* settling ≤ 0.25 µs to 1 LSB, `../g1_trip/sim/results_dac.txt`; *post-layout* 0.19 µs for 255 → 0). |
| `sense_ofs` (required) | 8 (signed) | digital register, internal | — | offset trim of the sense path: the macro adds this to both DAC codes before driving them (saturate at 0/255). LSB = 0.196 mV shunt-referred, range ±127 LSB = ±24.9 mV, sized from the G1_SENSE Monte Carlo (σ = 4.0 mV, see `../g1_sense/README.md`, "Trim"). No analog trim pins exist. |
| `trip_d` | 1 | digital → G1_GATE | 1.2 V | level; 1 sets the 3.3 V trip latch (asynchronous, ~ns). Hold ≥ 100 ns. Timer-based (soft) trips and blanked hard trips come this way. |
| `fast_en` | 1 | digital → G1_GATE | 1.2 V | 1 enables the analog fast path `cmp_hard` → latch, bypassing the blanking counter. Default 0 after reset. |
| `clr_d` | 1 | digital → G1_GATE | 1.2 V | 1 clears the trip latch (retrigger mode / register clear). Pulse ≥ 100 ns. Reset-dominant: while high the latch cannot set. |
| `en_core` | 1 | `EN` pad `p2c` → G1_GATE **and** digital | 1.2 V | pad-level-shifted `EN`. 0 clears the trip latch and forces `gate_core` = 0 regardless of everything else. |
| `gate_core` | 1 | G1_GATE → `GATE` pad `c2p` | 1.2 V | `en_core & !tripped`. Only G1_GATE drives the pad. |
| `fault_core` | 1 | G1_GATE → `FAULT_N` pad `c2p` | 1.2 V | `!tripped`. |
| `tripped` | 1 | G1_GATE → digital | 1.2 V | latch state, for the event counter, last-cause register and retrigger state machine. Asynchronous; synchronise in the macro. |
| `ISENSE` | analog | G1_SENSE → G1_TRIP | 3.3 V domain, 1.0–2.0 V | `VPED + 20 × (SENSE_P − SENSE_N)`, VPED = 51/53 × VREF = 1.0008 V; internal only. |
| `VREF` | analog | G1_BGR → G1_SENSE only | 3.3 V domain, 1.04 V nominal | drives one OTA gate (the VREF buffer in G1_SENSE); no resistive load, so the bandgap's 88 kΩ output impedance is acceptable. Any `VREF` pad leakage still moves it (BGR README). |
| `vref_buf` | analog | G1_SENSE → G1_TRIP | 3.3 V domain, 1.04 V | buffered copy of VREF (OTA follower, offset σ ≈ 3.8 mV = 0.37 % of scale, *simulated* MC of the same cell); loads: two DAC strings 2 × 20.5 µA + pedestal divider 2 µA. |
| `iptat` | analog | G1_BGR → G1_SENSE | current sink | 4.13 µA at 27 °C, PTAT (3.2 µA at −40 °C, 6.2 µA at 175 °C) into one `sg13_hv_nmos` 3.3 µm/1 µm diode; sets all OTA currents (≈ 350 µA per OTA at 27 °C, three OTAs, scaling with T). |

## Macro pins (layout, 2026-09-19)

The hardened macros carry the pin names below (`../g1_trip/layout/g1_trip.lef`, `../g1_osc/layout/g1_osc.lef`,
both with Metal3 `VSS` bar on the south edge and `VDD` bar on the north edge, signal pins as Metal3
stubs on the west/east edges):

| Macro | Schematic port | Macro pin | Edge |
| --- | --- | --- | --- |
| `g1_trip` (229 × 207 µm) | `isense`, `vref` | `ISENSE`, `VREF` | west |
| | `soft0..7`, `hard0..7` | `dac_soft[7:0]` (west), `dac_hard[7:0]` (east) | west / east |
| | `cmp_clk`, `cmp_soft`, `cmp_hard` | `clk`, `cmp_soft`, `cmp_hard` | east |
| | `vdd`, `vdda`, `vss` | `VDD` (north bar), `IOVDD` (bar inside the north edge), `VSS` (south bar) | — |
| `g1_osc` (166 × 137.6 µm) | `en`, `trim0..3` | `en`, `trim[3:0]` | west |
| | `osc_clk` | `osc_clk` | east |
| | `vdd`, `vss` | `VDD` (north bar), `VSS` (south bar) | — |

`g1_trip` has no `IOVSS` pin: its 3.3 V level shifters return to the same `vss`/substrate as the 1.2 V
circuits, as in the schematic. Both macros are filled (PDK filler, Activ/GatPoly/Metal1–5, no
TopMetal fill), carry a `prBoundary` on 189/4 (not 189/0, which the PDK density deck would take as
the chip area) and pass the PDK antenna deck (`g1_osc` got a `dpantenna` on its threshold node).
Their LEFs obstruct Metal4/Metal5 over the interior only — 3 µm inside the edges, below the `IOVDD`
bar zone in `g1_trip` — so the chip PDN can land its Metal5 straps on the bars (revised 2026-09-19
after the chip dry run); in `g1_trip` the two `vdd` Metal4 trunks cross the `IOVDD` bar at
x = 7 … 8 and 122 … 123 µm and are obstructed there. TopMetal1 is obstructed over the capacitors
only, TopMetal2 not at all.

## Timing assumptions the digital macro should encode

- Soft path: counter increments on `cmp_soft` samples at 5 MHz (200 ns per sample); a trip-off
  time of 1 ms is 5000 samples; ±20 % clock tolerance applies unless the host trims/calibrates.
- Hard path: `N` consecutive `cmp_hard` = 1 samples (`N` programmable, default 4 → 0.8 µs) then `trip_d`.
- Total hard-trip budget from overcurrent to `GATE` < 1 V into 5 nF (*simulated* in
  `../g1_gate/sim/results_gate.txt`): sense settling (~0.15 µs) + blanking (0.8 µs at N = 4)
  + latch and level shift + pad discharge (see G1_GATE README). Well inside the 10 µs target.
- Power-up: `en_core` = 0 until the host releases `EN`; `gate_core` = 0 while `en_core` = 0. The
  `GATE` pad itself is **not** defined while the 1.2 V core is absent: with `IOVDD` up and `VDD` down
  the `sg13g2_IOPadOut30mA` output was simulated **high** (3.3 V) even with a 10 kΩ external
  pull-down (`../g1_gate/sim/results_gate_pwr.txt`). Board requirement: `VDD` before or with `IOVDD`.
  With `VDD` up first, `GATE` stays low until `EN` is released.
- Reset values: `fast_en` = 0, `osc_en` = 1, `osc_trim` = 8, `dac_soft` = 153 (30.0 mV = 1.2 × 25 mV),
  `dac_hard` = 254 (49.8 mV), `sense_ofs` = 0.
- Absolute threshold accuracy: all thresholds scale with VREF (BGR README: 3σ ≈ ±5.5 % mismatch + ±1 %
  process, untrimmed) plus the vref_buf offset (0.4 %) plus the trimmed sense offset (≤ 0.1 mV) plus the
  comparator offset (see G1_TRIP README) — inside the ±10 % ECSS-style budget without a VREF trim.

## Spec inconsistency to resolve

`G1_TOP_LEVEL_SPECIFICATION.md` §4 gives the hard threshold as "1.5× to 8× nominal". With the
nominal current mapped to 25 mV of the 50 mV range (needed so the soft thresholds sit mid-range
for the comparator common mode), the hard threshold reaches at most 2× nominal. It is better
specified as a fraction of full scale: 0.3–1.0 FS (codes 77–255). The same table lists `ISENSE`
as 0–1 V; the implemented ISENSE is 1.0–2.0 V (pedestal 1.0 V, gain 20) and its halved copy
0.5–1.0 V is what the comparators see. The specification's "VREF nominal 1.2 V class" is 1.04 V in
this PDK (G1_BGR README); every ratio in the breaker path was re-derived from 1.04 V.
