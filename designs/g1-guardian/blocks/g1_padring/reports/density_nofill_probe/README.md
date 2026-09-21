# Density probe: does the PDK filler honour no-fill layers placed at chip level?

Question: can the block owners keep chip-level fill away from their matched
arrays and capacitors with no-fill shapes in the block GDS, and let the chip
flow fill everything else inside the macros?

PDK facts (`libs.tech/klayout/tech/macros/sg13g2_filler_{ActGatP,Metal,TopMetal}.lym`,
`sg13g2.lyp`): every fill macro subtracts `<layer>.nofill` = GDS datatype 23 of
the drawing layer — `Activ 1/23`, `GatPoly 5/23`, `Metal1 8/23`, `Metal2 10/23`,
`Metal3 30/23`, `Metal4 50/23`, `Metal5 67/23`, `TopMetal1 126/23`,
`TopMetal2 134/23` — and `NoMetFiller 160/0` (all metals). The `SG13_dev`
`NoFillerStack` PCell writes exactly these rectangles (one per selected layer).

Test (2026-09-19, PDK `8437402`, KLayout 0.30.9): the dry run's GDS after the
seal ring (all macros placed, before fill) with one no-fill rectangle per
layer over the `g1_sense` footprint (733, 440)–(985.16, 629.25) µm added at
the top level (`add_nofill.py`), then `libs.tech/klayout/tech/scripts/filler.py`
as the flow runs it (`filler.log`), then fill shapes (datatype 22) counted
inside and outside the rectangle (`count_fill.py`).

| Layer | Fill shapes, whole chip | Inside the no-fill rectangle | Same rectangle in the flow's own fill (no no-fill shape) |
| --- | ---: | ---: | ---: |
| Activ | 30 066 | **0** | 136 |
| GatPoly | 30 066 | **0** | 136 |
| Metal1 | 43 079 | **0** | 1 915 |
| Metal2 | 58 224 | **0** | 1 922 |
| Metal3 | 29 230 | **0** | 1 437 |
| Metal4 | 32 730 | **0** | 1 457 |
| Metal5 | 32 662 | **0** | 1 395 |
| TopMetal1 | 4 770 | **0** | 242 |
| TopMetal2 | 4 492 | **0** | 189 |

Result: the filler honours `<layer>/23` shapes wherever they are in the
hierarchy (it works on the flattened chip). Without no-fill shapes it does
place fill over a macro footprint, but only in the gaps its spacing rules
leave around the macro's own metal (`macro_fill.py`: all fill is in the top
cell, none inside the macro cells) — which is why the sense/trip/gate column
still fails the global density windows (`AFil.g1`, `M1.k`…`M5.k`, `TM1.d`,
`TM2.d`): the macros contain no fill of their own and their interiors are
too dense for the chip filler to add much.

Recommendation for the block owners: put `<layer>/23` (or one `NoFillerStack`
instance) over matched arrays, capacitors and sensitive nodes only, and run the
PDK filler inside the block GDS themselves (`filler.py` on the block, or the
`KLayout.Filler` step of their flow) so the macro arrives with its own fill;
the chip-level fill then fills the channels and respects the no-fill shapes.
Chip-level fill alone cannot lift the macro column to the minimum density.
