# G1 full-chip simulation driven by the chip CDL (2026-09-25)

All numbers are **simulated**: ngspice-46 with the Icarus d_cosim, IHP SG13G2 open PDK
(commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`), image `tapeoutbench-eda:latest`
`sha256:ddeb6957…`. The runs are tt, 27 °C, `--timeline compact` for `c_mid`,
and the ideal 9.436194721 MHz RTL clock unless a row says otherwise.

## Headline findings

1. **The fitted GATE driver is optimistic by about 7 %.** With the real
   `sg13g2_IOPadOut30mA` from the CDL, `GATE` < 1 V is reached 1.437 µs after the fault.
   The fitted 47 Ω driver of `run_top.py` gives 1.345 µs (pex; sch: 1.436 vs 1.344 µs).
   The digital decision is unchanged: `trip_d` is 1.0578 µs in both decks.
   `GATE` < 0.33 V moves only +12 ns (1.673 vs 1.661 µs).
   - The real pad behaves as a roughly constant ~27 mA sink into the 5 nF gate: about
     5.5 V/µs from the first 60 ns on.
   - The 47 Ω fit starts at about 70 mA. `GATE` is 2.21 V vs 2.66 V at 60 ns, and 1.35 V vs 1.79 V at 300 ns.
   - Only the waveform shape differs. The two curves meet near 0.3 V.
   - These are pad-model effects. The chip wiring is the same.
2. **The CDL is a simulation-source limitation for multi-finger devices.** It omits
   `ng` on 34 G1_SENSE devices (`g1_sense`, `g1_ota`, `g1_ota_main_candidate`; ng
   2–64 in the schematic) and on the two NF4 soft-comparator input devices (`g1_cmp`
   `MM1`/`MM2`, ng=4).
   - LVS compares the total width, so the CDL is correct as an LVS reference.
   - In ngspice, however, the PDK subckt passes `nf=ng` to PSP, so the CDL simulates single-finger devices.
   - Proven in the same CDL deck (OP of the `c_mid` compact deck; only the three sense
     subckts swapped for the schematic netlist `bb933fda`):
     - SENSE `VDDA` is **1004.8 µA with the CDL vs 1088.8 µA with the schematic (−7.7 %)**.
     - `ISENSE` at the OP is +1.3 mV.
     - `VREF` and BGR are identical (1.044995 V, 319.704 µA).
   - Transient, schematic mode: SENSE 1016.8 µA vs 1101.4 µA. QUIET `ISENSE` is
     1.50806 V vs 1.50689 V (hand-wired with T2F), and `icmp` is +0.7 mV.
   - The trip timing is unaffected.
   - It is not a wiring issue. BGR, gate, T2F and level shifters carry no `ng` > 1 difference.
3. **The wiring agrees with the hand-wired deck; the T2F is the real addition.** With the
   `--netlist pex` blocks, every QUIET value and supply current matches the hand-wired
   deck to ≤ 0.01 % once that deck also carries the T2F (`--t2f tl`). T2F runs from reset
   (TEMP_CTRL = 1) and has these effects:
   - It loads `VREF`: 1.04500 V vs 1.04546 V without T2F (−0.47 mV).
   - It adds 1–2 mV p-p `VREF` ripple (0.37 mV without it; 2 µs–6 µs of the `q` prefix).
   - It draws 41 µA from `VDDA`.
   - It toggles `TEMP_OUT` at 1.518 MHz (pex; 1.574 MHz sch). That is **97 µA of `IOVDD`**
     into the assumed 20 pF board load, which the hand-wired deck does not model at all.
4. **Numerics: T2F on makes the transient fragile.** VBIC "timestep too small" failures hit
   BGR586 `xq56`/`xq736`/`xq67` and T2F `xqqa1`. This is not CDL-specific:
   - The hand-wired deck with `--t2f tl --method gear` fails the same way (22.69 µs, `xbgr.xq60`), after its trip.
   - Trap failed in every T2F-on deck (0.28–1.9 µs).
   - Gear passed with the BGR586 extraction (pex, 5 ns maximum step) and with the CDL schematic BGR at a 1 ns maximum step, or at 5 ns with reltol 5e-4.
   - It failed with a 5 ns step at 13.9 µs, and with 2 ns, gmin 1e-11, abstol 1e-12, `selft=0`, itl4 500 and the BGR PEX in sch mode at 0.3–7.3 µs.
   - Treat any CDL-driven run as fragile. Use gear with the pex BGR or a ≤ 1 ns step.

## Method (`sim/run_top_cdl.py`, `sim/rtl/g1_dig_cosim_cdl.v`; `run_top.py` unchanged)

- **Netlist source.** `blocks/g1_padring/netlist/g1_chip_top_1414.cdl` is hash-bound
  (`af5a4dbd…`). It is the canonical reference: its header says "not LVS-qualified", and
  the canonical LVS failed on 14 IO sub-cells (the projected reference passed; signoff README).
- **Translation.** The subckts reachable from `g1_chip_top` are translated to ngspice:
  - M/Q/C/D and model-R lines become PDK X devices; `$SUB=…$[rppd]` is handled.
  - Diode `a=`/`p=` are dropped.
  - Bus names `[i]`/`<i>` become `_i_`.
  - `ptap1` `A=/P=` is replaced by the `R=` of the same instance in the PDK `sg13g2_io.spi`. All ptaps tie VSS/IOVSS to the VSS substrate.
- **IO cells.** They come from the CDL's own `G1_VSS_DERIVATIVE__*` cells (explicit substrate
  pin = VSS). `sg13g2_io.spi` is therefore not included, and there is no name clash; the CDL's
  unused `sg13g2_*` IO copies are not emitted.
- **Digital.** `g1_digital` is replaced by a subckt with the CDL's exact 48-port list. Its body
  is the d_cosim of `rtl/g1_dig_cosim_cdl.v`: `g1_dig_cosim_t2f.v` plus `bgr_r4`, `fault_n`,
  `trip_set_sel` and `clk_div_out`, no logic added, `por_n` tied to 1 as today.
  - The RTL reads `EN`/`SCLK`/`SDI` from the real `IOPadIn` outputs through the 0.6 V
    single-threshold receiver. There is no d_source.
  - `g1_osc` is replaced by the ideal clock; `--osc tl` keeps it.
- **Instantiation.** One instance `Xchip`, with 22 pins on run_top's board:
  - Shunt, load, FET gate RC.
  - Supplies through 0.5 Ω/1 nF.
  - `VREF` 10 nF; `EN`/`SCLK`/`SDI` PWLs; `FAULT_N` 20 pF.
  - Added: `SDO` and `TEMP_OUT` 20 pF; the unused test pins 1 MΩ to ground.
- **Deck-local additions.** 0 V ammeters sit in series with the block supply pins, named as
  in run_top. The 4867 decap/fill/filler/antenna instances are merged into 34 with `m=N`
  (exact for identical parallel instances).
- **Pads.** `--pads nodcn` removes all 8 `dantenna` instances: the IO cells and `sg13g2_antennanp`.
- **`--netlist pex`.** The hash-bound extractions are included and the CDL definitions dropped:
  BGR586 `01227a3d`, SENSE R100 partial-C `ffb14762`, TRIP NF4 `ba86b7b2`, gate
  Sep-19 PEX, and T2F `441edabc`. Port order is checked against the CDL through a name
  normalisation.
- **Stimulus and measurements.** Both come from `run_top.build_deck` (with `--t2f tl`
  lines), with the node names mapped into the hierarchy.
- **Checks.** `--dry` resolves every instance and port count (2841 sch / 4088 pex, 0 problems).
- **Not in the CDL deck.** The `Cw_*` wire capacitors and the fitted pad drivers.
- **BGR schematic.** The CDL `g1_bgr` has no capacitors. The hand-wired "sch" BGR carries 329 historical kpex capacitors.

## Results (c_mid compact, tt 27 °C)

| Deck | trip_d µs | GATE<1 V µs | GATE<0.33 V µs | VREF V | ISENSE V | icmp V | vth_soft/hard V | VDDA µA (bgr/sense/T2F) | IOVDD µA | Wall s | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CDL pex, gear, 5 ns (`cdlv1`) | 1.0578 | **1.437** | 1.673 | 1.04500 | 1.50689 | 0.75387 | 0.80481/0.89696 | 1462.2 (319.7/1101.4/41.2) | 97.1 | 7076 | passed |
| CDL sch, gear, 1 ns (`cdlv2`) | 1.0578 | 1.436 | 1.672 | 1.04500 | 1.50806 | 0.75448 | 0.80486/0.89696 | 1376.7 (319.7/1016.8/40.3) | 97.8 | 4798 | passed |
| hand-wired pex, trap (`c1414fullc`, existing) | 1.0579 | 1.345 | 1.661 | 1.04546 | 1.50734 | 0.75404 | 0.80514/0.89737 | 1421.1 (319.7/1101.4/—) | 0.0004 | 19264 | passed |
| hand-wired sch, trap, nodcn (`cdlref1`) | 1.0578 | 1.344 | 1.660 | 1.04546 | 1.50734 | 0.75401 | 0.80512/0.89737 | 1421.2 (319.7/1101.5/—) | 0.0004 | 1655 | passed |
| hand-wired sch + `--t2f tl`, gear (`cdlref1`) | 1.0578 | 1.344 | 1.660 | 1.04499 | 1.50689 | 0.75379 | 0.80476/0.89696 | 1462.3 (319.7/1101.4/—) | 0.0004 | 2333 | trip passed; failed at 22.69 µs (`xbgr.xq60`), not run to completion |
| CDL sch, other numerics (`cdlv1/v2/v3/v4/v5`) | — | — | — | — | — | — | — | — | — | — | failed: trap 0.28 µs; gear 5 ns 13.9 µs; see finding 4. Three v5 variants stopped by me to free CPUs: not run to completion |
| CDL sch, gear 5 ns, reltol 5e-4 (`cdlv2`) | 1.0578 | 1.436 | 1.672 | 1.04500 | 1.50806 | 0.75445 | 0.80483/0.89696 | — | — | 5428 | passed |
| CDL sch, gear 1 ns + itl4 500 (`cdlv5`) | — | — | — | — | — | — | — | — | — | — | still running at time of writing |

### q, 6 µs prefix (`--analysis prefix --tstop 6`)

| Deck | Status | VREF / ISENSE at 6 µs | Wall s |
|---|---|---|---|
| CDL sch, gear | passed | 1.044977 / 1.507718 | 690 |
| CDL sch, trap | failed at 0.284 µs (`xq56`) | — | 86 |
| hand-wired sch, trap, nodcn | passed | 1.045465 / 1.507085 | 294 |
| hand-wired sch + `--t2f tl`, gear | passed | 1.044994 / 1.506626 | 544 |

**Speed.** The CDL deck adds the IO ring, the T2F and three level shifters at transistor level.
- CDL q prefix: 2.3× the hand-wired trap deck and 1.3× the hand-wired T2F/gear deck.
- CDL sch `c_mid` (1 ns step): 2.9× the hand-wired sch trap deck.
- The CDL pex gear run (7076 s) was faster than the hand-wired pex **trap** run (19264 s). The integration method dominates.

## Commands (repository root, `BULK=${BULK}`)

```
W=designs/g1-guardian/blocks/g1_top/sim
flow/launch_pinned.sh 21 $W 14400 <log> python3 run_top_cdl.py q --analysis prefix --tstop 6 --method gear --timeout 14000 --run-id cdlv1
flow/launch_pinned.sh 27 $W 14400 <log> python3 run_top_cdl.py c_mid --timeline compact --netlist pex --method gear --timeout 14000 --run-id cdlv1
flow/launch_pinned.sh 21 $W 14400 <log> python3 run_top_cdl.py c_mid --timeline compact --method gear --maxstep-ns 1 --timeout 14000 --run-id cdlv2
flow/launch_pinned.sh 25 $W 14400 <log> python3 run_top.py c_mid --timeline compact --blockset c1414 --netlist sch --inpads nodcn --timeout 14000 --run-id cdlref1
flow/launch_pinned.sh 20 $W 14400 <log> python3 run_top.py c_mid --timeline compact --blockset c1414 --netlist sch --inpads nodcn --t2f tl --method gear --timeout 14000 --run-id cdlref1
G1_WORKDIR=$W flow/run.sh python3 run_top_cdl.py c_mid --timeline compact --dry      # instance/port check only
```

Logs: `sim/logs/cdl_*_{cdlv1..cdlv5,cdlpwr}.log/.json`. Summaries: `sim/results_cdl.txt`.
Decks: `sim/decks/cdl_*.cir`.

## Power-up, core first (gB, gB_pd; CDL pex gear deck, `--por-pin`, run-id `cdlpwr`)

These runs use the CDL pex gear deck with `--por-pin`:
- `por_n` comes from the CDL `sg13g2_tiehi` (wrapper `rtl/g1_dig_cosim_cdl_por.v`).
- `EN`, `GATE` and `FAULT_N` are the CDL pad cells.
- Ramps are as in run_top: `VDD` 1–3 µs, `IOVDD`=`VDDA` 5–7 µs, `EN` low until 12 µs.

**Pad treatment.** With every pad `dantenna` kept (`--pads pdk`), both tt runs stalled at
1.377 µs, as `VDD` rose. They were stopped after 806 s: **not run to completion**. The known
`darea` diode stall applies. The rows below therefore use `--pads nodcn`: all 8 `dantenna`
instances are removed, including those of the EN/GATE/FAULT_N pads.

| Case | Corner | GATE max, EN low (V) | gate_core max (V) | en_i max, EN low (V) | tripped max (V) | dig_trip max (V) | GATE after EN (V) | tripped end | Wall s | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| gB | tt 27 °C | 0.00024 | 0.612 | **0.853** | 1.217 | 1.2 | 3.300 | 0 | 1391 | passed |
| gB_pd | tt 27 °C | 0.00024 | 0.612 | 0.853 | 1.217 | 1.2 | 3.288 | 0 | 1726 | passed |
| gB | ss 125 °C | 0.00005 | 0.611 | **0.922** | 1.219 | 1.2 | 3.300 | 0 | 1382 | passed |
| gB_pd | ss 125 °C | 0.00005 | 0.611 | 0.922 | 1.219 | 1.2 | 3.283 | 0 | 1369 | passed |
| gB_pd | ff −40 °C | 0.00027 | 0.615 | 0.836 | 1.211 | 1.2 | 3.291 | 0 | 1668 | passed |
| gB | ff −40 °C | 0.00027 (to 7.42 µs) | 0.615 | 0.836 | 1.211 | 1.2 | — | — | 745 | failed: timestep too small at 7.42 µs (`xbgr.xq784`) |

**Finding 5: `EN` floats high while `IOVDD` is absent.** With `IOVDD` absent (core first),
the CDL `IOPadIn` (`LevelDown`) output `en_i` rises with `VDD` to 0.84–0.92 V
(0.70–0.77·VDD). At tt it exceeds 0.6 V from 2.34 µs to 5.70 µs. While it is high, the RTL
reads `EN` = 1 and its trip latch sets (`dig_trip` 2.86–5.70 µs), and G1_GATE's `tripped`
latch sets (2.08–5.78 µs).
- Both clear when `IOVDD` passes about 1.1 V (5.667 µs).
- `GATE` stays ≤ 0.27 mV, because the GATE pad driver has no `IOVDD`.
- The outcome is safe, but the latches toggle on an undefined pad output. The ideal EN copy of the hand-wired deck cannot show this.

**Reset timing.** `por_n` (the tiehi output) crosses 0.6 V at 2.0006 µs, with `VDD` crossing
0.6 V at 2.0006 µs. That is 3.67 µs *before* `IOVDD` reaches 1.1 V (5.667 µs). The RTL
therefore leaves reset while `EN` is still undefined.

**Artifact.** `osc_en` "rises" at 1 ns because the dac_bridge `out_high` is a fixed 1.2 V,
independent of `VDD`. RTL output levels before `VDD` is up are not physical.

`q` full length (44 µs, CDL pex gear, `cdlpwr`, wall 25200 s): completed in 9762 s, no trip; QUIET (28–30 µs) vref 1.0450 V, isense 1.50687 V, icmp 0.7535 V, vth_soft 0.8044 V, vth_hard 1.0037 V; VDDA 1462.5 µA (BGR 319.7, SENSE 1101.4), IOVDD 103.8 µA, VDD 7.0 µA.

## Not established

- The fitted-driver and pad difference was checked at tt/27 °C only.
- The `ng` restoration is shown at OP and by the block swap, not as a full `c_mid` run.
- The oscillator is not transistor-level (`--osc tl` untested).
- `c_mid` compact only; `f_mid`/`gA` not run.
