# r1_bias — bias distribution and power-on reset (R1, track T9)

State (2026-10-21): **schematic simulated**, revision 1d. Layout **not run**. All numbers are simulated (ngspice 46,
schematic level, no layout parasitics). Nothing is measured.

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
| `schematic/r1_bias.spice` | netlist of record, revision 1d, sha256 `3fa56d9296f8c409fd1335a6595eae459b39324837c5bfae9ea7693584b29ff4`; subckts `r1_bias_leg`, `r1_por_inv`, `r1_por_nand2`, `r1_por_cmp`, `r1_por_schmitt`, `r1_por`, `r1_bias` |
| `schematic/area.py` | device-area estimate from the netlist (method of `r1_isense/schematic/area.py` + HBT and device counts) |
| `sim/run_bias.py` | runner, suites `op comp mc startup psrr stb thr mcthr por`; exit 1 on any failed or unparsed job |
| `sim/run.sh`, `sim/chain.sh`, `sim/chain_e.sh` | wrapper (CPU set 116–119, needs `G1_RESULTS_ROOT`); campaign d chains |
| `sim/r1_bias_loads.spice` | consumer bias-pin load models (copied devices, source sha256 in the header) |
| `sim/tb_stb_toy.cir`, `sim/.spiceinit` | loop-gain method check (copy of the `r1_bgr` file); OSDI model load |
| `sim/results/<run-id>.json` | summaries; `sim/runs/<run-id>/run.json` per run (command, versions, sha256, disposition) |

Raw decks, logs and waveforms: `<G1_RESULTS_ROOT>/r1_bias/<run-id>/`.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT`, checked by `flow/run.sh` |
| ngspice | 46 (PSP 103 and R3 via OSDI) | `ngspice -v` in the container, recorded in every `run.json` |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| xschem, KLayout | not used (netlist generator; no layout) | — |
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
| Area | estimate | **estimated**: ≈ 0.020 mm² (0.015 with MIM over devices; upper bound 0.035) (see "Area and current") | `schematic/area.py` |
| Layout, DRC, LVS, PEX, post-layout | — | **not run** | — |
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
7. Layout, LVS, PEX, post-layout checks and chip-level start-up with all blocks: **not run**.

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
