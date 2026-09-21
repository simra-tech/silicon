# KLayout LVS deck vs the PDK IO library — reference runs

Question: can the PDK KLayout LVS deck (`libs.tech/klayout/tech/lvs/run_lvs.py`,
PDK `8437402`, KLayout 0.30.9) verify a ring built from `sg13g2_io` cells?
Test: each stock IO cell from `libs.ref/sg13g2_io/gds/sg13g2_io.gds` against
its own subcircuit in `libs.ref/sg13g2_io/cdl/sg13g2_io.cdl` (flat mode, default
simplification incl. device combination, `--top_lvl_pins`).

| Cell | Outcome | Cause (from the cross reference `xref_bare_<cell>.txt` and the extracted netlist) |
| --- | --- | --- |
| `sg13g2_Filler200` | **fail** (2 s) | layout extracts four `ptap1` devices on three unconnected `iovss` rail pieces plus `vss`; the CDL has two lumped `ptap1` on `iovss`/`vss` and pins `vdd`, `iovdd` that touch no device. The rails are only joined by abutment at ring level, so no IO cell can pass a cell-level LVS |
| `sg13g2_IOPadAnalog` | **fail** (26 s) | the `rppd` series resistor of `sg13g2_SecondaryProtection` (CDL `RR0 pad core 586.899 rppd`) is not extracted: layout net carries the labels `pad` and `padres` together (`I3.R0` missing), diodes `I3.D1`, `I5.D1`, `I3.D0` unmatched, `PADRES` and the `SUB!` nets unmatched |
| `sg13g2_IOPadIn` | **fail** (25 s) | same pattern: `I0.I0.R0` (rppd) and `I0.P0` missing in the layout netlist, diodes unmatched |
| `sg13g2_IOPadVdd` | **fail** (40 s) | as above |

Consequence: at this PDK commit the KLayout LVS deck does not reproduce the PDK's
own IO CDL from the PDK's own IO GDS, so a full-chip KLayout LVS containing
these cells cannot report a match whatever the ring wiring is. The full-chip
runs (`../run-1200*/lvs_klayout_*`) fail inside these cells, as expected.

Direct check of the `padbare` question (`padbare_conductor.py`, log
`padbare_conductor.log`): KLayout `LayoutToNetlist` on the stock
`sg13g2_IOPadAnalog` with Metal1…TopMetal2 and all vias connected. The
die-side `pad` stub (TopMetal2, y = 0–3) and the core-side strip renamed
`padbare` (Metal3, y = 179.71–180) are **one net (cluster 1)**; the `padres`
strip is a different net (cluster 33). Renaming the strip in the LEF changes
no conductor; `pad` and `padbare` are the same node, `padres` is behind the
resistor.
