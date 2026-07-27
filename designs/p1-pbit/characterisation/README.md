# CMOS inverter switching threshold — characterisation

This is the CMOS proxy characterisation described in the
[design README](../README.md). It measures one parameter of one CMOS inverter:
the DC switching threshold V<sub>th</sub>, defined as the input voltage at which
V<sub>out</sub> = V<sub>DD</sub>/2.

**The inverter is not the p-bit.** P1's decision comparator is a SiGe HBT CML
latch. CMOS appears in P1 only in the output level-shifter and drivers that turn
the CML swing into a rail-to-rail 1.2 V logic signal. This work exists to bring up
the xschem → ngspice → CACE flow on IHP SG13G2, and to get a real number for how
far a CMOS trip point wanders over corner, supply and temperature — which is what
sets the minimum CML swing that buffer needs to see.

## Results

The full record, with the three nine-cell matrices and the spread analysis, is in
[`ihp_sg13g2_inv_characterization.md`](ihp_sg13g2_inv_characterization.md).

In short:

| Sizing | Offset at `mos_tt`, 1.20 V, 27 °C | Process spread at 1.20 V | Worst cell in the 3×3 supply matrix |
| --- | ---: | ---: | ---: |
| Baseline, W<sub>p</sub> = 2.000 µm | +18.312 mV | 11.172 mV | +22.267 mV |
| Nulled, W<sub>p</sub> = 1.414 µm | +0.017 mV | 3.568 mV | −6.847 mV |

Both use W<sub>n</sub> = 1.000 µm, L = 0.130 µm.

The 1.414 µm null holds at exactly one operating point. Over temperature at 1.20 V
in the typical corner it drifts from **+5.173 mV at −40 °C** through +0.017 mV at
27 °C to −1.602 mV at +125 °C. Sizing cancels a static offset; it does not cancel
the temperature dependence of mobility and V<sub>th0</sub>.

## Reproducing a number

Every value in the tables comes from a run directory here. Take the typical
corner at nominal supply, baseline sizing — the +18.312 mV figure:

```
runs/RUN_2026-07-27_11-58-48/parameters/switching_threshold/run_1/
  conditions.yaml      corner: mos_tt, vdd: '1.2'
  ihp_inv_dc_tb.spice  the elaborated testbench ngspice was handed
  ngspice_stdout.out   vth = 6.18312e-01   ... ngspice-46 done
  ihp_inv_dc_tb_1.data the extracted value
```

0.618312 V against a 0.600000 V target is +18.312 mV. The same structure holds for
every other cell.

Which run holds which matrix row:

| Run | Sizing | Sweep |
| --- | --- | --- |
| `RUN_2026-07-27_12-07-01` | W<sub>p</sub> = 2.000 µm | `mos_ss` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_11-58-48` | W<sub>p</sub> = 2.000 µm | `mos_tt` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_12-18-01` | W<sub>p</sub> = 2.000 µm | `mos_ff` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_12-37-10` | W<sub>p</sub> = 1.414 µm | `mos_ss` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_12-28-58` | W<sub>p</sub> = 1.414 µm | `mos_tt` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_12-37-29` | W<sub>p</sub> = 1.414 µm | `mos_ff` × {1.08, 1.20, 1.32} V |
| `RUN_2026-07-27_13-08-12` | W<sub>p</sub> = 1.414 µm | {`mos_ss`, `mos_tt`, `mos_ff`} × {−40, 27, 125} °C at 1.20 V |

All 27 points ran at 0.5 mV DC sweep resolution, with the MOS corner selected from
`$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib`.

## Caveat on the baseline matrix

`netlist/schematic/ihp_sg13g2_inv.spice` is the **nulled** DUT, W<sub>p</sub> =
1.414 µm. CACE testbenches pull the DUT in with `.include <path>`, so the run
directories for the three baseline runs record the corner and supply but not the
device width. The baseline netlist is the same file with `w=2.0u` on the PMOS line
in place of `w=1.414u`; it was not captured at the time and is not committed here
as though it had been. Re-running the baseline matrix against an explicitly
committed 2.0 µm netlist would close the gap.

## Layout

```
ihp_sg13g2_inv_characterization.md   the characterisation record and analysis
cace/ihp_sg13g2_inv.yaml             CACE datasheet spec (format 5.2)
cace/templates/ihp_inv_dc_tb.*       the parameterised DC testbench
xschem/ihp_sg13g2_inv.sch/.sym       inverter schematic and symbol
netlist/schematic/*.spice            extracted DUT netlist (nulled sizing)
docs/*.svg                           rendered schematic and symbol
runs/                                the seven CACE runs the tables cite
```

Each published run keeps `summary.md`, the per-parameter
`simulation_summary.md`/`.csv`, and per condition the `conditions.yaml`,
the elaborated `ihp_inv_dc_tb.spice`, `ngspice_stdout.out` and the `.data` file.
Dropped from each run: the xschem stdout/stderr logs, the copied schematic and
symbol, and CACE's `flow.log`/`warning.log`/`error.log` — none of which carry a
number the tables depend on.

Absolute paths from the machine the runs happened on have been rewritten to be
relative to the design root, or to `$PDK_ROOT/`. Nothing else in these files has
been altered.
