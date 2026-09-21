# Antenna deck: reference runs

Question: are the `Ant.e` markers on the three `sg13g2_IOPadIn` cells of the G1
ring a layout problem or a deck/library artefact? Same deck
(`libs.tech/klayout/tech/drc/rule_decks/antenna.drc`, PDK `8437402`), KLayout
0.30.9, run as `klayout -b -zz -r antenna.drc -rd input=… -rd topcell=… -rd report=…`.

| Run | Input | IOPadIn revision | Items | Files |
| --- | --- | --- | --- | --- |
| G1 ring, 1200 µm frame | ring-1200 final GDS (sha256 `f04ba54d…`) | PDK `8437402` ("I/O Update 2") | 9 (`Ant.e_Metal5/TopMetal1/TopMetal2`, 3 IOPadIn) | `../run-1200/antenna.klayout.*` |
| G1 ring, 1130 µm frame | ring final GDS | PDK `8437402` | 6 (`Ant.e_TopMetal1/2`) | `../run-1130/antenna.klayout.*` |
| G1 ring, bondpads deleted | 1130 frame | PDK `8437402` | 6 | `../run-1130/ant__chip_without_bondpads.lyrdb` |
| Bare `sg13g2_IOPadIn` cell | PDK `sg13g2_io.gds` | PDK `8437402` | 0 | `../run-1130/ant__bare_iopadin.*` |
| Reference: iic-jku ams-chip-template final chip (1600 µm die, 3 `sg13g2_IOPadIn`, same deck) | `layout/chip_top.gds.gz` of commit `6524ffdd` | template's `ip/sg13g2_io_custom/gds` (older PDK revision) | **0** | `template_chip_top_antenna.*` |
| **G1 ring with only `sg13g2_IOPadIn` swapped for the template's cell** (`swap_iopadin.py`) | ring-1200 final GDS, cell contents replaced | older revision | **0** | `g1_1200_oldIOPadIn_antenna.*` |

Cell difference (`xor_iopadin.py`, `xor_and_trace_iopadin.log`): the two
`sg13g2_IOPadIn` revisions differ only in the input-receiver region
(x = 40–52, y = 140–167 µm): Activ 4, GatPoly 6, Cont 62, Metal1 16 XOR
polygons; `sg13g2_IOPadAnalog` and `sg13g2_Corner` are identical,
`sg13g2_IOPadVdd` differs in contacts only. In the current revision the gate at
(41.5–42.0, 161.4–166.7) is contacted to Metal1 that runs into the cell's `vdd`
rail (Metal3 → TopMetal1, traced in `trace_tmpl.py`), so the deck attributes
the whole ring's `vdd` rail area to that gate and the ratio grows with the
perimeter (24 503 µm² at 1130 µm, 27 624 µm² at 1200 µm; limit 20 000 with
diode).

Conclusion: deck/library interaction introduced with the `sg13g2_IOPadIn`
revision in this PDK commit, not a defect of the G1 layout; the identical ring
with the previous cell revision is clean. The question for the foundry: is a
gate tied to a supply rail exempt from Ant.e (the deck has no such exemption),
or should the cell carry a protection structure?
