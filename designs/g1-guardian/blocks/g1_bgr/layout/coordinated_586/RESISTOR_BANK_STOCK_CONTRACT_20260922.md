# Frozen resistor-bank stock gate

The first fixed-placement pilot passed399 native bindings,798 resistor-end
probes,40 source-net ports and one guard probe: no opens/shorts,84,268 polygon
vertices on5nm grid, unchanged GatPoly/PolyRes,420×132µm bounds. GDS SHA256
`14056b42510b67485bbcfdc8a36cb4803a9e6696e35b868f228fbf1f131601f8`,
CDL `8d8952e9a4fe8322f8ced32d3d4502433fdfff1af806acc27e1ecaf931cddb7f`.
The independent routing review flagged VSS bar/landing spacing; this frozen
geometry already uses1.2µm around both0.8µm VSS-role rails, giving0.38µm
planning clearance to adjacent0.84µm-tall landings. Stock rules decide legality.

Run exactly one unchanged stock hard/recommended/off-grid/angle DRC and one
strict stock LVS, sequentially, one CPU,180seconds each,0.15GiB total growth,
with a fresh resource gate. DRC requires completed zero-marker reports; LVS
requires explicit match and every database cross-reference exactly Match.
Missing reports, timeout, nonzero return or MatchWithWarning fail. Retain every
failure; no geometry/PDK/source changes or reroute is authorized by this gate.

Density and antenna are **not run** in this isolated stage. Full329 inherited
parasitics are not native resistors and are not copied into the399-device
subset CDL; new PEX is **not run**. Native source bindings remain unchanged.
This tests actual routing connectivity and stock legality, not matched branch
resistance, capacitance, electrical performance, full R1/HBT star, current
reliability, full macro or adoption. Seed is **not applicable**.
