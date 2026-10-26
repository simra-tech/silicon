# r1_bias — bias distribution and power-on reset (R1, track T9)

State (2026-10-26): **revision 2** (decision D20, VREF buffer `r1_vbuf`). Schematic simulated, layout done (DRC 0,
antenna 0, LVS match, 0.02841 mm²), PEX and post-layout buffer checks at tt and ffx. The layout does **not** fit
the try-e slot (see "Revision 2"). All numbers are simulated (ngspice 46). Nothing is measured. The sections after
"Revision 2" describe revision 1d; the legs, the POR and their results are unchanged in revision 2.

## Revision 2 (VREF buffer)

Revision 2 = revision 1d + `r1_vbuf`, a unit-gain buffer of the raw bandgap `vref`. New pins: `vref` (input, gate
only) and `vref_b` (output). The buffer bias comes from one more `r1_bias_leg` unit (`ibvb`, 5.07 µA at tt) of the
same mirror array. The 11 outputs, the POR and their devices are unchanged. Revision 1d is kept as
`schematic/r1_bias_rev1d.spice` (sha256 `3fa56d92…`).

### Circuit and sizes

Netlist of record: `schematic/r1_bias.spice`, sha256 `5511ea8db822408d882fad324b1f694f82b0e4448b7e6f81a6319fd14957dfeb`.
All devices are thick-oxide (`sg13_hv_*`). Units are single-finger devices (`m` = number of units).

| Device | Function | Size | Current tt |
| --- | --- | --- | --- |
| `XM1`, `XM2` | NMOS input pair. `XM1` gate = `vref` (diode side), `XM2` gate = `vref_b` (feedback) | 8/24 µm, m = 4 each, common centroid ABBA/BAAB | 0.98 µA each |
| `XM3`, `XM4` | PMOS mirror load; `XM4` drain = high-impedance node `x1` | 5/20 µm | 0.98 µA |
| `XMT` | tail | 5/2 µm, m = 2 | 1.95 µA |
| `XMB` | bias diode, fed by the leg `ibvb` | 5/2 µm, m = 5 | 5.07 µA |
| `XM7` | NMOS source follower, drain on `vdda`, source `vref_b` | 10/1 µm, m = 4 | 31.6 µA |
| `XM8` | sink | 10/2 µm, m = 4 | 8.4 µA |
| `XCC1`, `XCC2` | compensation, `x1` to `vss` (dominant pole) | 2 MIM plates 48.3 × 48.3 µm (≈ 7 pF) | — |

Why a source follower: the first revision-2 buffer (PMOS common-source output, Miller capacitor and nulling
resistor) failed the supply step (`vref_b` moved 22–24 %, failure 24). With the Miller capacitor, `x1` follows
`vref_b` at high frequency, so a `vdda` step changes V<sub>SG</sub> of the output device directly. In the
follower, the output device has its drain on `vdda`, and `x1` is held to `vss` by the capacitor.

### Load budget (`vref_b`)

The loads in every deck are the consumer netlists of record: `r1_safe_string` (copied unchanged from
`r1_safe.spice`, sha256 `812f886d…`) and the two `r1_isense` pedestal arms (26 `rppd` units and the switch, copied
from `r1_isense.spice`, sha256 `af013b95…`), in `sim/r1_vrefb_loads.spice` (written by `sim/make_vrefb_loads.py`).
The `r1_t2f` `vref` pin is on `vref_b`, because it draws current (5.7–74 nA). Capacitance: 25 pF (20 pF consumer
decoupling + 5 pF routing), with 2 pF and 50 pF as checks. Run `bias-op-20261026-r2e` (13 cases).

| Load | tt (µA) | Range over 13 cases (µA) |
| --- | --- | --- |
| `r1_safe` threshold string | 4.03 | 3.57–4.54 |
| `r1_isense` pedestal arm A | 9.61 | 8.48–10.89 |
| `r1_isense` pedestal arm B | 9.61 | 8.48–10.89 |
| `r1_t2f` `vref` pin | 0.022 | 0.006–0.074 |
| Total | 23.3 | 20.6–26.3 |
| Total + 50 % margin | 35.0 | 39.5 (worst) |
| Drive checked (`vb-drive-20261026-r2c`) | 50 µA total: `vref_b` moves ≤ 0.04 mV | 1 mV drop only above 100 µA total |

### Status (revision 2)

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| Load on the raw `vref` | ≤ 10 nA | **passed**: < 1 fA (gate input; the model has no gate leakage) | `sim/results/bias-op-20261026-r2e.json` |
| Offset, 13 cases (7 corners, tt −40/125 °C, `res_bcs/wcs`, 3.0/3.6 V) | ≤ 2 mV | **passed**: −0.16 … +0.21 mV (systematic) | same |
| Offset, mismatch MC, 200 samples, tt | ≤ 2 mV at 3σ | **passed**: mean 0.05 mV, σ 0.44 mV, \|mean\| + 3σ = 1.37 mV. Worst corner systematic + 3σ = 1.54 mV (estimate; MC at the corners **not run**) | `bias-mc-20261026-r2c` |
| Loop gain, 7 corners × pedestals on / off, 25 pF | PM ≥ 65°, GM ≥ 10 dB | **passed** 14/14: PM 67.6° (ffx, off) … 76.7°, GM ≥ 20.1 dB, f<sub>u</sub> 153–250 kHz | `vb-stb-20261026-r2c` |
| Loop gain at the bias extremes 3.5 / 7.7 µA (tt, 25 pF) | same | **passed**: PM 75.6 / 71.8° and 73.2 / 69.8° (on / off), GM ≥ 20.9 dB | same |
| Loop gain with 2 pF and 50 pF (tt, ff, ffx, ssx) | record | **run**: 2 pF PM ≥ 75.6°; 50 pF PM ≥ 67.5°, GM ≥ 20.3 dB | same |
| Method check (toy loop) | error < 1e-6 | **passed**: 4.7e-8 | same |
| Output impedance at DC | ≤ 1 kΩ | **passed**: 0.78–2.79 Ω (5 corners, pedestals on / off) | `vb-zout-20261026-r2c` |
| Output impedance to 10 MHz | record | **run**: peak 1.96–4.80 kΩ at 0.63–0.79 MHz; tables `sim/results/vb-zout-20261026-r2c_zbuf_<corner>_<state>.csv` | same |
| Supply step 3.3 → 3.0 → 3.3 V in 100 ns (tt, ss, ff, ssx, ffx) | `vref_b` within 1 %, one overshoot | **passed**: ≤ 0.27 % (2.77–2.84 mV; raw `vref` 2.5–2.6 mV, buffer 1.0–1.4 mV); one excursion per edge; settled to 1 mV in 3.0–4.0 µs | `vb-step-20261026-r2c` |
| PSRR of `vref_b` | record | **run**: 10 Hz −64…−67 dB; worst −37.0…−37.4 dB (near 100 kHz); raw `vref` worst −38.5…−38.9 dB | `vb-psrr-20261026-r2c` |
| Pedestal switching (`azb` of one or both arms, 1 ns edges) | record | **run**: one arm (8.6–10.9 µA step) 17–22 mV; both arms 41–50 mV; back within 0.5 mV 1.6–3.5 µs after the closing edge; after the opening edge 1.5 µs (ff, ffx) or not within the 2 µs pulse (tt, ss, ssx) (open issue R2-2) | `vb-az-20261026-r2c` |
| Start-up, 10 µs VDDA ramp, POR, tt/ss/ff/ssx/ffx | settles, no step at the `por_n` edge | **passed**: `vref_b` within 1 % at 12.2–25.4 µs, overshoot ≤ 0.23 %, no step at `por_n` (< 0.05 mV) | `bias-startup-20261026-r2c` |
| Noise 10 Hz–100 kHz (tt, ss, ff) | record against the raw `vref` | **run**: `vref_b` 45.9–72.5 µV rms, raw `vref` 43.4–69.8 µV rms; the buffer adds 15–20 µV rms | `vb-noise-20261026-r2c` |
| The 11 output currents against 1d | unchanged | **passed**: tt 10.1419 / 5.0710 µA; all 11 outputs in all 13 cases equal to `bias-op-20261021-d` (difference 0 at the printed precision) | `bias-op-20261026-r2e` |
| `r1_bgr` loop gain with the buffer input attached, 5 cuts × 7 corners | PM ≥ 60°, GM ≥ 10 dB | **passed** 35/35: core PM 100.9–101.1° (1d: 101.3–101.5°), GM ≥ 12.95 dB | `bias-stb-20261026-r2c` |
| Output PSRR (`ib_afe_s1`, tt/ss/ff) | record | **run**: tt −44.75 dB at 20 kHz, −22.44 dB at 1 MHz (inside the 1d range) | `bias-psrr-20261026-r2c` |
| Output mismatch MC, 200 samples | record | **run**: σ 1.15 % (10 µA) and 1.10 % (5 µA) | `bias-mc-20261026-r2c` |
| Supply current, whole r1_bias | ≤ 150 µA (revision-1 budget) | **failed**: 98.0–195.7 µA; tt 135.5, ss 150.6, tt 125 °C 171.1, `res_bcs` 155.1, ffx 195.7 µA. Buffer 31.6–49.0 µA, of which 20.6–26.3 µA is the load (open issue R2-1) | `bias-op-20261026-r2e` |
| Layout: DRC main + maximal, antenna, LVS, pins | 0, 0, match, all ports | **passed**: DRC 0, antenna 0, LVS match (84 nets), pin check 19/19 | `layout/runs/layout-*-20261026-r2c` |
| Layout box against the try-e slot | ≤ 120 × 174.4 µm (ctrl at chip y 673.0, 10 µm keep-out) | **failed**: 120.0 × 236.74 µm (+62.3 µm in height) (open issue R2-3) | same |
| PEX | full RC netlist | **run**: 196 devices, 144 nets, 1162 R, 1162 C (1573.1 fF) | `layout/runs/pex-rc-20261026-r2d` |
| Post-layout loop gain tt, ffx | PM ≥ 65°, GM ≥ 10 dB | **passed**: tt 73.8 / 70.1°, ffx 70.9 / 66.9° (on / off), GM ≥ 21.0 dB | `sim/runs/post-vbstb-20261026-r2e` |
| Post-layout offset, Zout, supply step at tt | as above | **passed**: offset 0.039 mV; Z at DC 1.04 / 1.89 Ω; step 0.70 % (see pre/post) | `post-op-20261026-r2e`, `post-vbzout-20261026-r2e`, `post-vbstep-20261026-r2e` |
| Post-layout op at ss | — | **not run**: no operating point (`r1_bgr` HBT, also with `conv=1` and `conv=2`) | `post-op-20261026-r2e`, `-r2e1` |
| Post-layout MC, PSRR, noise, pedestal switching, start-up; buffer at sf/fs | — | **not run** | — |
| `r1_safe`, `r1_isense` decks with this `vref_b` source | — | **not run** (owners' tracks) | — |

### Area and floorplan

| Item | Value |
| --- | --- |
| Box | 120.0 × 236.74 µm = **0.02841 mm²** (1d: 120.0 × 165.94 µm = 0.01991 mm²; +70.8 µm in height) |
| Buffer band | between the POR ring and the cascode rows: NMOS row (bias, tail, sink, follower), two pair rows, PMOS mirror row, own p+ ring, a p+ tie across the pair rows (LU.b); the two MIM plates lie over the band |
| Drawn device area (`schematic/area.py`) | `r1_vbuf` 6 592 µm² (MIM 4 666, MOS 1 926); r1_bias 11 704 µm² |
| Try-e slot (`r1_top/reports/integration_checklist_e.md`) | origin chip (444.0, 488.6); `r1_ctrl` box starts at chip y 673.0, so the height limit is about 174.4 µm with a 10 µm keep-out. The new top edge is at chip y 725.3 and overlaps `r1_ctrl` in x 543.8–564.0 |
| Pins kept | `por_n` (east, y 38.38), `vdd` (east, y 48.74), `vss` bar (y 0–2), `ib_afe_s1` 42.39, `ib_afe_s2` 69.19, `ib_afe_c2` 82.59 |
| Pins moved | north edge to y 236.14; `vdda` bar to y 233.14–235.14; `pbias` west y 212.99 (was 142.19), `pcasc` west y 191.94 (was 121.14); `ib_is_a` 26.49, `ib_sf_oa` 34.49, `ib_sf_na` 43.34, `ib_adc_ref` 50.49, `ib_afe_c1` 55.79, `ib_sf_ob` 66.49, `ib_sf_nb` 74.49, `ib_is_b` 81.69 (the mirror row has one more unit, `ibvb`) |
| Pins new | `vref` west y 116.44; `vref_b` east y 147.14 |

GDS of record: `layout/r1_bias.gds`, 1 104 848 bytes, sha256 `e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c`;
LVS netlist `layout/r1_bias_lvs.cdl` sha256 `abb7bc28…`. Layout runs `layout-{gen,drc,ant,lvs}-20261026-r2c`; PEX
`pex-rc-20261026-r2d` (`pex-rc-20261026-r2c` lacked the `vref`/`vref_b` ports, failure 29).

### Pre/post (revision 2, schematic → full RC, simulated)

| Item | Corner | Schematic (`bias-op-20261026-r2e`, `vb-*-20261026-r2c`) | Post-layout (`post-*-20261026-r2e`) | 1d post-layout |
| --- | --- | --- | --- | --- |
| 10 µA outputs (µA) | tt | 10.1419 | 10.1312–10.1329 (−0.09…−0.11 %) | 10.1332–10.1339 |
| 5 µA outputs (µA) | tt | 5.0710 | 5.0646–5.0666 (−0.09…−0.13 %) | 5.0664–5.0670 |
| 10 / 5 µA outputs (µA) | ssx | 6.9382 / 3.4691 | 6.9318–6.9330 / 3.4652–3.4667 | not run |
| 10 / 5 µA outputs (µA) | ffx | 15.3552 / 7.6776 | 15.3375–15.3399 / 7.6673–7.6702 | not run |
| 10 / 5 µA outputs | ss | 11.8062 / 5.9031 | **not run** (no operating point) | 11.796 / 5.898 |
| 10 / 5 µA outputs | ff | 8.9996 / 4.4998 | op spread −1.1…0 %: the known op artifact of the RC netlist (failure 22); transient **not run** | 8.9915 / 4.4960 (transient) |
| Offset `vref_b` − `vref` (mV) | tt / ssx / ffx | 0.040 / 0.137 / −0.105 | 0.039 / 0.137 / −0.107 | — |
| PM pedestals on / off (°) | tt | 74.43 / 70.75 | 73.75 / 70.07 | — |
| PM pedestals on / off (°) | ffx | 71.66 / 67.61 | 70.94 / 66.88 | — |
| GM on / off (dB) | tt / ffx | 24.45 / 21.53, 23.17 / 20.38 | 25.26 / 22.14, 23.96 / 21.00 | — |
| Z<sub>out</sub> at DC on / off (Ω) | tt | 1.006 / 1.851 | 1.042 / 1.893 | — |
| Z<sub>out</sub> peak on / off | tt | 2.27 / 4.17 kΩ at 0.71 MHz | 2.33 / 4.26 kΩ at 0.63 MHz | — |
| Supply step, `vref_b` deviation | tt | 2.80 mV (0.27 %); raw `vref` 2.59 mV | 7.27 mV (0.70 %); raw `vref` 7.22 mV; buffer part 2.37 mV | — |
| VDDA current, whole block (µA) | tt | 135.5 (buffer 38.7) | 135.2 (buffer 38.6) | 96.7 (1d) |

Note: post-layout, the raw `vref` moves more on the supply step (7.2 against 2.6 mV). The extracted `vref` net has
15.2 fF to `xvb.d1` (the mirror diode, which follows `vdda`) and 7.8 fF to `vdda`. The cause is not isolated
(**not run**: a deck with only these capacitors).

### Open issues (revision 2)

1. **R2-1 Supply budget.** The block draws up to 195.7 µA (ffx) against the revision-1 limit of 150 µA. The buffer
   load (20.6–26.3 µA) is new current that the safe string and the pedestals need from any source; the buffer
   overhead is 11–23 µA. The coordinator must set a new budget, or the sink (`XM8`, 8 µA) and the follower bias
   must be reduced (not run).
2. **R2-2 Pedestal switching.** A pedestal edge moves `vref_b` by 17–22 mV (one arm) or 41–50 mV (both) for
   1.5–3.5 µs. `r1_isense` and `r1_safe` must confirm that their samples are outside this window (the safe
   threshold step is 4.17 mV). Options: break-before-make with a dummy load, slower `azb` edges, or more capacitance
   at `vref_b` (PM at 50 pF is still ≥ 67.5°).
3. **R2-3 Slot.** The box is 62.3 µm higher than the try-e slot and overlaps `r1_ctrl`. T10/T8 must move the block
   (or `r1_ctrl`), or the buffer must become a separate macro (its band is 70.8 µm high; the MIM plates need about
   100 × 50 µm).
4. **R2-4 Raw `vref` coupling.** See the pre/post note. The ADC uses the raw `vref`.
5. Not run: post-layout MC, PSRR, noise, pedestal switching, start-up; offset MC at the corners; consumer decks with
   this source.

### Failures (revision 2)

| # | What | Class | Consequence / fix | Evidence |
| --- | --- | --- | --- | --- |
| 24 | First revision-2 buffer (PMOS common-source output, Miller C<sub>c</sub> + R<sub>z</sub>) passed the loop, offset and Z<sub>out</sub> checks but failed the supply step: `vref_b` moved 226–256 mV (22–24 %); PSRR about 0 dB near 1 MHz. The prototype sweeps checked only loop gain and offset | functional-bug | Output stage changed to an NMOS source follower with C<sub>c</sub> to `vss`; step now 0.27 %. Campaign r2b superseded | `sim/runs/vb-step-20261026-r2b`, `vb-psrr-20261026-r2b` |
| 25 | `vb-step` and `vb-psrr` exited 0 although the step criterion failed: the runner counted only failed jobs | verification-gap | `run_vbuf.py` now counts every `pass_*` flag that is false and exits 1 (`spec_failures` in the summary) | `sim/runs/vb-step-20261026-r2b` |
| 26 | Campaign r2 started with multi-finger devices; the netlist changed to single-finger units for the layout while the decks read the live netlist | process-hygiene | Run stopped (`podman stop`) and recorded abandoned; campaign restarted as r2b | `sim/runs/vb-stb-20261026-r2` |
| 27 | The SG13G2 PCell limits L to 10 µm ("using maximum length"); the 24 µm and 20 µm devices came out short | tooling | `mos_long()` draws the PCell and extends the gate | `layout/runs/layout-gen-20261026-r2a` |
| 28 | DRC r2a: 8 × LU.b on the inner input-pair units (N+ more than 20 µm from a p-tap) | verification-gap | p+ tie strip across the band in channel V2c; r2b and r2c clean | `layout/runs/layout-drc-20261026-r2a` |
| 29 | `pex_build.py` kept the 1d port list; `pex-rc-20261026-r2c` had no `vref`/`vref_b` ports | process-hygiene | Ports added; PEX re-run as `pex-rc-20261026-r2d` | `layout/runs/pex-rc-20261026-r2c` |
| 30 | `bias-op-20261026-r2c`: the op print list kept the removed node `xvb.cz`, so ngspice printed no line and 13/13 rows failed | process-hygiene | Node removed; re-run as `bias-op-20261026-r2e` | `sim/runs/bias-op-20261026-r2c` |
| 31 | Noise deck r2b: no AC value on `vdda` and no convergence | tooling | Deck fixed; r2c passed | `sim/runs/vb-noise-20261026-r2b` |
| 32 | MC r2b seed 198 and post-layout ss op: no operating point (`r1_bgr` HBT) | numerical | MC r2c 200/200; post-layout ss **not run** (also with `conv=2`) | `bias-mc-20261026-r2b`, `post-op-20261026-r2e1` |
| 33 | The supply current exceeds the 150 µA budget; the D20 brief gave the load but no current budget for the buffer | estimation | Open issue R2-1 | `bias-op-20261026-r2e` |
| 34 | The block height (236.74 µm) does not fit the try-e slot (174.4 µm) | estimation | Open issue R2-3 | `layout/runs/layout-gen-20261026-r2c` |

### Commands (revision 2, from the repository root, POSIX shell)

1. `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT`.
2. Schematic campaign: `sh designs/r1-joint/blocks/r1_bias/sim/chain_r2.sh <tag>` (suites `vbstb op vbzout vbstep vbaz vbpsrr vbnoise vbdrive mc startup stb psrr`).
3. Layout: `sh designs/r1-joint/blocks/r1_bias/layout/run_checks.sh 20261026-r2c`, then `sh designs/r1-joint/blocks/r1_bias/layout/run_pex.sh 20261026-r2c 20261026-r2d`.
4. Op re-run and post-layout: `sh designs/r1-joint/blocks/r1_bias/sim/chain_r2_post.sh 20261026-r2e pex-rc-20261026-r2d`.
5. One suite: `sh designs/r1-joint/blocks/r1_bias/sim/run_vb.sh <suite> <run-id> [cases=… pex=<run-id> view=rc conv=1]`.

## What it is

1. **Bias distribution.** One cascoded PMOS leg per consumer bias pin, driven from the `r1_bgr` rails `pbias` and
   `pcasc`. The unit leg is 12/4 µm (mirror) + 12/4 µm (cascode). The `r1_bgr` unit leg is 10/4 µm at 4.23 µA, so
   one unit gives 5.07 µA at tt/27 °C. A 10 µA output uses two units. Every consumer pin is an NMOS diode, so every
   output **sources** current into the consumer. No NMOS re-mirror is necessary. The currents are PTAT
   (ΔV<sub>BE</sub>/R of `r1_bgr`); they follow temperature and the `rppd` corner (table below).
2. **Power-on reset `r1_por`.** `por_n` (1.2 V domain) is low until VDDA and VDD are both above their thresholds and
   then for a delay. Thresholds (assumptions of this track, from the brief): VDDA 2.70 V rising, 2.60 V falling;
   VDD 1.00 V rising, 0.95 V falling. Delay target ≥ 100 µs.
   - Reference: a replica of the `r1_bgr` output leg (one 10/4 leg on `pbias`/`pcasc`, `rppd` 45.9 + 260.3 µm,
     4 × `npn13G2`). It gives `vrh` = 1.000 V and the tap `vrl` = 0.950 V (tt). It does **not** load the
     `r1_bgr` `vref` node.
   - VDDA comparator: `rhigh` divider (27 units of 0.5 × 27 µm, about 2 MΩ, 1.65 µA). A switch shorts 1 unit
     while VDDA is good, so the falling threshold is 2.60 V.
   - VDD comparator: VDD is compared directly with `vrh` (VDD bad) or `vrl` (VDD good). There is no divider and no
     DC load on VDD.
   - Comparators: open-loop, two stages, PMOS input pair, tail and load from a local rail `pl`. `pl` is one
     cascoded `r1_bgr` leg into an NMOS mirror into a PMOS diode, decoupled to VDDA. So comparator edges do not
     reach `pbias` (revision 1b).
   - 0.5 pF MIM filters on `vrh`, `vrl`, `tapa` (revision 1c).
   - Delay: a stack of 20 PMOS (0.5/4 µm) on `pl` charges a 1.5 pF MIM (32 × 32 µm). The MIM is discharged at once
     when either supply is bad. Then a Schmitt trigger.
   - Output (revision 1d): thick NMOS pass from VDD, gated by `ready` (VDDA level), an `rhigh` pull-down (about
     2 MΩ) on `por_raw`, then two thin inverters. `por_raw` is defined low whenever VDDA is absent.
   - G1 has no POR cell (`por_n` was a tie-high cell in G1 r4, `g1-guardian` red-team F3), so `r1_por` is new.
3. **Loads in every deck** ("real neighbour" rule). The `r1_bgr` netlist of record (sha256 `c19a7425…0c26`,
   checked by the runner) is the source. `r1_t2f` (`g1_t2f_rev2.spice`, `en` = 0, `mode` = 0) loads `pbias`,
   `pcasc` and `vref`. `vref` carries 11 pF (ADC `r1_reffilt5` 10 pF + 1 pF). Each output drives a fitted model
   of its consumer: every device on the consumer bias net, copied unchanged from the consumer netlist of record,
   with the mirror drains held at 1.0 V (`sim/r1_bias_loads.spice`, source sha256 listed in the file). `por_n`
   carries 0.2 pF.

## Bias table (consumer, pin, current, polarity, compliance)

Currents at tt/27 °C/3.3 V; pin voltage = consumer diode voltage with the real load; compliance = output voltage
range in which the current stays within 1 % of its value at the pin voltage (`bias-comp-20261021-d`).

| Consumer | r1_bias pin → consumer pin | Required (consumer netlist) | Delivered tt | Polarity | Consumer pin voltage (tt / ss / ff) | Compliance (tt / ss / ff) |
| --- | --- | --- | --- | --- | --- | --- |
| `r1_afe` OTA1, sine | `ib_afe_s1` → `ib_s1` | 10 µA ("sunk into the block", ideal in the AFE decks) | 10.14 µA | r1_bias sources, AFE diode `XMB0` 4/1 sinks | 0.832 / 0.861 / 0.792 V | 0–2.95 / 0–2.55 / 0–3.31 V |
| `r1_afe` OTA2, sine | `ib_afe_s2` → `ib_s2` | 10 µA | 10.14 µA | same, diode 8/2 | 0.821 / 0.840 / 0.789 V | same |
| `r1_afe` OTA1, cosine | `ib_afe_c1` → `ib_c1` | 10 µA | 10.14 µA | same | as `s1` | same |
| `r1_afe` OTA2, cosine | `ib_afe_c2` → `ib_c2` | 10 µA | 10.14 µA | same | as `s2` | same |
| `r1_isense` channel A | `ib_is_a` → `ibias_a` | 5 µA PTAT (README: "5 µA × T/300 K") | 5.07 µA | sources into diode `XMBN` 4/1 | 0.759 / 0.764 / 0.732 V | same |
| `r1_isense` channel B | `ib_is_b` → `ibias_b` | 5 µA PTAT | 5.07 µA | same | same | same |
| `r1_safe` OC A, NEG A, OC B, NEG B | `ib_sf_oa`, `ib_sf_na`, `ib_sf_ob`, `ib_sf_nb` → `ibias_oa/na/ob/nb` | 5 µA PTAT each (tails 2 × 40 µA by the cell's ×8 mirror) | 5.07 µA each | sources into diode `XMBN` 4/1 | 0.759 / 0.764 / 0.732 V | same |
| `r1_adc` reference buffer `r1_refbuf5` (option 3c) | `ib_adc_ref` → node `nb` (**new pin needed**, today `Ibias vdda nb 5u` inside the subckt) | 5 µA (×160 follower, ×40 LSB follower) | 5.07 µA | sources into diode `XMB0` 2/1 | 0.819 / 0.853 / 0.775 V | same |
| `r1_adc` comparators `r1_cmp4`, `r1_cmp5n` | — | local `rppd` bias, VDD-tracking by design since revision 3 | not served | — | — | not applicable |
| `r1_osc` comparators | — | local `rppd` bias `XRBIAS` (no bias pin) | not served | — | — | not applicable |
| `r1_t2f` | `pbias`, `pcasc` (direct from `r1_bgr`, not through r1_bias) | rails | — | gate load only | — | not applicable |

Output current over corners (all outputs scale together; 10 µA / 5 µA rows; `bias-op-20261021-d`):

| Corner | 10 µA outputs | 5 µA outputs | `iptat` |
| --- | --- | --- | --- |
| tt, 27 °C, 3.3 V | 10.14 | 5.07 | 4.23 |
| ss, 125 °C, 3.0 V | 11.81 | 5.90 | 4.92 |
| ff, −40 °C, 3.6 V | 9.00 | 4.50 | 3.76 |
| ssx (ss, −40 °C, 3.6 V) | 6.94 | 3.47 | 2.90 |
| ffx (ff, 125 °C, 3.0 V) | 15.36 | 7.68 | 6.41 |
| tt −40 / 125 °C | 7.87 / 13.41 | 3.93 / 6.71 | 3.28 / 5.59 |
| tt, `res_bcs` / `res_wcs` | 11.60 / 8.95 | 5.80 / 4.48 | 4.84 / 3.73 |
| tt at 3.0 / 3.6 V | 10.14 / 10.14 | 5.07 / 5.07 | 4.23 |

The full PTAT and resistor range is 6.9–15.4 µA for the 10 µA outputs and 3.5–7.7 µA for the 5 µA outputs. The AFE
decks used an ideal constant 10 µA, so the AFE is **not run** with this range (open issue 1).

## Files

| Path | What |
| --- | --- |
| `schematic/gen_r1_bias.py` | netlist generator (parameters of record in `P`, outputs in `LEGS`) |
| `schematic/r1_bias.spice` | netlist of record, **revision 2**, sha256 `5511ea8db822408d882fad324b1f694f82b0e4448b7e6f81a6319fd14957dfeb`; subckts `r1_bias_leg`, `r1_por_inv`, `r1_por_nand2`, `r1_por_cmp`, `r1_por_schmitt`, `r1_por`, `r1_vbuf`, `r1_bias` |
| `schematic/r1_bias_rev1d.spice` | revision 1d, sha256 `3fa56d9296f8c409fd1335a6595eae459b39324837c5bfae9ea7693584b29ff4` (the runs `*-20261021-*`) |
| `schematic/area.py` | device-area estimate from the netlist (method of `r1_isense/schematic/area.py` + HBT and device counts) |
| `sim/run_bias.py` | runner, suites `op comp mc startup psrr stb thr mcthr por`; exit 1 on any failed or unparsed job; revision 2: `vref_b` loads, offset and buffer currents in `op`/`mc`/`startup`, `conv=2` |
| `sim/run_vbuf.py`, `sim/run_vb.sh` | revision-2 buffer runner and wrapper, suites `vbstb vbzout vbpsrr vbstep vbaz vbnoise vbdrive`; exit 1 on a failed job or a failed `pass_*` check |
| `sim/make_vrefb_loads.py`, `sim/r1_vrefb_loads.spice` | `vref_b` loads copied from `r1_safe` and `r1_isense` (source sha256 in the header) |
| `sim/chain_r2.sh`, `sim/chain_r2_post.sh` | revision-2 schematic campaign; op re-run and post-layout buffer checks |
| `sim/run.sh`, `sim/chain.sh`, `sim/chain_e.sh` | wrapper (CPU set 116–119, needs `G1_RESULTS_ROOT`); campaign d chains |
| `sim/r1_bias_loads.spice` | consumer bias-pin load models (copied devices, source sha256 in the header) |
| `sim/tb_stb_toy.cir`, `sim/.spiceinit` | loop-gain method check (copy of the `r1_bgr` file); OSDI model load |
| `layout/` | layout generator, GDS of record, LVS netlist, checks and PEX scripts (see "Layout") |
| `sim/results/<run-id>.json` | summaries; `sim/runs/<run-id>/run.json` per run (command, versions, sha256, disposition) |

Raw decks, logs and waveforms: `<G1_RESULTS_ROOT>/r1_bias/<run-id>/`.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT`, checked by `flow/run.sh` |
| ngspice | 46 (PSP 103 and R3 via OSDI) | `ngspice -v` in the container, recorded in every `run.json` |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| xschem | not used (netlist generator) | — |
| KLayout, kpex | 0.30.9, 0.3.12 (layout, checks, PEX; see "Layout") | `klayout -v`, `kpex --version` in the container |
| Neighbour netlists | `r1_bgr` `c19a7425…`, `r1_t2f` `8011b761…`, loads from `r1_afe` `4a84a3d8…` (rev E), `r1_isense` `af013b95…` (rev 2), `r1_safe` `812f886d…` (rev 3), `r1_adc_r5` `a2c3c9a2…` | sha256 in the runner (`r1_bgr`, `r1_t2f`) and in the load-file header |

Command (from the repository root): `G1_RESULTS_ROOT=<G1_RESULTS_ROOT> sh designs/r1-joint/blocks/r1_bias/sim/run.sh <suite> <run-id> [cases=… n=… conv=1]`.
Corners: tt = `hbt_typ mos_tt res_typ cap_typ` 27 °C 3.3/1.2 V; ss = `hbt_wcs mos_ss res_wcs cap_wcs` 125 °C 3.0/1.08 V;
ff = `hbt_bcs mos_ff res_bcs cap_bcs` −40 °C 3.6/1.32 V; sf, fs at tt conditions; ssx = ss at −40 °C 3.6/1.32 V;
ffx = ff at 125 °C 3.0/1.08 V (r1_isense convention). Transient decks: `method=gear`, tmax 0.2 µs. Runs with
`conv=1` add `gmin=1e-12 rshunt=1e12` (≤ 1 pA/V per node).

## Status

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| Output currents tt / ss / ff | per consumer netlist (10 / 5 µA) | **passed**: 10.14 / 11.81 / 9.00 µA and 5.07 / 5.90 / 4.50 µA (PTAT, see corner table) | `sim/results/bias-op-20261021-d.json` |
| Output currents at sf, fs, ssx, ffx, tt −40/125 °C, `res_bcs/wcs`, 3.0/3.6 V | record | run (table above); supply has no effect (3.0 vs 3.6 V: < 0.01 %) | same |
| Compliance, all 11 outputs, tt/ss/ff | consumer pin inside the 1 % range | **passed**: 1 % range 0–2.55 V (ss) … 0–3.31 V (ff); pins 0.70–0.87 V; headroom ≥ 1.69 V | `bias-comp-20261021-d` |
| Mismatch MC, 50 samples, tt/27 °C/3.3 V | σ per output (record) | **run**: 49/50 in the campaign, seed 41 (operating point did not converge) passed on retry with `conv=1` (10.158 µA). σ per output 0.98–1.09 % (all outputs share σ(`iptat`) 1.07 %); σ of output/`iptat` 0.39–0.57 %. POR reference `vrh` σ 0.39 %, `vrl` 0.36 % | `bias-mc-20261021-d`, `bias-mc-20261021-d1` |
| Start-up with `r1_bgr`, 10 µs and 1 ms VDDA ramps, tt/ss/ff (VDD ramp 1 µs at t = 0) | outputs settle, no stuck state | **passed**: 10 µs ramp: all outputs within 1 % at 9.3–10.2 µs after the ramp start, `vref` at 10.9–13.2 µs, overshoot ≤ 1.8 %; 1 ms ramp: settled during the ramp at 463–674 µs (VDDA 1.67–2.02 V), overshoot ≤ 4.7 % (ff). tt/1 ms: aborted in the campaign (solver stall at 0.17 ms), passed on retry with `conv=1` | `bias-startup-20261021-d`, `bias-startup-20261021-d1` |
| PSRR, `ib_afe_s1` (10 µA), tt/ss/ff | record (no limit specified) | **run**: 20 kHz −43.8…−46.1 dB (58 nA/V); 1 MHz −20.7…−24.4 dB (0.71–0.83 µA/V); DC ≤ −95 dB. Same in dB for the 5 µA outputs. `vref` −51…−53 dB (20 kHz), −45.5…−46.9 dB (1 MHz) with this load | `bias-psrr-20261021-d` |
| `r1_bgr` loop gain with the r1_bias + T2F + consumer loads attached, 5 cuts × 7 corners (tt ss ff sf fs ssx ffx) | PM ≥ 60°, GM ≥ 10 dB | **passed** 35/35: core loop (`pbias` cut) PM 101.3–101.5° at 312–368 kHz (`r1_bgr` alone: ≈ 132°); `pcasc` no unity crossing; `vb2` GM ≥ 33.8 dB; `vbe` DC positive loop GM 12.95 dB (unchanged from `r1_bgr` alone); start-up kick loop open (GM ≥ 197 dB). Method check (toy loop) error 4.7e-8 | `bias-stb-20261021-d` |
| Supply current, whole r1_bias (VDDA), all corners | ≤ 150 µA | **passed**: 96.9 µA tt, 112.1 ss, 86.8 ff, max 146.7 µA at ffx (2 % margin); of that, POR 14.3–31.6 µA (20.8 tt). VDD: 0.35–0.88 µA (`por_raw` pull-down) | `bias-op-20261021-d` |
| POR thresholds, slow triangle ramps (0.55 V/ms VDDA, 0.35 V/ms VDD), 7 corners | VDDA rising ≤ 3.0 V and falling ≥ 2.5 V (assumed window), VDD rising ≤ 1.08 V, one transition per ramp | **passed** at tt ss ff sf fs ssx: VDDA rising 2.671–2.735 V, falling 2.577–2.633 V; VDD rising 0.989–1.013 V, falling 0.921–0.973 V; exactly one rise and one fall of every signal. **ffx**: VDDA 2.649 / 2.560 V, VDD rising 0.981 V; VDD falling **not run** on 1d (solver stall at the edge, also with `conv=1`); 1c value 0.913 V (same comparator path) | `bias-thr-20261021-d`, `bias-thr-20261021-d1`, `bias-thr-20261021-c` |
| POR power-up / ramp-down / brown-out, tt/ss/ff × {1 ms, 10 ms} (VDD first and VDDA first) + brown-out | delay ≥ 100 µs, one transition, brown-out resets | **passed** 14/15 decks: delay 197–247 µs; one rise per power-up; VDD and VDDA brown-out reset and re-release; POR current 18.8–23.6 µA. tt upA 10 ms: release passed, the ramp-down part is **not run** (deck aborted at 13.1 ms, numerical) | `bias-por-20261021-d2` |
| POR thresholds under mismatch, 30 samples, tt | record | **run**: 24/30 complete (6 numerical aborts); σ VDDA 15.7 / 15.3 mV (rise / fall), σ VDD 4.7 / 4.4 mV | `bias-mcthr-20261021-d2` |
| `por_n` before release (fast 1 µs VDD ramp with VDDA absent) | stays low | **passed** (1d): ≤ 2.0 mV at tt/ss/ff; **failed** in 1c (0.36 µs pulse to 0.66 V at ff) | `bias-startup-20261021-d`, `bias-startup-20261021-c` |
| Loop-gain margins inside r1_bias | every feedback loop | **not applicable**: the legs and the local rail are open-loop mirrors; the comparators are open-loop; the two hysteresis loops and the Schmitt trigger are positive feedback by design (bistable). Their evidence is the single transition per ramp above | — |
| Area | estimate | **estimated** before layout: ≈ 0.020 mm² (layout: 0.01991 mm²) (0.015 with MIM over devices; upper bound 0.035) (see "Area and current") | `schematic/area.py` |
| Layout, DRC, LVS, PEX, post-layout | DRC/antenna 0, LVS match, post-layout within 0.5 % | **passed**: DRC 0, antenna 0, LVS match, 0.01991 mm²; outputs −0.08…−0.10 % post-layout; POR thresholds +0.7…+3.6 mV, delay +2…+3 %. Post-layout MC, PSRR, loop gain: **not run** (see "Layout") | `layout/runs/layout-*-20261021-d`, `layout/runs/pex-rc-20261021-c`, `sim/runs/post-*-20261021-*` |
| AFE, isense, safe, ADC campaigns with r1_bias instead of ideal sources | — | **not run** (owners' tracks) | — |

## POR transients

Run `bias-por-20261021-d2` (netlist 1d, `conv=1`), 15 decks. **upA**: VDD on at 1 µs, VDDA 0 → nominal in the
ramp time, hold 1 ms, back to 0 V in the ramp time. **upD**: VDDA on (10 µs), VDD 0 → nominal from 0.3 ms, hold,
back to 0 V. **bo**: both on; at 1.0 ms VDD dips to 0.90 V, at 1.5 ms VDD dips to 0.975 V (inside the hysteresis
band), at 2.0 ms VDDA dips to 2.50 V (20 µs each, 1 µs edges). Delay = from the last fall of `rst` (both supplies
good) to `por_n` rising through VDD/2.

| Corner | Deck | `por_n` rises (ms) | Delay (µs) | Supply at release decision | `por_n` falls at | `por_n` max before release |
| --- | --- | --- | --- | --- | --- | --- |
| tt | upA 1 ms | 1 (1.066) | 246.6 | VDDA 2.703 V | VDDA 2.602 V | 1.9 mV |
| tt | upA 10 ms | 1 (8.397) | 211.8 | VDDA 2.701 V | **not run** (deck aborted at 13.1 ms in the ramp-down, solver stall in a replica HBT) | 1.9 mV |
| tt | upD 1 ms / 10 ms | 1 / 1 | 246.2 / 246.2 | VDD 1.00 V | VDD 0.949 / 0.950 V | 5.8 / 20.8 mV |
| ss | upA 1 ms / 10 ms | 1 / 1 | 233.4 / 215.3 | VDDA 2.673 / 2.671 V | VDDA 2.575 / 2.578 V | 2.0 / 2.0 mV |
| ss | upD 1 ms / 10 ms | 1 / 1 | 233.5 / 233.4 | VDD 0.989 V | VDD 0.920 / 0.921 V | 26.3 / 43.0 mV |
| ff | upA 1 ms / 10 ms | 1 / 1 | 246.0 / 197.4 | VDDA 2.722 / 2.720 V | VDDA 2.620 / 2.622 V | 1.8 / 1.8 mV |
| ff | upD 1 ms / 10 ms | 1 / 1 | 245.0 / 244.8 | VDD (rising threshold) | VDD 0.968 / 0.968 V | 3.0 / 11.6 mV |
| tt / ss / ff | bo | power-up 0.255 / 0.243 / 0.253; after the VDD dip 1.268 / 1.255 / 1.266; after the VDDA dip 2.268 / 2.255 / 2.266 | 246 / 233 / 245 | — | VDD dip to 0.90 V: falls at 1.001 ms; VDD dip to 0.975 V: **no reset** (as intended); VDDA dip to 2.50 V: falls at 2.0015 ms | 1.5–2.6 mV |

Results:

1. Delay 197–247 µs (criterion ≥ 100 µs): **passed**. It is shorter on the 10 ms VDDA ramps because the charging
   current from `pl` still rises with VDDA during the delay.
2. One `por_n` rise per power-up at 1 ms and 10 ms ramps, no extra transitions: **passed** (no oscillation).
3. Brown-out on VDD and on VDDA: **passed**. The reset follows within 1–1.5 µs of the dip edge, and release
   follows a full delay. A dip that stays inside the hysteresis band does not reset.
4. `por_n` stays ≤ 43 mV before release: **passed**.
5. POR current with both supplies up (POR part of the r1_bias VDDA current): 18.8–23.6 µA; VDD 0.39–0.70 µA.
6. Note: while VDDA < about 1.6 V the comparators are unbiased, and `rst` can be low (logic "good") for a few µs
   (`rst` falls at 3–9 µs in the 10 µs VDDA start). The delay capacitor cannot charge then, because its current
   also comes from `pl`. This is by design, and it is the reason the delay current must stay on the bandgap-derived
   rail.

Threshold mismatch (30 samples, tt, slow triangle ramps): run `bias-mcthr-20261021-d2` (`conv=1`), 24 of 30
samples complete (6 aborted with solver stalls at a comparator edge, numerical; they are excluded, so the
statistics are from 24 samples). VDDA rising 2.692 V mean, σ 15.7 mV (2.665–2.727 V); VDDA falling 2.596 V,
σ 15.3 mV (2.570–2.628 V); VDD rising 1.000 V, σ 4.7 mV (0.991–1.007 V); VDD falling 0.949 V, σ 4.4 mV
(0.941–0.955 V). Every complete sample has one rise and one fall per signal. Worst case with corners and 3σ
(estimate): VDDA rising ≤ 2.78 V, falling ≥ 2.51 V; VDD rising ≤ 1.03 V, falling ≥ 0.90 V.


## Area and current

Device area (`python3 schematic/area.py schematic/r1_bias.spice r1_bias`): drawn 5 016 µm² in 137 devices. That is
MOS 1 982 µm² (95 thick, 4 thin), MIM 1 996 µm² (delay 1.5 pF and 3 × 0.5 pF filters), `rppd` 306 µm²,
`rhigh` 732 µm² and 4 `npn13G2`. The 11 output legs are 30 MOS of 48 µm² (1 440 µm²).

| Estimate | Value |
| --- | --- |
| Footprint (MOS × 2, resistors × 2 at pitch, MIM × 1.1 for enclosure, HBT 25 µm² each) | ≈ 8 340 µm² |
| Macro at the G1 packing ratio 2.4 (`r1_osc` README) | **≈ 0.020 mm²** |
| Upper bound with the `r1_bgr` layout ratio (layout 18 650 µm² / drawn 2 676 µm² = 7.0) | 0.035 mm² (the `r1_bgr` ratio includes 38 dummy HBT) |
| With the MIM stacked over the legs (MIM is Metal5–TopMetal1) | ≈ 0.015 mm² |

The block belongs next to `r1_bgr` (short `pbias`/`pcasc`). The outputs leave as current lines.

Supply current (`bias-op-20261021-d`): see the status row. At tt: legs 76.1 µA (15 units × 5.07 µA, the sum of the
11 outputs), POR 20.8 µA (local rail 8.5, replica 4.2, comparators 6.3, divider 1.65), VDD 0.50 µA.

## Bias-line decoupling (what each consumer must provide)

1. Every bias output is a current. It goes into the consumer's own diode. Route the current line, not a gate
   voltage. Put the diode next to the mirrors it feeds. Do not share one diode between blocks.
2. Shield each line with VSS on both sides (Metal3, as the `r1_bgr` pins). Keep it away from `clk30`, the SAR
   strobes and the gate-driver lines. The line is high impedance at the r1_bias end (cascode output). A coupled
   charge goes into the consumer diode (1/g<sub>m</sub> ≈ 10–20 kΩ).
3. r1_bias needs no capacitor on its outputs. A capacitor at the r1_bias end does not help (the injected current
   splits by impedance; 1 pF at 1 MHz is 160 kΩ against the diode).
4. `r1_adc` reference buffer: `nb` is mirrored ×160 and ×40 into the followers. A bias ripple of 0.8 µA/V at 1 MHz
   (simulated PSRR) becomes about 160 µA/V of follower current. Recommended: RC filter between the diode and the
   follower gates (for example `rppd` 100 kΩ + the existing ≈ 2 pF gate load: pole ≈ 0.8 MHz), or a dedicated
   larger MOS capacitor on `nb`. The ADC track decides.
5. `r1_afe` and `r1_isense`: the gate load on the diode node (1–2 pF from the existing mirrors) is enough for DC.
   Their supply rejection with this bias source is **not run**.
6. No consumer may add a DC load to its bias pin other than its diode (a leak reduces its current one for one).

## Pins

| Pin | Dir | Domain | Notes |
| --- | --- | --- | --- |
| `vdda` | supply | 3.0–3.6 V | legs, POR analog part |
| `vdd` | supply | 1.08–1.32 V | POR output stage only (0.5 µA) and the VDD monitor input (gate only) |
| `vss` | ground | | |
| `pbias`, `pcasc` | in | VDDA | from `r1_bgr` (gate loads: 15 + 4 units of 12/4 and 10/4 µm) |
| `ib_afe_s1`, `ib_afe_s2`, `ib_afe_c1`, `ib_afe_c2` | out | VDDA | 10 µA (tt), source into the AFE diodes |
| `ib_is_a`, `ib_is_b` | out | VDDA | 5 µA (tt) |
| `ib_sf_oa`, `ib_sf_na`, `ib_sf_ob`, `ib_sf_nb` | out | VDDA | 5 µA (tt) |
| `ib_adc_ref` | out | VDDA | 5 µA (tt), into `r1_refbuf5` `nb` |
| `por_n` | out | VDD | active low reset to `r1_ctrl` and the ADC sequencers; load 0.2 pF assumed |
| `vref` | in | VDDA | revision 2: raw `r1_bgr` `vref`, gate load only (4 units 8/24 µm) |
| `vref_b` | out | VDDA | revision 2: buffered `vref` for `r1_safe`, the `r1_isense` pedestals and `r1_t2f`; Z<sub>out</sub> ≤ 2.8 Ω at DC, peak ≤ 4.8 kΩ near 0.7 MHz; drive ≥ 100 µA |

## Layout

State (2026-10-21): layout of record `layout-*-20261021-d`. DRC, antenna and LVS are clean. PEX and
post-layout simulation are done at tt, ss and ff (full RC). All post-layout numbers are simulated. Nothing is
measured.

### Files

| Path | What |
| --- | --- |
| `layout/r1_bias_layout.py` | KLayout batch generator (SG13_dev PCells, channel router from `r1_bgr`, Metal2/Metal4 self-check) |
| `layout/r1_bias.gds` | layout of record, **revision 2**, 1 104 848 bytes, sha256 `e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c` (1d: 794 kB, `354fa73c…`) |
| `layout/r1_bias_lvs.cdl` | flattened LVS netlist from the generator, revision 2: 166 units, sha256 `abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8` (1d: 137 units, `37636bf6…48ae`); dummies not listed (the deck deletes them) |
| `layout/r1_bias_layout_meta.json` | bands, trunks, channels, MIM plates, mirror-unit positions, hierarchical name map |
| `layout/run_checks.sh` | generator, DRC (main + maximal, density off), antenna, LVS, `run.json`, pin check |
| `layout/check_pins.py` | pin check from the GDS: every CDL port has a Metal3 pin and label on the boundary |
| `layout/pex_input.py`, `layout/run_pex.sh`, `layout/pex_build.py` | PEX: MIM/Metal5/TopMetal1/Via4 removed, kpex 2.5D CC, KLayout `RNetExtractor` wiring R, devices and MIM put back. Views: `rc` (full), `c` (wiring R 10 mΩ), `dev` (devices + MIM only) |
| `layout/pex_paths.py` | IR drop of the source bus and pin-to-gate resistance per mirror unit |
| `layout/runs/<run-id>/run.json` | record of every layout and PEX run (`pin_check.log` in `layout-gen-20261021-d`, `pex_paths.json` in `pex-rc-20261021-b`) |
| `sim/run_bias.py` | arguments `pex=<run-id> view=rc\|c\|dev` replace the schematic `r1_bias` with the extracted netlist |

Command (from the repository root):
1. `G1_CPUSET=116-119 G1_RESULTS_ROOT=<G1_RESULTS_ROOT> sh designs/r1-joint/blocks/r1_bias/layout/run_checks.sh 20261021-d`.
2. `sh designs/r1-joint/blocks/r1_bias/layout/run_pex.sh 20261021-d 20261021-c`.
3. `sh designs/r1-joint/blocks/r1_bias/sim/run.sh <suite> <run-id> pex=pex-rc-20261021-c view=rc conv=1`.

Extracted netlists, LVS reports and DRC databases stay in `<G1_RESULTS_ROOT>/r1_bias/<run-id>/`.

### Built against (layout)

| Item | Value | Established by |
| --- | --- | --- |
| PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh`, recorded in every `run.json` |
| KLayout | 0.30.9 (generator, PDK DRC, antenna and LVS decks, `RNetExtractor`) | `klayout -v` in the container |
| kpex | 0.3.12 (2.5D coupling capacitance only) | `kpex --version` in the container |
| ngspice | 46 | `ngspice -v`, recorded in `sim/runs/post-*/run.json` |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| Netlist of record | revision 2 `5511ea8d…` (layout `layout-*-20261026-r2c`); revision 1d `3fa56d92…` (layout `layout-*-20261021-d`) | sha256 in `layout/runs/<run-id>/run.json` |

### Floorplan

- Size: 120.0 × 165.94 µm = **0.01991 mm²** (limit 0.022 mm²). Routing on Metal1–Metal4. Metal5 and TopMetal1
  are used only for the four MIM plates (`cdel` 32, `vrh`, `vrl`, `tapa` 18 µm sides) and their via islands.
- North band: one row of 15 mirror units (12/4 µm pmosHV) plus one dummy at each end, all with the same
  orientation, pitch 5.4 µm. The AFE pairs are in common-centroid order. Two cascode rows follow (row A: the
  four 2-unit AFE legs; row B: the seven single legs and the two POR mirrors). Each row has a dummy at each end.
  The `pbias` and `pcasc` gate buses run the full row width.
- South band: the POR (resistor band with `rppd` and `rhigh`, 4 HBT, LV inverters, HV NMOS and PMOS bands, the
  stack devices). The POR has its own p+ guard ring. A p+ guard ring goes around the whole block.
- Pins (all Metal3 on the boundary): `pbias`, `pcasc` on the west edge (bandgap side). The 11 outputs on the
  north edge. `por_n` and `vdd` on the east edge. `vdda` west and east, `vss` west, east and south.
- The netlist of record has no `iptat`, `vref` or `bias_en` pin. These pins are not drawn (failure 16).

### Layout status

| Check | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| DRC, main + maximal rule tables, deep, density off | 0 markers | **passed**: 0 | `layout/runs/layout-drc-20261021-d` |
| Density | chip level after fill | **not applicable** at block level (waived) | — |
| Antenna | 0 markers | **passed**: 0 | `layout/runs/layout-ant-20261021-d` |
| LVS against `r1_bias_lvs.cdl` (revision 1d) | match | **passed**: 77 nets; hv_pmos 65, hv_nmos 22, lv_pmos 2, lv_nmos 2, rhigh 4, rppd 2, npn13G2 1 (m = 4), cap_cmim 4 | `layout/runs/layout-lvs-20261021-d` |
| Dummies in LVS | — | **not applicable**: the deck deletes devices with all terminals on one net | — |
| Pin check | 17 CDL ports as Metal3 pins on the boundary | **passed**: 17/17, no extra labels | `layout/runs/layout-gen-20261021-d/pin_check.log` |
| Area | ≤ 0.022 mm² | **passed**: 0.01991 mm² | same |
| PEX | full RC netlist | **run**: 169 devices, 137 nets, 891 R, 1081 C (1071.8 fF), 0 island ties. MIM plate-to-substrate C not in the netlist | `layout/runs/pex-rc-20261021-c` |
| Output currents tt / ss / ff, full RC | within 0.5 % of the schematic | **passed**: see the pre/post table | `sim/runs/post-op-20261021-b1`, `post-op-20261021-b`, `post-startup-20261021-b` |
| Array mismatch from wiring R | record | **run**: source drop 102.3–113.5 µV (spread 11.2 µV); output spread 0.007 % (10 µA) and 0.012 % (5 µA) at tt | `layout/runs/pex-rc-20261021-b/pex_paths.json`, `post-op-20261021-b1` |
| `c` and `dev` views at tt | separate wiring C from wiring R | **run**: both 10.1430 / 5.0715 µA (schematic 10.1419 / 5.071) | `post-op-20261021-c2`, `post-op-20261021-dev2` |
| POR thresholds tt, ss/125 °C | one transition, inside the assumed window | **passed** | `post-thr-20261021-a` |
| POR delay, 1 ms ramp, tt and ss | ≥ 100 µs, one transition | **passed**: 238–253 µs | `post-por-20261021-a` |
| Start-up, 10 µs VDDA ramp, tt | outputs settle, `por_n` low before release | **passed**: `vref` at 11.86 µs, outputs within 1 % at 10.8 µs, `por_n` ≤ 7.2 mV before release (see note) | `post-startup-20261021-a1` |
| Start-up, 10 µs ramp, ff | — | **not run** to the end: solver stall at 258.6 µs (at the `por_n` release, numerical); data up to the stall kept | `post-startup-20261021-b` |
| MC, PSRR, loop gain, cross corners post-layout | — | **not run** | — |
| LEF | — | **not run** | — |

### Pre/post (schematic → full RC, simulated)

| Item | Corner | Schematic | Post-layout | Change |
| --- | --- | --- | --- | --- |
| 10 µA outputs (µA) | tt | 10.1419 | 10.1332–10.1339 | −0.08 % |
| 5 µA outputs (µA) | tt | 5.0710 | 5.0664–5.0670 | −0.09 % |
| 10 / 5 µA outputs | ss | 11.81 / 5.90 | 11.796 / 5.898 | −0.1 % |
| 10 / 5 µA outputs | ff | 9.0005 / 4.5002 | 8.9915 / 4.4960 (transient, 20–100 µs) | −0.10 % |
| VDDA current, whole block (µA) | tt | 96.88 | 96.69 | −0.2 % |
| POR current (µA) | tt | 20.81 | 20.69 | −0.6 % |
| `vrh` (V) | tt | 1.000301 | 1.001353 | +1.05 mV |
| VDDA rising / falling (V) | tt | 2.7013 / 2.6043 | 2.7049 / 2.6064 | +3.6 / +2.1 mV |
| VDDA rising / falling (V) | ss | 2.6706 / 2.5771 | 2.6736 / 2.5788 | +3.0 / +1.7 mV |
| VDD rising / falling (V) | tt | 1.0005 / 0.9496 | 1.0015 / 0.9507 | +1.0 / +1.1 mV |
| VDD rising / falling (V) | ss | 0.9891 / 0.9210 | 0.9898 / 0.9219 | +0.7 / +0.9 mV |
| POR delay upA / upD, 1 ms (µs) | tt | 246.6 / 246.2 | 251.7 / 252.8 | +2.1 / +2.7 % |
| POR delay upA / upD, 1 ms (µs) | ss | 233.4 / 233.5 | 238.1 / 239.0 | +2.0 / +2.4 % |
| `por_n` max before release (mV) | tt / ss | 1.9–26.3 | 6.7–26.8 | — |
| `vref` settled, 10 µs ramp (µs) | tt | 12.02 | 11.86 | — |
| `por_n` rise, 10 µs ramp (µs) | tt | 253.8 | 260.2 | +6.4 µs |
| Overshoot at the ramp end | tt | 1.3 % | 3.8 % | see note |

Every case has exactly one rise and one fall of `gooda`, `goodd` and `por_n`.

Notes on the start-up (`post-startup-20261021-a1`):

1. The outputs are within 1 % at 10.8 µs. A second excursion occurs at the `por_n` edge (260.22 µs): −0.4 to
   +1.6 % for 117–166 ns. Thus the t99 metric reads 260.22 µs for 10 outputs. In the schematic, the outputs stay inside
   1 % at this edge. The likely path is the extracted coupling C between the POR and the shared rails (not isolated).
2. The overshoot at the ramp end is 3.8 % (schematic 1.3 %). The `ib_adc_ref` value of 17.5 % is a spike in the
   first nanoseconds, with VDDA near 0 V. It is not a bias overshoot.

Wiring resistance (`pex_paths.json`, unit currents from the tt post-layout op):

- Source bus: vdda pin to a unit source 7.6–9.2 Ω. The drop is 108.2 µV mean, 11.2 µV spread. It is common to
  all outputs. It shifts them about 0.1 % against the `r1_bgr` reference (same as the tt pre/post shift).
- Gate buses: `pbias` pin to gate 25–47 Ω, `pcasc` 29–68 Ω. The DC gate current is 0, so the DC drop is 0.
- Mirror drain to cascode source: 24–71 Ω (V_DS loss < 1 mV).
- `c` and `dev` views give the schematic current. The −0.09 % comes from the wiring R.

### Layout open issues

1. **Floorplan slot.** S7 (§ 3.1) gives a bias slot of 86.8 × 69.7 µm and a POR slot of 55 × 55 µm, next to
   `r1_bgr`. The layout is one 120 × 165.94 µm macro. T8 and the coordinator must re-slot it (or ask for a split POR macro).
2. **Common vdda feed.** The 108 µV source drop shifts all outputs by about 0.1 %. Feed `r1_bgr` and `r1_bias`
   from the same `vdda` trunk point.
3. Dummies are not checked by LVS (the deck deletes them). Visual and GDS checks only.
4. MIM plate-to-substrate capacitance is not in the PEX netlist (plates removed before kpex).
5. The kpex LVS gives NoMatch (series devices not combined). 100 nets named from the cross-reference, 38 not
   paired. `xpor.vq` has no name in the extracted netlist.
6. The 12/4 µm unit is drawn as the 10 µm PCell plus a 2 µm extension. LVS extracts W = 12 µm.
7. Not run: post-layout MC, PSRR, loop gain, cross corners, ff start-up to the end, LEF, density with fill.
8. The DC op at ff with the full RC netlist gives a false 1.2 % output spread (numerical, see failure 22).
   Use the transient value.

## Open issues

1. **PTAT bias for the AFE.** The AFE was designed with an ideal constant 10 µA. r1_bias gives 6.9–15.4 µA over
   the PVT corners (PTAT and `rppd`). The AFE must re-run its corners with the r1_bias source (or with this range).
   If the AFE needs a constant current, a V/R generator (`vref`/`rppd` with an amplifier) is the next option; it is
   a feedback loop and adds about 20 µA.
2. **ADC reference-buffer pin.** `r1_refbuf5` holds `Ibias vdda nb 5u` inside the subckt. r1_adc must replace it
   with a pin (`ibias`, sunk) and re-run its reference settling with the r1_bias source (×200 PTAT spread on the
   follower current: 0.69–1.54 of nominal).
3. **`vref` is loaded by `r1_t2f` in mode 0.** `XMX1` connects `vref` to the bases of `QA1`/`QA2`; the base
   current through the 190 kΩ `r1_bgr` output lowers `vref` from 1.0449 V (`r1_bgr` alone, `bgr-temp-20261020-b`)
   to 1.0428 V (these decks, tt). The shift changes when the T2F changes mode. It is a gain error for the ADC
   reference. The cause is from the netlist; a mode-1 comparison deck is **not run**.
4. **Current margin at ffx.** 146.7 µA against 150 µA. Halving the local POR rail leg (10/4 → 5/4) saves about
   4–6 µA (estimated, not run).
5. **ffx VDD falling threshold** not run on 1d (solver stall at the comparator edge). The mechanism of the
   stalls (HBT instances of `r1_bgr` at fast edges elsewhere in the deck) is not understood; it is a numerical
   issue in these decks, but it was cured only by circuit changes (1b, 1c) in two cases.
6. **Thresholds are assumptions** (VDDA 2.70/2.60 V, VDD 1.00/0.95 V, delay ≥ 100 µs). `r1_ctrl` 0.5 defines the
   reset polarity and the ADC-enable discard; the system owner confirms the values.
7. Layout open issues: see "Layout". Chip-level start-up with all blocks: **not run**.

## Failures and mistakes

| # | What | Class | Consequence / fix | Evidence |
| --- | --- | --- | --- | --- |
| 1 | POR transient decks stalled ("timestep too small" in `r1_bgr` HBTs) at the POR comparator edges with trapezoidal integration | numerical | `method=gear` in all transient decks | `dev-thr-20261021-a` |
| 2 | Gear with tmax 1 µs stalled at ssx/ffx; tmax 0.2 µs then stalled at sf/ffx; solver variants alone did not cure it | numerical | Revision 1b (local POR rail `pl`) and 1c (0.5 pF on `vrh`/`vrl`/`tapa`); campaigns a and b stopped and kept | `bias-thr-20261021-a`, `-b`, `dev-num-20261021-a`, `dev-thr-20261021-c`, `dev-fix-20261021-a` |
| 3 | Down-shifter race: with VDDA absent and a 1 µs VDD ramp at ff/−40 °C, `por_n` followed VDD to 0.66 V for 0.36 µs (thick inverter not yet on, thin inverter on) | functional-bug | Revision 1d (NMOS pass + pull-down + thin inverters); campaign c stopped | `bias-startup-20261021-c`, `dev-su-20261021-d` |
| 4 | Campaign d: three jobs failed (ffx threshold, tt 1 ms start-up, MC seed 41) | numerical | Retried as separate runs with `conv=1`; two passed, ffx VDD falling remains not run | `bias-*-20261021-d`, `-d1` |
| 5 | Ran ngspice from the results directory: `.spiceinit` not found, PSP models missing | tooling | Decks run from `sim/` | `dev-thr-20261021-a` |
| 6 | A host `kill` on the runner inside the rootless container had no effect; the pool kept starting jobs | tooling | `podman stop` on the inspected container id (only `run_bias.py` containers) | chain a |
| 7 | First wrapper scripts carried the machine results path as a default | process-hygiene | Scripts require `G1_RESULTS_ROOT` | `sim/run.sh` |
| 8 | The brief listed an ADC comparator "14 µA ideal source"; the netlist of record uses a local resistor bias since revision 3 | spec-ambiguity | Not served; recorded in the bias table | `r1_adc/README.md` revision 3 |
| 9 | The T2F loads `vref` (open issue 3), found only because the decks use the real neighbours | coordination | Recorded for `r1_t2f`/`r1_adc` | `bias-op-20261021-d` |
| 10 | The 150 µA budget has 2 % margin at ffx after the local rail (+8 µA) | estimation | Open issue 4 | `bias-op-20261021-d` |
| 11 | `bias-op-20261021-b` was marked abandoned but had completed (netlist 1) | process-hygiene | Disposition corrected: superseded | `sim/runs/bias-op-20261021-b/run.json` |
| 12 | Threshold MC: 6 of 30 samples aborted with solver stalls at a comparator edge (with `conv=1`) | numerical | Statistics from 24 samples; recorded as a gap | `bias-mcthr-20261021-d2` |
| 13 | First generator run: the Metal2 self-check found `vdd`/`tapa` stubs that crossed in channel NP | functional-bug | Mixed nets get one track each, in topological order; caught by the self-check before DRC | `layout/runs/layout-gen-20261021-a` |
| 14 | DRC run a: 164 markers (Metal3/Via3/Metal4 off-grid 148, M1.d 16); trunk x not rounded to the grid, stack strips too short | verification-gap | Trunk x rounded to 0.01 µm, strips lengthened; run b 0 markers | `layout/runs/layout-drc-20261021-a` |
| 15 | The 12/4 µm units came out at W = 0.3 µm: the pmosHV PCell limits a finger to 10 µm; the "wrong width" warning was missed | tooling | 10 µm PCell plus a 2 µm drawn extension; LVS extracts 12 µm | `layout/runs/layout-lvs-20261021-a` |
| 16 | The brief asked for 10/4 µm units and `iptat`/`vref`/`bias_en` pins; the netlist of record has 12/4 µm units and none of these pins | spec-ambiguity | The netlist of record was followed; the pins are not drawn | `schematic/r1_bias.spice` |
| 17 | LVS run b mismatch: the dummy units were in the CDL, but the deck deletes devices with all terminals on one net (known from `r1_osc`) | verification-gap | Dummies removed from the CDL; run c match | `layout/runs/layout-lvs-20261021-b` |
| 18 | kpex LVS NoMatch (series devices not combined); 38 nets not paired, `xpor.vq` unnamed | tooling | Names from the KLayout cross-reference and the hierarchical map; probes on named nodes only | `layout/runs/pex-rc-20261021-b` |
| 19 | `c` and `dev` views: no operating point with the wiring R replaced by 0.1 mΩ (also with `conv=1`) | numerical | Short set to 10 mΩ (`pex-rc-20261021-c`); both views passed | `post-op-20261021-c`, `-c1`, `-dev`, `-dev1`, `-c2`, `-dev2` |
| 20 | Post-layout: no op at ff; the tt 10 µs start-up stalled at 259.5 µs and the ff one at 258.6 µs (POR replica HBT at the `por_n` release) | numerical | `conv=1` retries for op and tt start-up passed; ff start-up not run to the end | `post-op-20261021-b`, `post-startup-20261021-a`, `-b` |
| 21 | The layout (120 × 165.94 µm) does not fit the S7 slots (86.8 × 69.7 and 55 × 55 µm, 0.0091 mm² together; the schematic estimate was 0.020 mm²) | estimation | Layout open issue 1 (T8, coordinator) | `designs/r1-joint/specification/studies/S7_REFLOORPLAN.md` § 3.1 |
| 22 | The ff op on the full RC netlist converged with `conv=1` but gives a false 1.2 % output spread; the `dev` view and the ff transient give 0.003 % | numerical | Pre/post table uses the ff transient value; op dispositions say so | `post-op-20261021-b1`, `post-op-20261021-d`, `post-op-20261021-dev3`, `post-startup-20261021-b` |
| 23 | `run_pex.sh` copied machine paths from the build log into `run.json` | process-hygiene | Paths replaced by `<G1_RESULTS_ROOT>` in the script and the records | `layout/runs/pex-rc-20261021-*/run.json` |
