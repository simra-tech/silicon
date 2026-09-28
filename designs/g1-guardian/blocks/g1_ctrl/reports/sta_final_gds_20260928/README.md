# Timing of the final GDS (r4), 2026-09-28

Post-submission campaign, track T3. Every number here is **simulated**: static timing analysis
(OpenSTA) plus one ngspice run for the oscillator output stage. Nothing was measured.

## What this covers

This is the static timing of the digital paths of the chip of record,
`blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` (`225d0b53…`, top `g1_chip_top`). The submitted
`SoC1816.gds` has the same geometry. The run uses:

- **The macro as it is in the GDS.** That is the ECO `g1_digital` macro: gate netlist `4b83f181…`
  and its own nominal SPEF `0b626c7f…`. The r4 sign-off shows that this macro is byte-identical
  in r3 and r4 (`../../../g1_padring/reports/signoff-1414r4-20260927/digital_identity/`).
- **The connectivity of the final chip.** The top-level netlist is generated from the canonical
  CDL of record, `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl` (`e060c0c5…`), which passed
  the projected LVS against the GDS.
- **The top-level routes of the final GDS.** Per-net R and C come from track T1's r4
  top-interconnect view (`${BULK}/postsub-20260928/pex/top_rc_nets.json`, `7672d6db…`). T1
  extracted them with kpex 0.3.12 2.5D CC on the fill-free r4 GDS. R comes from the kpex sheet and
  via tables, both as a series upper bound and as the pin-to-pin value from KLayout's RNetExtractor.
  The pad-side pin-stack and bondpad C come from the same view (`top_interconnect_r4_summary.json`,
  `82e36de0…`). These annotations replace the routed signal netlist of the superseded 1350 µm
  LibreLane assembly (`final_signal.nom.spef`). The r3 sign-off STA ("setup slow 25.70 ns in
  chip") and every earlier chip-context STA were timed with that netlist.
- **The real pad and SDC models.** The pads use the PDK's stock `sg13g2_io` liberty, and the
  constraints are the SDC of record `blocks/g1_padring/flow/g1_chip_top.sdc` (`bb006e96…`,
  unchanged).

The campaign brief names `blocks/g1_ctrl/layout/g1_digital.nom.spef` as the macro SPEF. That file
is the historical run7 SPEF (`42dbd018…`, `layout/SHA256SUMS`), not the ECO macro in the GDS. It
was therefore **not** used. The ECO views were copied from the r3 run root
`${BULK}/digital-eco-r3cand2-20260926/final/` after `sha256sum -c final_views.sha256` passed. They
are bulk only, and their hashes are in the "Built against" table.

## Built against

| Item | Version / hash | How established |
| --- | --- | --- |
| GDS of record | `g1_chip_top_1414_r4.gds` `225d0b535321ed31…` | `sha256sum` |
| CDL (connectivity) | `g1_chip_top_1414_r4.cdl` `e060c0c59a168e5b…` | `sha256sum`; recorded in `inputs/nets.json` |
| Macro gate netlist / SPEF | `4b83f1812af385d2…` / `0b626c7fb186f0da…` (ECO, r3 = r4) | `sha256sum -c` against the r3 run's `final_views.sha256` |
| Top-level route RC | T1 `top_rc_nets.json` `7672d6db0cc04750…`, `top_interconnect_r4_summary.json` `82e36de05bc236d4…` | `sha256sum`; recorded in `annotation/top_*.json` |
| SDC | `g1_chip_top.sdc` `bb006e9680938e9a…` (chip), `g1_digital.sdc` `c36bf030…` (macro case) | `sha256sum`, unchanged since the 24 Sep record |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; `sg13g2_stdcell_{fast_1p32V_m40C,typ_1p20V_25C,slow_1p08V_125C}.lib`, `sg13g2_io_{fast_1p32V_3p6V_m40C,typ_1p2V_3p3V_25C,slow_1p08V_3p0V_125C}.lib` (io typ `85d56d20…`) | `flow/run.sh` commit check; `sha256sum` in the container |
| OpenSTA | 3.1.0 | `sta -version` in the container |
| ngspice | 46 (PSP 103 OSDI of the PDK) | `ngspice -v` |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image identity check |
| CPUs | 97-100 (`taskset` through `flow/run.sh`, `G1_CPUSET`) | campaign allocation |

## Method

1. **Top netlist** (`make_sta_inputs.py` → `inputs/g1_chip_top_sta.v`, `nets.json`). The script
   walks `.SUBCKT g1_chip_top` of the CDL and emits:
   - the IO pads with their stock `sg13g2_io` cell names (`pad`, `p2c`, `c2p`, `padres`);
   - `\i_core.u_digital` (the ECO macro), the `por_n` tie cell and the six top-level `sg13g2_antennanp`
     diodes;
   - stub cells for the analog blocks that touch a digital net (OSC, TRIP, GATE, three `g1_ls_up`,
     T2F, BGR `r4`).

   The net names are the CDL's, which are also the labels of T1's view. Decap, fill and tap cells,
   supply and corner or filler IO cells, bondpads, SENSE, DOSE and DUT are left out; they carry no
   digital signal.
2. **Analog stubs** (`inputs/g1_analog_stubs.lib`). A stub has digital pins only and no timing arcs,
   because none of these blocks has a timing model. The input capacitance of each pin is estimated
   from the gate area of every MOS gate on it, over the block's whole CDL sub-hierarchy. Thin oxide
   uses 11.86 fF/µm², calibrated on `sg13g2_inv_1` pin A. Thick oxide uses that value scaled by the
   oxide thickness ratio in the process spec (4.09 fF/µm²). The estimate is ±50 %, and the values
   are 5–34 fF per pin (`inputs/stub_pin_caps.json`). They are small next to the 12–270 fF routes.
3. **Route annotation** (`make_top_spef.py` → `annotation/top_p2p.spef`, the record case). Each net
   is a star. Its centre is the reference pin of the extraction, normally the macro pin. Every other
   pin hangs on the centre through its pin-to-pin R. Half of the net C sits on the centre and the
   rest is spread over the other pins. C is kpex C_total (ground + coupling to other routed nets,
   **coupling grounded, Miller factor 1**) plus the IO pin-stack fragments. The pad-side port nets
   get the bondpad + pin-stack C (125.7 fF). `annotation/top_ub.spef` (sensitivity) puts the series
   upper-bound R in front of every load instead. The macro-internal parasitics come from the
   macro's own SPEF (`read_spef -path i_core.u_digital`). All RC is nominal; no RC corner exists.
4. **STA** (`sta_final.tcl`, `run_sta_final.sh`, `run_all.sh`). The runs cover three corners
   (stdcell fast 1.32 V −40 °C / typ 1.20 V 25 °C / slow 1.08 V 125 °C, each with the matching io
   liberty) and seven cases:

   | Case | What changes against `chip_p2p` |
   | --- | --- |
   | `chip_p2p` | nothing: this is **the record case**, with the SDC of record unchanged |
   | `chip_ub` | series upper-bound R on every load |
   | `chip_p2p_oscedge` | the simulated oscillator edge is assigned at the osc_clk root (`set_assigned_transition`), plus the simulated source latency (step 5) |
   | `chip_p2p_sclkport` | SCLK clock defined at the `SCLK` port, so the input-pad delay is inside the clock path; the SDC of record defines it at `pad14_sclk/p2c` |
   | `chip_p2p_board10pF`, `chip_p2p_board15pF` | external load of 10 / 15 pF on the output pad ports (see finding 4) |
   | `macro` | macro alone, macro sign-off SDC |
5. **osc_clk upstream of the macro** (`osc_clk_stage.py`, ngspice). The oscillator has no liberty,
   and the SDC starts the clock at the macro's root buffer `clkbuf_0_osc_clk/A`. So the SDC's
   0.3 ns clock transition is not what the STA sees: with an ideal driver, OpenSTA computes about
   0.09 ns at that pin. The stage from the oscillator's latch output `q` to that pin was therefore
   simulated at transistor level:
   - the two `g1_osc_inv` output inverters of the CDL (lv PMOS 1/0.13 µm, NMOS 0.5/0.13 µm);
   - the extracted top route as a pi (414.7 Ω, 145.0 fF);
   - the macro-internal port wire as a second pi (300.9 Ω, 35.6 fF, from the macro SPEF);
   - `sg13g2_buf_16` with its 38 fF load.

   It ran with the tt / ss / ff PDK model sections at 1.20 V 25 °C / 1.08 V 125 °C / 1.32 V −40 °C.
   There is **no level shifter on osc_clk**: the oscillator is a 1.2 V block, and the `g1_ls_up`
   level shifters sit only on `t2f_en`, `t2f_mode` and `bgr_r4`.

Commands, from the repository root. `BULK` in `run_all.sh` is the track's results root,
`${BULK}/postsub-20260928/timing`:

```sh
R=${BULK}/postsub-20260928/timing; H=designs/g1-guardian/blocks/g1_ctrl/reports/sta_final_gds_20260928
python3 $H/make_sta_inputs.py --cdl designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl --out $R/inputs
for m in p2p ub; do python3 $H/make_top_spef.py --nets $R/inputs/nets.json --rc $R/rc_r4/top_rc_nets.json \
  --aux $R/rc_r4/top_interconnect_r4_summary.json --model $m --out $R/rc_r4/top_$m.spef --report $R/rc_r4/top_$m.json; done
G1_CPUSET=99 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=$R flow/run.sh \
  python3 /work/$H/osc_clk_stage.py 414.681 145.034 300.885 35.6174 $R/osc_r4
BULK=$R $H/run_all.sh                      # 18 runs on CPUs 97-100
MACRO_NL=$R/eco_views/g1_digital.nl.v MACRO_SPEF=$R/eco_views/g1_digital.nom.spef INPUTS=$R/inputs PIN_SLEWS=1 \
  TOP_SPEF=$R/rc_r4/top_p2p.spef BOARD_LOAD_PF=10 $H/run_sta_final.sh chip <fast|typ|slow> <cpu> $R $R/final/chip_p2p_board10pF-<corner>
python3 $H/summarize.py $R/final $R/summary
```

Each STA run takes about 1–2 min on one CPU. All 21 completed (`STA_FINAL_COMPLETE` in every log).
Two earlier attempts (`final_attempt1`, `final_attempt2`, bulk only) were superseded for these
reasons:
- the first had no assigned osc edge;
- in the second, a script was edited during the batch and two runs ended with rc 127.

## Results

### Setup and hold, all cases (worst slack, ns)

| Case | Corner | Worst setup | Worst hold | Setup / hold violations | Setup SCLK / osc_clk / async | Hold SCLK / osc_clk / async | Registers SCLK / osc_clk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **chip_p2p** | fast | **27.874** | **+0.114** | 0 / 0 | 27.874 / 97.011 / 97.661 | 0.114 / 0.122 / 0.246 | 52 / 1170 |
| **chip_p2p** | typ | **27.053** | **+0.195** | 0 / 0 | 27.052 / 95.681 / 96.628 | 0.195 / 0.212 / 0.410 | 52 / 1170 |
| **chip_p2p** | slow | **25.381** | **+0.337** | 0 / 0 | 25.381 / 93.372 / 94.953 | 0.338 / 0.374 / 0.696 | 52 / 1170 |
| chip_ub | fast / typ / slow | 27.874 / 27.052 / 25.381 | +0.114 / +0.195 / +0.337 | 0 / 0 | as chip_p2p | as chip_p2p | 52 / 1170 |
| chip_p2p_oscedge | fast / typ / slow | 27.874 / 27.053 / 25.381 | +0.114 / +0.195 / +0.337 | 0 / 0 | osc_clk 97.011 / 95.681 / 93.373 | as chip_p2p | 52 / 1170 |
| chip_p2p_sclkport | fast / typ / slow | 27.680 / 26.780 / 24.950 | +0.114 / +0.195 / +0.337 | 0 / 0 | SCLK 27.680 / 26.780 / 24.950 | as chip_p2p | 52 / 1170 |
| chip_p2p_board10pF | fast / typ / slow | 24.855 / 22.721 / 18.725 | +0.114 / +0.195 / +0.337 | 0 / 0 | SCLK 24.855 / 22.721 / 18.725 | as chip_p2p | 52 / 1170 |
| chip_p2p_board15pF | fast / typ / slow | 23.350 / 20.561 / 15.402 | +0.114 / +0.195 / +0.337 | 0 / 0 | SCLK 23.350 / 20.561 / 15.402 | as chip_p2p | 52 / 1170 |
| macro | fast | 29.044 | +0.114 | 0 / 0 | 29.044 / 76.918 / 97.660 | 0.114 / 0.122 / 0.246 | 52 / 1170 |
| macro | typ | 28.821 | +0.195 | 0 / 0 | 28.821 / 75.608 / 96.628 | 0.195 / 0.212 / 0.410 | 52 / 1170 |
| macro | slow | 28.447 | +0.337 | 0 / 0 | 28.447 / 73.376 / 94.953 | 0.338 / 0.374 / 0.696 | 52 / 1170 |

All registers are clocked: 52 SCLK + 1170 osc_clk = 1222, the same count as the macro. The macro
case reproduces the r3 macro sign-off exactly (29.044 / 28.821 / 28.447, hold 0.114 / 0.195 /
0.337). The worst setup in the chip is always the SDO output path. The launch is on the falling
SCLK edge; the path goes through `output34` (`sg13g2_buf_1`), the 549 µm `i_core_sdo_o` route and
`pad16_sdo` (`sg13g2_IOPadOut4mA`), and ends against the SDC's 20 ns output delay. The worst hold is
inside the macro, and the top-level routes do not change it. In the macro case the osc_clk setup
group is lower (73–77 ns) because the macro SDC puts a 20 ns output delay on the macro outputs. The
chip SDC leaves them unconstrained, because they end at analog blocks.

### Comparison with the macro-only and the earlier in-chip numbers

| Worst setup (ns) | fast | typ | slow | Worst hold (ns) | fast | typ | slow |
| --- | --- | --- | --- | --- | --- | --- | --- |
| macro only (r3 sign-off; reproduced here) | 29.044 | 28.821 | 28.447 | | 0.114 | 0.195 | 0.337 |
| in chip, r3 sign-off (1350 µm routed signal netlist, not this chip's routes) | 27.988 | 27.248 | **25.704** | | 0.114 | 0.195 | 0.337 |
| **in chip, final GDS r4 (this record)** | **27.874** | **27.053** | **25.381** | | **0.114** | **0.195** | **0.337** |
| difference, final GDS − r3 sign-off in chip | −0.114 | −0.195 | −0.323 | | 0 | 0 | 0 |

The final GDS costs 0.11–0.32 ns of SDO setup margin against the earlier in-chip figure. The
reasons are:
- the r4 `sdo_o` route with its pin stack (81.8 fF, against about 60 fF in the 1350 netlist): at
  slow, `output34` sees 124 fF instead of 98 fF, and its output slew is 0.78 ns instead of 0.62 ns;
- the pad-side pin-stack and bondpad C (125.7 fF) on the SDO port: at slow, the pad delay is
  2.57 ns instead of 2.39 ns.

The margin is still 25.4 ns in a 100 ns period.

### Pad paths (chip_p2p)

| Path | fast | typ | slow |
| --- | --- | --- | --- |
| SDO: SCLK fall → `pad16_sdo/pad` → port, setup slack (ns) | 27.874 | 27.053 | 25.381 |
| SDI: port → `pad15_sdi/p2c` → macro flop, hold slack (ns; SDC min input delay 2.0 ns) | 2.062 | 2.123 | 2.265 |
| SDI: setup slack (ns) | 79.209 | 79.054 | 78.759 |
| EN | false path by the SDC (asynchronous reset, synchronised in the macro) | | |
| GATE, FAULT_N, TEMP_OUT | not timed: driven by G1_GATE / G1_T2F, which have no timing model | | |

### Clocks

| Clock | fast | typ | slow |
| --- | --- | --- | --- |
| SCLK, `pad14_sclk/p2c` → register CK, min–max (ns) | 0.269–0.324 | 0.374–0.450 | 0.559–0.676 |
| SCLK, `SCLK` port → register CK (sclkport case) | 0.463–0.535 | 0.645–0.756 | 0.988–1.147 |
| osc_clk, root pin → register CK, ideal-driver edge at the root (record case) | 0.264–0.351 | 0.374–0.489 | 0.562–0.724 |
| osc_clk, latch output `q` → register CK, simulated edge and source latency (oscedge case) | 1.323–1.490 | 1.985–2.186 | 3.041–3.510 |
| osc_clk skew (ideal / simulated edge) | 0.079 / 0.078 | 0.102 / 0.101 | 0.148 / 0.147 |

osc_clk upstream stage, ngspice (`osc/osc_clk_stage.json`; the "no route" row has the inverters on
the buffer pin directly):

| Quantity (ns) | fast | typ | slow |
| --- | --- | --- | --- |
| `q` → `clkbuf_0_osc_clk/A`, rise / fall (with route) | 0.485 / 0.528 | 0.723 / 0.767 | 1.086 / 1.235 |
| 20–80 % transition at `clkbuf_0_osc_clk/A`, rise / fall (with route) | 0.620 / 0.659 | 0.940 / 0.948 | **1.426 / 1.560** |
| same, no route | 0.068 / 0.069 | 0.097 / 0.089 | 0.134 / 0.135 |

The oscillator edge adds a common latency of about 1–2.8 ns. It does not change skew (0.001 ns) or
any slack by more than 0.001 ns. osc_clk has one source, and every crossing out of its domain is
declared asynchronous.

### Slew and capacitance at the pads and on the top-level nets (chip_p2p)

`runs/chip_p2p-<corner>/top_net_pins.tsv` holds the slew at every leaf pin of every top-level net,
and `results/net_table.md` holds the per-net summary. The worst values:

| Pin / net | fast | typ | slow | Limit |
| --- | --- | --- | --- | --- |
| `pad16_sdo/c2p` (macro `output34` over the 72 Ω / 81.8 fF route), rise / fall (ns) | 0.450 / 0.377 | 0.685 / 0.533 | 1.038 / 0.856 | 2.5 (io liberty c2p); 1.5 (macro design limit) |
| `i_core.u_trip/clk` (`cmp_clk`, 280 Ω / 122.5 fF) | 0.429 / 0.350 | 0.662 / 0.509 | 1.014 / 0.832 | TRIP: no timing model; 1.5 (macro) |
| worst DAC code input at TRIP (`dac_hard_0`, 210 Ω / 144.6 fF) | 0.411 | 0.636 | 0.977 | as above |
| worst OSC trim input (`osc_trim_3`, 246 Ω / 132.1 fF) | 0.393 | 0.609 | 0.935 | as above |
| `pad14_sclk/p2c` / `pad15_sdi/p2c` / `pad12_en/p2c` | 0.245 / 0.207 / 0.170 | 0.372 / 0.319 / 0.258 | 0.565 / 0.492 / 0.397 | p2c max_capacitance 0.24 pF: loads 0.213 / 0.180 / 0.141 pF (slow), passed |
| `pad16_sdo/pad` with the SDC load (6 fF + 125.7 fF pad metal) | 0.260 / 0.229 | 0.370 / 0.330 | 0.575 / 0.532 | 3.5 (io liberty default) |
| osc_clk root `clkbuf_0_osc_clk/A`, simulated | 0.659 | 0.948 | **1.560** | 2.5074 (stdcell liberty); **1.5 (macro design limit)** |

`report_check_types` reports **0 max-capacitance and 0 max-fanout violations in all three corners**.
It reports 10 max-slew flags per corner, and all 10 are analog pads: `pad` of SENSE_P/N, TRIP_SET,
VREF, G_SHARED, D_STD, D_ELT and HBT_E/B/C. They report 200 ns against 3.5 ns because the
`sg13g2_IOPadAnalog` liberty uses constant placeholder tables. This is the same disposition as the
24 Sep record, which had 12 flags; VDDA and the `padbare` view are not in this netlist. None of
the flags is on a digital net.

## Findings

1. **Setup and hold pass with the parasitics of the final GDS**, with margin, in every corner and
   every variant. The record case has worst setup 25.381 ns (SDO, slow) and worst hold +0.114 ns
   (inside the macro, fast). There are no violations.
2. **osc_clk edge at the macro root.** The oscillator's small output inverter (lv NMOS 0.5 µm)
   drives 181 fF of route and port wire. At slow (ss, 1.08 V, 125 °C) this gives a simulated fall
   transition of 1.56 ns at `clkbuf_0_osc_clk/A`. That is above the macro's 1.5 ns design
   `set_max_transition`, and below the 2.51 ns liberty limit of `sg13g2_buf_16`. With that edge
   assigned in STA, no slack changes by more than 1 ps. The effect is a common insertion of up to
   3.5 ns. **Failed against the macro design limit (simulated); timing impact none.**

   The OSC qualification estimated the root route at 459.8 Ω / 60.4 fF. The extracted values are
   414.7 Ω / 145.0 fF on top plus 300.9 Ω / 35.6 fF inside the macro. The inverter is outside the
   oscillation loop, so the frequency effect is expected to be small, but it was **not simulated**
   here.
3. **Top-level route RC equals the 25 Sep r1-view values.** T1's r4 extraction gives the same per-net
   R and C as `blocks/g1_top/sim/postlayout/top_interconnect_20260925_summary.json` on all 57
   routed nets. The TRIP change of r4 did not move a top-level route.
4. **The SDC of record models a 6 fF external load, not 6 pF.** `OUTPUT_CAP_LOAD 6.0` is divided by
   1000 into pF, as in LibreLane. The 24 Sep README's "6 pF load" is therefore a misreading; the
   earlier numbers were also timed with 6 fF. With a board load the SDO setup slack stays positive:
   - 10 pF: 18.73 ns (slow);
   - 15 pF: 15.40 ns.

   The pad output slew then exceeds the io library's 3.5 ns default: 6.5–14.4 ns at 10 pF for
   SDO/FAULT_N, and TEMP_OUT at slow. 15 pF exceeds the `sg13g2_IOPadOut4mA` max_capacitance of
   12 pF, so the 15 pF numbers are extrapolated beyond the liberty table.
5. **Clock at the pad port.** Moving the SCLK clock definition to the port, so that the input pad
   delay is inside the clock path, lowers SDO setup by 0.19–0.43 ns (24.950 ns slow). The SDC of
   record starts SCLK at `pad14_sclk/p2c`.
6. **The earlier "98 unannotated drivers" are down to 62**, and none is a digital top-level net:
   - 53 are the macro's CTS dummy-load outputs `clkload*`, the same as the macro alone;
   - 9 are the unconnected `padres` pins of the analog pads, which have no core connection in the
     CDL (`_nc*`);
   - there are 0 partially annotated drivers.

   Every routed digital net carries the extracted RC.

## Status

| Check | Status |
| --- | --- |
| Setup / hold, final-GDS routes (star, pin-to-pin R), merged SDC of record, 3 corners | **passed** (0 / 0 violations) |
| Same with the series upper-bound R (`chip_ub`) | passed |
| Same with the simulated oscillator edge and latency (`chip_p2p_oscedge`) | passed |
| Same with SCLK at the port (`chip_p2p_sclkport`) | passed |
| Same with 10 / 15 pF external load on the output pads | passed (setup / hold); 15 pF is outside the 4 mA pad liberty (max_capacitance 12 pF) |
| Clock coverage (52 SCLK + 1170 osc_clk registers) | passed |
| Max capacitance, max fanout | passed (0 / 0, every corner) |
| Max slew, digital nets and pads (SDC load) | passed (worst 1.04 ns at `pad16_sdo/c2p`, slow) |
| Max slew, analog pads | failed: 10 per corner, `sg13g2_IOPadAnalog` placeholder liberty (dispositioned, not waived) |
| Max slew at the output pads with 10 pF board load | failed: SDO / FAULT_N 6.5–14.4 ns against the io default 3.5 ns (external edge rate; informative) |
| osc_clk root transition against the macro's 1.5 ns design limit (ngspice) | failed at slow (1.56 ns fall); passed at fast and typ; the liberty limit 2.51 ns passed |
| Parasitic annotation | failed: 62 unannotated drivers (53 CTS dummy loads, 9 unconnected analog-pad `padres`), none on a digital net (dispositioned) |
| Unconstrained endpoints | 4 macro flops (the first synchroniser stages of `cmp_soft`, `cmp_hard`, `tripped` and one more, as in the r3 sign-off) + 16 ports (false paths or blocks without timing model); by design |
| Min / max RC corners of the routes and of the macro SPEF | **not run**: only the nominal extraction exists |
| Signal integrity (crosstalk delay, glitch); coupling is grounded with Miller factor 1 | **not run** |
| Timing of the analog-driven nets (`cmp_soft`, `cmp_hard`, `tripped`, GATE, FAULT_N, TEMP_OUT) | **not run**: no timing models; their slews here assume an ideal driver. Asynchronous inputs are synchronised (false paths) |
| Route C with fill, and route-to-macro-internal coupling | **not run**: T1's view is fill-free and sees the macros as black boxes |
| Synchroniser MTBF | **not run** |
| Oscillator frequency with the extracted output load | **not run** |
| Board-level SCLK/SDI/SDO timing budget (host, cable) | not applicable here (bench plan) |

## Files

- Scripts:
  - `make_sta_inputs.py`: CDL → STA netlist, analog stubs and net map;
  - `make_top_spef.py`: T1 RC → SPEF;
  - `sta_final.tcl` and `run_sta_final.sh`: one STA run;
  - `run_all.sh`: the batch;
  - `osc_clk_stage.py`: ngspice for the osc_clk upstream stage;
  - `summarize.py`: tables.
- `inputs/`: `g1_chip_top_sta.v`, `g1_analog_stubs.lib`, `nets.json`, `stub_pin_caps.json`.
- `annotation/`: `top_p2p.spef` (record) and `top_ub.spef`. Their reports `top_p2p.json` and
  `top_ub.json` give R to every pin, C per net and the input hashes.
- `osc/`: `osc_clk_stage.json` and the six ngspice decks.
- `results/`: `results.json` (every run, parsed), `tables.md`, `net_table.md`.
- `runs/<case>-<corner>/`: summary, per-group slacks, violators, DRV, annotation, coverage, clock
  latency and skew for all 21 runs. For `chip_p2p` there are also the full worst paths, the SDO/SDI
  paths, `nets_all.rpt`, `top_net_pins.tsv` and `sta.log`.
- `SHA256SUMS`: every file in this directory except itself and this README.

The bulk run directories, the ECO views copy and T1's inputs are in `${BULK}/postsub-20260928/timing/`
(`${BULK}` = the external artefact root, as in the earlier records).
