# HBT pilot r2 preparation — only ten collector Via1 rotations

Preserve r1 DRC ten M2.b failures and strict LVS pass. Derive r2 from the frozen
r1 builder and exactly the same source586/34 packed positions/contact cells.
Only ten c2 collector Via1 two-cut arrays rotate from x to y direction, with
their associated M1/M2 landing rectangles changing0.72×0.30 to0.30×0.72 µm.
All other routes, net assignments, Via2 cuts, terminals and native shapes stay
unchanged. Each cut remains0.19 µm, pitch0.42 µm, enclosure0.055 µm.

Before stock review, require exact source subset/CDL equality, unchanged
unaffected route/cut multisets, exactly20 removed/20 added landing records and
20 removed/20 added Via1 cuts, all other ledger records equal; serialized GDS
XOR only on M1/M2/Via1 inside the ten declared landing windows, all other drawn
layers and texts equal. Re-run native Activ/GatPoly parity, all136 terminal
incidences/six-net graph, via enclosure and all1002-neighbor obstruction screen.
The expected side gap increases from0.09 to0.30 µm; stock rules still decide
legality, including the taller M1 landing.

One CPU0,180s preparation,.10GiB growth after fresh gate. No analog, fullmacro
claim, stock run, automatic retry or other geometry edit in this preparation.
Send actual r2 geometry/CDL/diff hashes and prospective stock contract to root.
