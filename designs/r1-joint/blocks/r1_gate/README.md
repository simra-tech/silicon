# R1_GATE — gate output path for the three `sg13g2_IOPadOut30mA` pads (schematic level)

State on 2026-10-21: **schematic written, simulated with the PDK pad model at three corners. Laid out (both variants), DRC, antenna and LVS clean, see "Layout" at the end. No PEX, no post-layout simulation.** No parasitics in the simulations. All numbers are
**simulated** (ngspice-46). Nothing is measured.

## Answer first: does the pad need an extra 1.2 V to 3.3 V shifter?

**No.** The PDK cell `sg13g2_IOPadOut30mA` has its own core-to-IO level shifter on `c2p`. The subcircuit is:

```
.subckt sg13g2_IOPadOut30mA pad c2p vdd vss iovdd iovss
XI2 net2 net1 iovdd c2p vdd vss sg13g2_GateLevelUpInv     <- two sg13g2_LevelUpInv, input c2p on the core VDD (1.2 V)
XI1 net1 iovdd iovss pad sg13g2_Clamp_P15N15D             <- output PMOS driver
XI3 net2 iovss pad sg13g2_Clamp_N15N15D                   <- output NMOS driver
```

(`libs.ref/sg13g2_io/spice/sg13g2_io.spi`, PDK commit below.) `c2p` is a 1.2 V input. The shifter is inside the pad and runs from `iovdd`.

Consequence for R1:

1. The PWM path needs **no** 1.2 V to 3.3 V shifters. The gating AND can sit in the 1.2 V core and drive `c2p` directly (variant L below).
2. Shifters are needed only if the AND is built in the 3.3 V domain, as in G1 (variant H below). Then 4 x `g1_lvlup` (3 `pwm` + `gate_en`) and
   3 x `g1_lvldn` are needed, and the shifted signal is shifted back to 1.2 V for the pad. That is an up-shift and a down-shift in front of a pad
   that shifts up again.
3. In G1 the 3.3 V domain was chosen for the trip latch (thick-oxide gates resist single-event upsets). R1 has no latch in this block.
   The fault latch is in `r1_ctrl` / `r1_safe`.
4. Simulation shows no difference at the pad between the two variants (tables below): the pad output delay differs by 2 ns at most
   (the HV chain delay) and the peak supply currents differ by 9 % at most.

Recommendation: variant L. A decision on single-event hardness is open (see "Open issues"). It was **not run**.

## Built against

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` in the container (`flow/run.sh` checks it) |
| ngspice | 46 | `ngspice -v` in the container |
| Container image | `tapeoutbench-eda:latest`, `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` compares the image id before each run |
| Models | `cornerMOSlv.lib`, `cornerMOShv.lib` (`mos_tt/ss/ff`), `cornerRES.lib res_typ`, `cornerCAP.lib cap_typ`, `cornerDIO.lib dio_tt`; PSP103 OSDI | decks in `<G1_RESULTS_ROOT>/r1_gate/g20261020b/*/deck.cir` |
| Pad model | `sg13g2_IOPadOut30mA` from `sg13g2_io.spi`, **deck-local copy without the `dantenna` devices ("nodcn")** | see "Deviation" below |
| G1 cells | `schematic/g1_cells_copy.spice` = byte copy of `designs/g1-guardian/blocks/g1_gate/sim/netlist/g1_gate.spice`, sha256 `846a55e037c5ab6e63a7490e941dc957292fe93de9d1f88bd25ab9ba5610d97c` | `sha256sum` equals the G1 file |
| R1 gate netlist | `schematic/r1_gate.spice`, sha256 `a95a9a8c558e8b594dcf1e5580a0df719765ea6a917af1b08e4e4b4a777662c7` | `sha256sum` |
| CPU | CPU 119 only, `num_threads=1` in `sim/.spiceinit` | run commands in `sim/runs/*/*/run.json` |

### Deviation: pad model without `dantenna`

With the stock pad file, the 5 nF transient stalls ("Timestep too small", node `d.xp?.xi?.xd0.d1#internal` = the `dantenna` diode of the pad):
tt at 8.90 us, ss at 0.2 us (runs `g20261020a-stock`, four failed runs kept in `sim/runs/g20261020a-stock/`). A 1 nF smoke test at tt with the stock pad
completed in an earlier version of the script (not kept). This is the known `dantenna` discontinuity (G1 deck notes). The fix is the G1 one:
`sim/make_nodcn.sh` writes a copy of `sg13g2_io.spi` in which every `dantenna` device (7 lines in the file; in this pad: two in `sg13g2_DCNDiode` and one in `sg13g2_Clamp_N15N15D`)
is commented out. The PDK file and all model cards are unchanged. The kept parts are the clamps, `dpantenna` (`sg13g2_DCPDiode`) and the substrate resistors.
Effect: the pad-to-ground diode `dantenna` does not conduct in the model. The pad node stays between 0 and IOVDD in these decks, so these diodes are reverse biased or off. The effect on the results is expected to be small. This was **not** checked by a stock-pad run at 5 nF (it stalls).

Other deck choices, as in the G1 gate deck: `.option method=gear reltol=0.005 itl4=100 abstol=1e-9 vntol=1e-5 chgtol=1e-13`, supplies through 0.5 ohm
with 1 nF local decoupling, 2 ns stimulus edges, 10 ohm in series with the load capacitor (board gate resistor stand-in).

## Circuit

Netlist `schematic/r1_gate.spice` has two top cells. Both have ports `pwm_a pwm_b pwm_c gate_en gc_a gc_b gc_c vdd vdda vss`.
`gc_x` goes to `c2p` of pad `x`.

| Variant | Content | Cells (unchanged G1 cells) |
| --- | --- | --- |
| **H** `r1_gate_hv` | `pwm_x` and `gate_en` shifted up (`g1_lvlup`); `gate_h = NOR(!en_h, !pwm_h)` in thick oxide; back down with `g1_lvldn` (needs `gate_h` and its complement) | 4 x `g1_lvlup`, 1 + 3 x `g1_hv_inv` at the input, 3 x `g1_hv_nor2`, 3 x `g1_hv_inv`, 3 x `g1_lvldn` |
| **L** `r1_gate_lv` | `gc_x = pwm_x & gate_en` in the core | 3 x `g1_lv_nand2`, 3 x `g1_lv_inv` |

`vdda` of variant H is tied to the same `IOVDD` net as the pad (the decks do this). The G1 SR latch is dropped in both variants.
A shared `gate_en` shifter and inverter serve all three channels in variant H.

## Test bench (`sim/run_gate.py`)

One deck per case, generated by the script. Three pads, each with 10 ohm and a load capacitor to ground. One 40 us timeline per case, segment S = 4 us (10 segments):

| Time | Event | Purpose |
| --- | --- | --- |
| 0.2 us | `gate_en` rises (`pwm_b` is already high) | enable path |
| S - 50 ns, S | `b` falls, then `a` and `c` rise 50 ns later | dead time 50 ns, turn-off of b then turn-on of a |
| 2S, 2S + 50 ns | `a` and `c` fall, then `b` rises 50 ns later | dead time 50 ns, turn-off of a then turn-on of b |
| 3S | `b` falls alone | clean single falling edge |
| 4S, 5S | `c` rises alone, falls alone | clean single rising edge |
| 6S, 7S, 8S | all three rise, fall, rise together | simultaneous switching |
| 9S | `gate_en` falls with all three `pwm` high | fault path |

Corners: tt (`mos_tt`, 27 C, IOVDD 3.3 V, VDD 1.2 V), ss (125 C, 3.0 V, 1.08 V), ff (-40 C, 3.6 V, 1.32 V). Loads: 5 nF, 1 nF, and 1 pF for the cross-conduction case.
Two supply models: **ideal** (0.5 ohm + 1 nF, ideal ground; as G1) and **package** (IOVDD pin 1 nH + 0.1 ohm; two IOVSS pins in parallel 0.5 nH + 0.05 ohm in total;
decoupling between the on-chip IOVDD and IOVSS nodes 1 nF or 100 pF; core VDD and core VSS stay ideal). The pin count follows the R1 pin map
(one `IOVDD`, two `IOVSS` pads, `../r1_padring/README.md`). The on-chip decoupling value is **assumed** (unknown until the core is placed).
The substrate node `sub!` is tied to ideal ground in all decks (as in G1).

Post-processing: `sim/analyze_gate.py` reads the `wrdata` waveform file and measures crossings by linear interpolation. Delays are from the 50 % point of `pwm`
(1.2 V domain) to the 50 % point of the node (half of IOVDD). Edge times are 10 to 90 % of IOVDD.

## Results (simulated, schematic level, run `g20261020b`: 27 of 27 cases completed)

Notes for reading the tables:

- "pad" is the `pad` pin of the `sg13g2_IOPadOut30mA`. "FET gate" is the node after the 10 ohm series resistor (the load capacitor).
- `pwm->gc` is the delay through the gating logic only (from a 2 ns edge). Variant L is almost zero. Variant H adds the up-shift, NOR and down-shift.
- The dead time of 50 ns is an ideal input. The pad edges are much slower than 50 ns for 1 nF and 5 nF (tables a and b).

### (a) Timing, ideal supply (0.5 ohm + 1 nF), pad node and FET-gate node (10 ohm + C)

Single-channel edges. Rise: `c` rises alone. Fall: `b` falls alone. Delay = pwm 50 % to node 50 % (half of IOVDD). Times in ns.

| Path | Corner | Load | pwm->`gc` rise | pwm->pad rise | pad 10-90 % | FET gate 10-90 % | pwm->`gc` fall | pwm->pad fall | pad 90-10 % | FET gate 90-10 % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HV | tt 27 C 3.3 V / 1.2 V | 5 nF | 0.77 | 250 | 666 | 671 | 0.75 | 242 | 606 | 612 |
| LV | tt 27 C 3.3 V / 1.2 V | 5 nF | 0.07 | 248 | 666 | 671 | 0.03 | 241 | 606 | 612 |
| HV | ss 125 C 3.0 V / 1.08 V | 5 nF | 2.29 | 406 | 990 | 993 | 1.55 | 398 | 922 | 926 |
| LV | ss 125 C 3.0 V / 1.08 V | 5 nF | 0.09 | 404 | 990 | 993 | 0.09 | 396 | 922 | 926 |
| HV | ff -40 C 3.6 V / 1.32 V | 5 nF | 0.99 | 161 | 473 | 491 | 0.56 | 159 | 429 | 448 |
| LV | ff -40 C 3.6 V / 1.32 V | 5 nF | 0.05 | 159 | 473 | 491 | 0.12 | 158 | 429 | 448 |
| HV | tt 27 C 3.3 V / 1.2 V | 1 nF | 0.77 | 52 | 133 | 134 | 0.75 | 50 | 121 | 123 |
| LV | tt 27 C 3.3 V / 1.2 V | 1 nF | 0.07 | 51 | 133 | 134 | 0.03 | 49 | 121 | 122 |
| HV | ss 125 C 3.0 V / 1.08 V | 1 nF | 2.29 | 86 | 198 | 199 | 1.55 | 83 | 184 | 185 |
| LV | ss 125 C 3.0 V / 1.08 V | 1 nF | 0.09 | 83 | 198 | 199 | 0.09 | 81 | 184 | 185 |
| HV | ff -40 C 3.6 V / 1.32 V | 1 nF | 0.99 | 34 | 94 | 98 | 0.56 | 33 | 86 | 90 |
| LV | ff -40 C 3.6 V / 1.32 V | 1 nF | 0.05 | 33 | 94 | 98 | 0.12 | 32 | 86 | 90 |

### (b) Skew and edge overlap (50 ns ideal dead time between a/c and b)

Gap = time when the turn-on edge crosses the level minus time when the turn-off edge crosses the level. Positive: no overlap. Negative: both nodes are above the level together. Level 1 V stands for a FET threshold, level IOVDD/2 is the logic mid-point. Same edge pairs at the pad node and at the FET-gate node (after 10 ohm + C). Times in ns.

| Path | Corner | Load | gap b off -> a on, pad, IOVDD/2 | pad, 1 V | FET gate, IOVDD/2 | FET gate, 1 V | gap a off -> b on, pad, IOVDD/2 | pad, 1 V | FET gate, IOVDD/2 | FET gate, 1 V | spread of 3 pad delays, 3 gates rising together | falling together | fall - rise delay (single edges) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HV | tt 27 C 3.3 V / 1.2 V | 5 nF | 58.4 | -202.4 | 58.8 | -204.7 | 57.2 | -202.0 | 57.6 | -204.2 | 0.0000 | 0.0000 | -8.0 |
| LV | tt 27 C 3.3 V / 1.2 V | 5 nF | 58.0 | -202.8 | 58.4 | -205.0 | 56.5 | -202.7 | 56.8 | -205.0 | 0.0001 | 0.0000 | -7.9 |
| HV | ss 125 C 3.0 V / 1.08 V | 5 nF | 57.3 | -275.8 | 57.5 | -277.0 | 56.5 | -275.1 | 56.7 | -276.3 | 0.0020 | 0.0000 | -8.3 |
| LV | ss 125 C 3.0 V / 1.08 V | 5 nF | 56.9 | -276.2 | 57.0 | -277.4 | 56.1 | -275.5 | 56.2 | -276.7 | 0.0020 | 0.0000 | -7.9 |
| HV | ff -40 C 3.6 V / 1.32 V | 5 nF | 51.5 | -160.4 | 52.2 | -164.0 | 50.9 | -159.3 | 51.6 | -163.0 | 0.0000 | 0.0000 | -2.0 |
| LV | ff -40 C 3.6 V / 1.32 V | 5 nF | 51.1 | -160.7 | 51.9 | -164.4 | 49.8 | -160.4 | 50.5 | -164.1 | 0.0000 | 0.0000 | -1.1 |
| HV | tt 27 C 3.3 V / 1.2 V | 1 nF | 53.5 | 1.2 | 53.5 | 0.8 | 53.0 | 1.1 | 53.0 | 0.6 | 0.0000 | 0.0000 | -2.3 |
| LV | tt 27 C 3.3 V / 1.2 V | 1 nF | 52.8 | 0.4 | 52.8 | -0.0 | 52.2 | 0.3 | 52.3 | -0.1 | 0.0000 | 0.0000 | -2.2 |
| HV | ss 125 C 3.0 V / 1.08 V | 1 nF | 53.1 | -13.6 | 53.1 | -13.8 | 52.8 | -13.6 | 52.8 | -13.9 | 0.0000 | 0.0000 | -2.9 |
| LV | ss 125 C 3.0 V / 1.08 V | 1 nF | 52.7 | -14.0 | 52.7 | -14.2 | 52.4 | -14.0 | 52.4 | -14.3 | 0.0000 | 0.0000 | -2.5 |
| HV | ff -40 C 3.6 V / 1.32 V | 1 nF | 51.2 | 8.8 | 51.3 | 8.1 | 51.4 | 9.4 | 51.5 | 8.6 | 0.0000 | 0.0000 | -1.4 |
| LV | ff -40 C 3.6 V / 1.32 V | 1 nF | 51.0 | 8.6 | 51.1 | 7.9 | 50.3 | 8.3 | 50.5 | 7.5 | 0.0000 | 0.0000 | -0.4 |

### (b-i) Pad output stage cross-conduction (current from the opposite rail during an edge, baseline removed, first 200 ns)

Fall edge: IOVDD current (the load discharges to ground through IOVSS, so IOVDD current is cross-conduction and shifter current). Rise edge: IOVSS current. Single-channel edges.

| Corner | Load | fall edge: IOVDD peak (mA) | fall edge: IOVDD charge (pC) | rise edge: IOVSS peak (mA) | rise edge: IOVSS charge (pC) |
| --- | --- | ---: | ---: | ---: | ---: |
| tt 27 C 3.3 V / 1.2 V | 1 pF | 12.54 | 19.7 | 0.852 | 0.4 |
| ss 125 C 3.0 V / 1.08 V | 1 pF | 7.06 | 15.2 | 0.346 | -0.1 |
| ff -40 C 3.6 V / 1.32 V | 1 pF | 18.81 | 24.0 | 2.169 | 0.5 |
| tt 27 C 3.3 V / 1.2 V | 1 nF | 3.71 | 7.4 | 0.094 | -0.1 |
| ss 125 C 3.0 V / 1.08 V | 1 nF | 1.72 | 4.8 | 0.036 | -0.2 |
| ff -40 C 3.6 V / 1.32 V | 1 nF | 6.59 | 11.0 | 0.042 | -0.1 |
| tt 27 C 3.3 V / 1.2 V | 5 nF | 3.60 | 6.9 | 0.094 | -0.1 |
| ss 125 C 3.0 V / 1.08 V | 5 nF | 1.64 | 4.2 | 0.035 | -0.2 |
| ff -40 C 3.6 V / 1.32 V | 5 nF | 6.46 | 10.5 | 0.034 | -0.2 |

### (c) Three gates switching together into 5 nF, package model (1 nH + 0.1 ohm IOVDD pin, 2 IOVSS pins in parallel at 0.5 nH + 0.05 ohm)

Rising: IOVDD current peak and mean over the 10-90 % window of the slowest FET gate. Falling: IOVSS return current. Bounce = deviation of the on-chip IOVDD / IOVSS node from the ideal rail.

| Path | Corner | On-chip IOVDD-IOVSS decap | rise: IOVDD peak (mA) | rise: mean (mA) | rise: charge (nC) | IOVDD droop (mV) | fall: IOVSS peak (mA) | IOVSS bounce, max (mV) | core VDD min (V) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HV | tt 27 C 3.3 V / 1.2 V | 1 nF | 135.2 | 59.6 | 45.0 | 64.9 | 50.1 | 5.4 | 1.2000 |
| LV | tt 27 C 3.3 V / 1.2 V | 1 nF | 138.8 | 59.8 | 45.0 | 70.4 | 50.1 | 5.4 | 1.2000 |
| HV | ss 125 C 3.0 V / 1.08 V | 1 nF | 71.5 | 36.8 | 40.8 | 30.2 | 29.9 | 3.1 | 1.0800 |
| LV | ss 125 C 3.0 V / 1.08 V | 1 nF | 77.8 | 36.9 | 40.8 | 35.8 | 29.9 | 3.1 | 1.0800 |
| HV | ff -40 C 3.6 V / 1.32 V | 1 nF | 220.1 | 88.6 | 49.2 | 114.7 | 76.0 | 8.5 | 1.3200 |
| LV | ff -40 C 3.6 V / 1.32 V | 1 nF | 219.4 | 88.7 | 49.2 | 113.8 | 76.0 | 8.4 | 1.3200 |
| HV | tt 27 C 3.3 V / 1.2 V | 100 pF | 101.3 | 59.6 | 44.9 | 95.8 | 50.0 | 5.6 | 1.2000 |
| LV | tt 27 C 3.3 V / 1.2 V | 100 pF | 104.4 | 59.8 | 44.9 | 106.7 | 50.0 | 5.5 | 1.2000 |
| HV | ss 125 C 3.0 V / 1.08 V | 100 pF | 54.8 | 36.8 | 40.8 | 38.0 | 29.8 | 3.1 | 1.0800 |
| LV | ss 125 C 3.0 V / 1.08 V | 100 pF | 55.0 | 36.9 | 40.8 | 39.0 | 29.8 | 3.0 | 1.0800 |
| HV | ff -40 C 3.6 V / 1.32 V | 100 pF | 175.0 | 88.6 | 49.2 | 199.8 | 75.8 | 9.3 | 1.3200 |
| LV | ff -40 C 3.6 V / 1.32 V | 100 pF | 169.7 | 88.7 | 49.2 | 184.9 | 75.8 | 9.3 | 1.3200 |

### (d) Fault path: `gate_en` falls with all three `pwm` high (ideal supply)

Time from `gate_en` 50 % to the node below 0.33 V (10 % of 3.3 V) and below 1 V; worst of three channels. Requirement: pad below 0.33 V within 200 ns.

| Path | Corner | Load | pad < 0.33 V (ns) | pad < 1 V (ns) | FET gate < 0.33 V (ns) | pad voltage at 200 ns (V) | Requirement 200 ns |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| HV | tt 27 C 3.3 V / 1.2 V | 5 nF | 614 | 378 | 670 | 1.87 | failed |
| LV | tt 27 C 3.3 V / 1.2 V | 5 nF | 612 | 376 | 669 | 1.86 | failed |
| HV | ss 125 C 3.0 V / 1.08 V | 5 nF | 933 | 571 | 987 | 2.15 | failed |
| LV | ss 125 C 3.0 V / 1.08 V | 5 nF | 932 | 570 | 986 | 2.14 | failed |
| HV | ff -40 C 3.6 V / 1.32 V | 5 nF | 444 | 272 | 503 | 1.48 | failed |
| LV | ff -40 C 3.6 V / 1.32 V | 5 nF | 443 | 271 | 503 | 1.47 | failed |
| HV | tt 27 C 3.3 V / 1.2 V | 1 nF | 125 | 77 | 136 | 0.05 | passed |
| LV | tt 27 C 3.3 V / 1.2 V | 1 nF | 123 | 76 | 135 | 0.05 | passed |
| HV | ss 125 C 3.0 V / 1.08 V | 1 nF | 190 | 118 | 201 | 0.28 | passed |
| LV | ss 125 C 3.0 V / 1.08 V | 1 nF | 189 | 116 | 200 | 0.27 | passed |
| HV | ff -40 C 3.6 V / 1.32 V | 1 nF | 90 | 56 | 102 | 0.01 | passed |
| LV | ff -40 C 3.6 V / 1.32 V | 1 nF | 89 | 55 | 101 | 0.01 | passed |

### (e) Static and per-edge supply current (ideal supply, single-channel edges)

Static values are the mean over 90 ns before an edge with all three channels low or all high (three pads, three paths, includes the pad). Charge per edge: `c` rises alone (IOVDD) and `b` falls alone; core charge is taken from the 1.2 V supply.

| Path | Corner | Load | static IOVDD, all low / all high (nA) | static core VDD, all low / all high (nA) | IOVDD charge per rising edge (nC) | core VDD charge, rising edge / falling edge (pC) |
| --- | --- | --- | --- | --- | ---: | --- |
| HV | tt 27 C 3.3 V / 1.2 V | 5 nF | not static (5 nF still settles in the window) | 1.54 / 2.13 | 14.98 | 0.05 / 0.11 |
| LV | tt 27 C 3.3 V / 1.2 V | 5 nF | not static (5 nF still settles in the window) | 1.72 / 2.29 | 14.98 | 0.05 / 0.06 |
| HV | ss 125 C 3.0 V / 1.08 V | 5 nF | not static (5 nF still settles in the window) | 6.83 / 14.97 | 13.58 | 0.06 / 0.07 |
| LV | ss 125 C 3.0 V / 1.08 V | 5 nF | not static (5 nF still settles in the window) | 7.98 / 15.85 | 13.58 | 0.06 / 0.06 |
| HV | ff -40 C 3.6 V / 1.32 V | 5 nF | not static (5 nF still settles in the window) | 2.13 / 3.37 | 16.39 | 0.11 / 0.16 |
| LV | ff -40 C 3.6 V / 1.32 V | 5 nF | not static (5 nF still settles in the window) | 2.44 / 3.54 | 16.39 | 0.06 / 0.10 |
| HV | tt 27 C 3.3 V / 1.2 V | 1 nF | 0.35 / 0.20 | 1.54 / 2.13 | 3.08 | 0.05 / 0.11 |
| LV | tt 27 C 3.3 V / 1.2 V | 1 nF | 0.27 / 0.11 | 1.72 / 2.29 | 3.08 | 0.05 / 0.06 |
| HV | ss 125 C 3.0 V / 1.08 V | 1 nF | 9.49 / 2.02 | 6.83 / 14.97 | 2.77 | 0.06 / 0.07 |
| LV | ss 125 C 3.0 V / 1.08 V | 1 nF | 8.55 / 1.22 | 7.98 / 15.85 | 2.77 | 0.05 / 0.05 |
| HV | ff -40 C 3.6 V / 1.32 V | 1 nF | 1.36 / 0.29 | 2.13 / 3.37 | 3.39 | 0.11 / 0.15 |
| LV | ff -40 C 3.6 V / 1.32 V | 1 nF | 1.21 / 0.15 | 2.44 / 3.54 | 3.39 | 0.06 / 0.09 |

## Reading the results

1. **Timing (a).** The pad edge time is set by the output stage (about 30 mA) and the load, not by the gate logic. 5 nF: 10-90 % rise 666 ns (tt), 990 ns (ss), 473 ns (ff);
   1 nF: 133, 198, 94 ns. Propagation delay `pwm` to pad 50 %: 241 to 250 ns (tt, 5 nF; rise 248 to 250 ns, fall 241 to 242 ns). The fall is 0.4 to 8.3 ns faster than the rise. Variants H and L differ by 2 ns or less at the pad.
2. **Shoot-through (b-i).** The pad driver is two separate gate drives (`ngate`, `pgate`, two shifters). With a 1 pF load the output stage draws up to 12.5 mA (tt),
   18.8 mA (ff), 7.1 mA (ss) from IOVDD on a falling edge, 15 to 24 pC per edge. These values include the two shifters inside the pad. With 1 nF and 5 nF the peak is 1.6 to 6.6 mA.
   On a rising edge the IOVSS current is below 2.2 mA (1 pF) and below 0.1 mA (1 nF, 5 nF). The cross-conduction is small against the 30 mA drive and against the load charge (15 nC for 5 nF).
   The model has no limit for this current. No limit was set.
3. **Skew (b-ii).** With three identical channels in the simulation, the delay spread between channels is at most 2 ps (ss, 5 nF). This is below the 50 ns dead time by a factor of 25000.
   Mismatch between channels is **not run**, so this number is a floor. The difference between the falling and the rising delay of one channel is 0.4 to 8.3 ns. It adds to the dead time
   (the fall is faster). The corner spread of the delay (tt 248 ns, ss 404 ns, ff 159 ns at 5 nF) is a bound for a chip-to-chip effect, not for channel to channel.
4. **Overlap (b-ii).** Three results for a/c against b with a 50 ns dead time:
   - at the logic mid-point (IOVDD/2), the gap is +49.8 to +58.8 ns for all cases: no overlap;
   - at 1 V (a FET threshold) the gap is **-160 to -277 ns with 5 nF**: the two gate voltages are above 1 V together for that time;
   - at 1 V with 1 nF the gap is -0.1 to +1.2 ns (tt, marginal), -13.6 to -14.3 ns (ss) and +7.5 to +9.4 ns (ff).
   Each gate here drives its own low-side FET, not one half bridge. Then an overlap between a and b does not cause shoot-through. If two of these pads ever drive a half bridge,
   the dead time of `r1_ctrl` (register `dead`) must be larger than 50 ns plus the loss shown in the table (up to 327 ns for 5 nF at ss).
5. **Simultaneous switching (c).** Three gates into 5 nF: peak IOVDD current 72 to 139 mA at tt/ss (1 nF decoupling), 220 mA at ff; mean 37 to 89 mA over the edge; charge 41 to 49 nC.
   IOVDD droop at the on-chip node: 30 to 115 mV with 1 nF decoupling and 38 to 200 mV with 100 pF (200 mV at ff, 3.6 V; 5.5 % of IOVDD). IOVSS bounce is 3 to 9 mV.
   The droop is mostly the 1 nH inductor of the single IOVDD pin. A smaller on-chip capacitor gives a larger droop and a lower peak current. Both variants give the same result within 9 % on the peak.
6. **Fault path (d).** `gate_en` falling to the pad below 0.33 V (10 % of 3.3 V):
   - 1 nF: 89 to 190 ns (passed, 200 ns requirement). At the FET-gate node after 10 ohm, ss needs 199.6 ns (variant L) and 201.0 ns (variant H): marginal;
   - **5 nF: 443 ns (ff), 612 ns (tt), 933 ns (ss): failed.** The pad sinks about 30 mA. The 200 ns requirement holds only for a gate capacitance below about
     1.06 nF (ss), 1.63 nF (tt) and 2.25 nF (ff) (linear interpolation between the 1 nF and 5 nF cases; an estimate, not a run).
   The gating path delay is not the limit: `gate_en` to `gc` is below 2.3 ns in variant H and 0.1 ns in variant L.

## Area and current estimates (estimates, not layout)

Area is estimated from the sum of W x L per cell, scaled by two known G1 layouts (`sim/area_est.py`, result `sim/results/area_est.json`). Low value: density of `g1_ls_up`
(9.2 x 11.7 um = 107.6 um2, 16.1 um2 of layout per um2 of gate area). High value: density of the placed G1 `g1_gate` macro (130.7 x 50.65 um, 81 um2 per um2 of gate area; sparse, with the latch and routing).

| Variant | Estimated area (um2) | Note |
| --- | --- | --- |
| L (3 x NAND2 + 3 x inverter, 1.2 V) | 69 to 348 | core standard-cell size; could also be done in the `r1_ctrl` RTL at no extra area |
| H (4 x `g1_lvlup`, 7 x `g1_hv_inv`, 3 x `g1_hv_nor2`, 3 x `g1_lvldn`) | 1135 to 5722 | the 4 `g1_lvlup` alone are about 320 to 430 um2 (80 um2 each at the low density; 107.6 um2 each if a `g1_ls_up` is used instead) |
| Pads | 3 x `sg13g2_IOPadOut30mA`, 80 x 180 um each (ring cells, not in this count) | `../r1_padring/README.md` |

Current (simulated; table (e) above and tables (c)):

- Static (1 nF cases; three pads and the gate path): IOVDD 0.3 to 9.5 nA with all gates low and 0.1 to 2.0 nA with all gates high. Core VDD 1.5 to 16 nA. The highest values are at ss/125 C.
- Dynamic: the load charge is C x V per rising edge per channel: 15 nC (5 nF, tt) and 3.1 nC (1 nF, tt). The mean IOVDD current is f x Q per channel. At 100 kHz and 5 nF that is 1.5 mA per channel, 4.5 mA for three. The PWM frequency of R1 is not fixed here.
- Core VDD charge per edge: 0.05 to 0.16 pC per edge for both variants (the logic is a small load).
- Energy drawn from IOVDD per rising edge per channel: Q x V = 15 nC x 3.3 V = 50 nJ at 5 nF (tt). Half of it is stored in the load, half is lost in the pad and the 10 ohm.

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| Does the pad contain its own core-to-IO shifter on `c2p`? | yes (read in `sg13g2_io.spi`) | section "Answer first" |
| (a) 10-90 % times and `pwm` to pad delay, 5 nF and 1 nF, tt / ss / ff, both variants | done, no limit was given (values only) | table (a); runs `g20261020b/*_pkg0_nodcn` |
| (b-i) Pad output-stage cross-conduction current reported | done (1 pF, 1 nF, 5 nF at three corners; peak 18.8 mA at 1 pF ff) | table (b-i) |
| (b-ii) Channel skew below dead time (50 ns) | passed: at most 2 ps, 3 identical channels (no mismatch) | table (b), run `g20261020b` |
| (b-ii) Channel skew with device mismatch | not run | - |
| (b-ii) Gate edges do not overlap at the logic mid-point | passed (gap +49.8 to +58.8 ns, all cases) | table (b) |
| (b-ii) Gate edges do not overlap at 1 V | **failed** for 5 nF (all corners) and for 1 nF at ss (-14 ns); at 1 nF tt about zero (-0.1 to +1.2 ns, marginal) and passed at ff (+7.5 to +9.4 ns). No shoot-through risk with separate low-side FETs | table (b) |
| (c) Simultaneous switching, peak and mean IOVDD current, bounce, package model, 5 nF | done; no limit given | table (c) |
| (c) Realistic on-chip decoupling value | not known: 1 nF and 100 pF assumed | - |
| (d) Fault path within 200 ns, 1 nF | passed at the pad (89 to 190 ns). At the FET-gate node, ss: 199.6 ns (L) and 201.0 ns (H), marginal | table (d) |
| (d) Fault path within 200 ns, 5 nF | **failed** at all corners (443 to 933 ns) | table (d) |
| Both variants (H and L) simulated and compared | done | all tables |
| Stock PDK pad model at 5 nF | **failed**: solver stall (4 runs); fixed with the `nodcn` copy | `sim/runs/g20261020a-stock/` |
| Power-up order (IOVDD before core), GATE state | not run in R1. G1 found that the pad holds `GATE` high for about 4 us when IOVDD comes first (board rule P1) | G1 README, `designs/g1-guardian/blocks/g1_top/README.md` |
| Single-event upset of the gating logic (H versus L) | not run | - |
| Real FET gate model (Miller charge, series gate resistor value) | not run (capacitor and 10 ohm stand-in) | - |
| Layout, DRC, antenna, LVS of both variants | passed (2026-10-21), see "Layout" at the end | `layout/runs/` |
| PEX, post-layout simulation | not run | - |
| Temperature -40 / 27 / 125 C only with the matching process corner | done; cross corners (for example ss/-40 C) not run | - |

## Open issues

1. **The 200 ns fault-path requirement fails for a 5 nF gate load.** The pad current limit sets the time. Options for the owner: (a) limit the total gate capacitance to about 1 nF;
   (b) relax the requirement to match 5 nF (about 0.95 us at ss); (c) add an external pull-down (outside this block). Decision needed. The 5 nF value is the G1 stand-in, not an R1 FET.
2. **Variant choice.** Variant L is simpler and smaller and gives the same pad behaviour. Variant H keeps thick-oxide gating logic for single-event robustness, as G1 did. Single-event robustness of either variant is not run.
   If variant L is chosen, the AND can be part of `r1_ctrl` (`gate_a = pwm_a & gate_en`), and then this block is only the three pads.
3. **IOVDD droop.** One IOVDD pin gives up to 200 mV droop (assumed 100 pF on chip, ff, 3.6 V) with three 5 nF loads. Check against the pad-ring decoupling in `r1_padring` and the number of IOVDD pins.
4. **Dead time.** With separate low-side FETs the overlap is harmless. The `dead` register must allow more than 50 ns plus the delay loss if a half bridge is driven later.
5. **`vdda` of variant H** is tied to IOVDD in the decks. A tie to the analog 3.3 V pin `VDDA` would put gate switching noise on the analog supply. Keep IOVDD.
6. Skew from mismatch is not run. The measured spread of 2 ps is a floor.

## Files

| File | Content |
| --- | --- |
| `schematic/r1_gate.spice` | the two top cells H and L |
| `schematic/g1_cells_copy.spice` | unchanged copy of the G1 `g1_gate.spice` (cells used) |
| `sim/run_gate.py`, `sim/analyze_gate.py` | deck generator, runner and waveform analysis (host python 3.6) |
| `sim/batch.sh` | the case matrix (27 cases) |
| `sim/make_nodcn.sh` | makes the pad file without `dantenna` (runs in the container) |
| `sim/make_tables.py`, `sim/results/g20261020b_tables.md` | table generator and tables |
| `sim/area_est.py`, `sim/results/area_est.json` | area estimate |
| `sim/finalize.py` | writes the `run.json` files |
| `sim/runs/g20261020b/<case>/metrics.json`, `run.json` | all numbers and the run record per case |
| `sim/runs/g20261020a-stock/<case>/run.json` | failed runs with the stock pad model |
| `<G1_RESULTS_ROOT>/r1_gate/g20261020b/<case>/` | deck, log, waveform (`wave.dat`, 288 MB in total for all cases) |

## Layout

Scope: the whole netlist of record `schematic/r1_gate.spice` (sha256 `a95a9a8c...`) is the on-chip part. It holds no pad device. The `sg13g2_IOPadOut30mA`
and its `dantenna` removal exist only in the simulation decks (`sim/make_nodcn.sh`), so no device leaves the block and the padring owns the pad.
The netlist has two top cells, and both are laid out. Variant H is `r1_gate_hv` (3.3 V domain AND, G1 style). Variant L is `r1_gate_lv` (1.2 V AND, 3 NAND2 + 3 inverters).
The choice between them is still open (see "Open issues" above). Recommendation L: then the AND can move into `r1_ctrl` and `r1_gate_lv` is not placed.

Source: the G1 generator `designs/g1-guardian/blocks/g1_gate/layout/g1_gate_layout.py` (sha256 `234302ef...`) with the G1 library
`g1_sense/layout/g1_layout_lib.py` (copied unchanged, sha256 `08412793...`), `fill_prep.py` (`f4823b17...`) and `spice2cdl.py` (`5d0b13c4...`). The G1 cell
generators (LV inverter and NAND2, LV cross-coupled PMOS pair, HV inverter and NOR2, `g1_lvlup` pull-downs and keepers, `g1_lvldn` pull-downs) and the
row, track and rail code are unchanged. Only the netlist part (which cells, in which order, with which nets) is new. There is no single G1 GDS to copy: the
R1 composition differs from `g1_gate`. G1 cell netlists: `schematic/g1_cells_copy.spice` (sha256 `846a55e0...`, equal to the G1 file).

Files in `layout/`:

| File | Content |
| --- | --- |
| `r1_gate_hv_filled.gds` | GDS of record, variant H, top cell `r1_gate_hv`, sha256 `861ec889fd70eb270f183a807e82442829bc18bedf01e3c0ec044664dc35e7b1`, 267 kB |
| `r1_gate_lv_filled.gds` | GDS of record, variant L, top cell `r1_gate_lv`, sha256 `a3dee0f091c5236f7b6ff231b765d0b70e60a6e791d9db0b12fd821ce44e013b`, 62 kB |
| `r1_gate_hv.gds`, `r1_gate_lv.gds` | generator output before the fill (`65791e14...`, `4a165022...`) |
| `r1_gate_hv.lef`, `r1_gate_lv.lef` | LEF (pins on Metal3, Metal1/Metal2 obstruction, Metal3 obstruction between the bars) |
| `r1_gate_hv_lvs.cdl`, `r1_gate_lv_lvs.cdl` | LVS references from `schematic/r1_gate.spice` and `g1_cells_copy.spice` by `make_lvs_cdl.py` |
| `r1_gate_layout.py` | generator (`-rd variant=hv` or `lv`) |
| `g1_layout_lib.py`, `fill_prep.py`, `spice2cdl.py` | G1 files, unchanged |
| `fill_r1_gate.sh`, `fill_r1_gate_hv.log`, `fill_r1_gate_lv.log` | PDK fill (G1 `fill.sh` method) and logs |
| `run_checks.sh`, `write_runjson.py`, `check_pins.py` | check flow |
| `runs/` | `run.json` of the runs (tags `hv-a`, `lv-a`) |

Built against: PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9, container image `sha256:ddeb6957...`, CPU set 100-102.

| Check (on the filled GDS) | Variant H `r1_gate_hv` | Variant L `r1_gate_lv` | Evidence |
| --- | --- | --- | --- |
| DRC, deep, `--no_density`, main + maximal tables | passed, 0 markers | passed, 0 markers | `layout/runs/layout-drc-{hv,lv}-a/run.json`, `<G1_RESULTS_ROOT>/r1_gate/layout-drc-{hv,lv}-a/` |
| Antenna, `--antenna_only` | passed, 0 markers | passed, 0 markers | `layout/runs/layout-ant-{hv,lv}-a/run.json` |
| LVS, deep, `--no_series_res`, against `r1_gate_<v>_lvs.cdl` | passed (25 HV PMOS, 31 HV NMOS, 10 LV PMOS, 4 LV NMOS; 42 nets) | passed (9 LV PMOS, 9 LV NMOS; 15 nets) | `layout/runs/layout-lvs-{hv,lv}-a/run.json`, `<G1_RESULTS_ROOT>/r1_gate/layout-lvs-{hv,lv}-a/` |
| Device counts against the netlist (hand count from the cell list) | equal | equal | - |
| Pin names equal the CDL ports | passed | passed | `layout/runs/layout-gen-{hv,lv}-a/check_pins.log` |
| Density | not run (waived at block level; chip level) | not run | - |
| PEX, post-layout simulation | not run | not run | - |

Area (`prBoundary` 189/4): variant H 126.00 x 49.05 um = 6180.3 um2 (G1 `g1_gate`: 130.68 x 50.65 um = 6619 um2). Variant L 28.39 x 27.90 um = 792.1 um2.
The estimate in "Area and current estimates" was 1135 to 5722 um2 (H) and 69 to 348 um2 (L). H is 8 % above the high estimate. L is 2.3 times above the high estimate:
5 Metal2 tracks, three bars, a guard ring and 2 um pin stubs set a floor that does not scale with the 6 cells.

Pins (all Metal3, `check_pins.log`). Inputs on the west edge: `pwm_a`, `pwm_b`, `pwm_c`, `gate_en` (0.5 um wide, 2 um long, 0.8 um pitch) and `vdd` (a 2 um stub at y 14.08..14.58).
Outputs on the east edge: `gc_a`, `gc_b`, `gc_c`. `vss` bar on the south edge (y 1.5..4.5), `vdda` bar on the north edge (H: y 44.55..47.55; L: y 23.4..26.4), both across the full width.
Variant L has no 3.3 V device. Its `vdda` bar is a bare pin with no connection, so that the pin list equals the netlist of record. The chip must not rely on it.
H pin y positions: `pwm_a/b/c`, `gate_en` 15.65..18.55; `gc_a/b/c` 24.45..27.35. L: inputs and outputs 15.65..18.55.

Differences between the G1 layout (`g1_gate`) and the R1 layout:

| Item | G1 `g1_gate` | R1 `r1_gate_hv` | R1 `r1_gate_lv` |
| --- | --- | --- | --- |
| Top cell | `g1_gate` | `r1_gate_hv` | `r1_gate_lv` |
| Inputs | `trip_d clr_d fast_en hard_cmp en_core` | `pwm_a pwm_b pwm_c gate_en` | same as H |
| Outputs | `gate_core fault_core tripped` | `gc_a gc_b gc_c` | same as H |
| `g1_lvlup` | 4 (`fast`, `trip_d`, `clr_d`, `en_core`) | 4 (`pwm_a/b/c`, `gate_en`) | 0 |
| 1.2 V `g1_lv_nand2` + `g1_lv_inv` (`fast_en & hard_cmp`) | 1 + 1 | 0 | 3 + 3 (the channel AND) |
| `g1_hv_nor2` | 5 (set, reset, 2 for the latch, gate) | 3 (one per channel) | 0 |
| `g1_hv_inv` (outside the `g1_lvlup`) | 4 | 7 (`en_hn`, 3 `p?_hn`, 3 `g?_hn`) | 0 |
| `g1_lvldn` | 3 (`gate`, `fault`, `tripped`) | 3 (`gc_a/b/c`) | 0 |
| SR latch, no-fill box over the latch | yes | no (the G1 latch is dropped in the netlist) | no |
| Devices | 78 | 70 | 18 |
| Outline | 130.68 x 50.65 um | 126.00 x 49.05 um | 28.39 x 27.90 um |
| Generator | `g1_gate_layout.py`, imports `g1_sense_layout.write_lef` | `write_lef` copied into the file, `variant` switch, output next to the script | same file; 3.3 V rows, TGO and 3.3 V rails not drawn; bare `vdda` bar added |
| Output location | `layout/` and `build/g1_gate_lay/` | `layout/` only | same |
| Fill scratch | `build/<macro>_fill` | `/tmp` in the container | same |

Open issues: (1) Variant choice (H, L, or the AND in `r1_ctrl`) is open; the unused GDS is then dropped. (2) No PEX and no post-layout simulation of either variant;
the simulated gate delay (schematic) excludes wiring. (3) Single-event robustness of H against L is not run (as before). (4) The G1 latch no-fill region is gone, and no other no-fill is drawn;
the fill inside the block is the PDK default. (5) `r1_gate_lv` carries a bare `vdda` pin; if variant L is placed, drop that bar or tie it at chip level.

Failures and mistakes:

| Class | What happened |
| --- | --- |
| spec-ambiguity | The brief spoke of a pad copy "without dantenna" that might sit in the block. The netlist of record has no pad device; the copy is a deck file. Nothing was removed from the layout. |
| verification-gap | The PDK LVS selects `IGNORE_TOP_PORTS_MISMATCH` by default. `check_pins.py` compares the LEF pins with the CDL ports. |
| planning | Both variants were laid out although the recommendation is L. The reason: the netlist of record has two top cells and the choice is open. Cost: one more generator branch and four more runs. |
