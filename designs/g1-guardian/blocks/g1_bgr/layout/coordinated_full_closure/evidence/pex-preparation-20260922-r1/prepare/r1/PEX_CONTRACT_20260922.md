# Prospective assembled BGR extraction

Only a completed full-assembly stock DRC-zero / strict-LVS-Match candidate
may enter this stage. Preserve its GDS, source1036-device CDL, nine ports,
55-net physical graph, all seven star-cut checks, and exact MOS junction audit.
No electrical source/calibration adoption is implied by extraction.

Create a derived flat view without deleting any text or polygon. In particular,
retain native HBT recognition annotations and GatPoly pin shapes. Require
all-layer polygon parity and exact transformed text parity after saving.
Run the installed unchanged KPEX IHP extraction deck using the existing
export-only wrapper. Disable simplification, device combination, purge and
net purge using supported switches; preserve336MOS/301HBT/399resistor devices.
Require explicit LVS match, strict cross-reference Match (warnings fail),
exact source-node/device parameters and pin map before any capacitance run.
Record all bundled extraction-support and public PDK hashes separately.

Then, and only then, run KPEX0.3.12 2.5D `--mode CC --threads1`. Require a
complete finite nonnegative capacitance inventory, named-source-net mapping,
and device-count/parameter invariance against the passed extraction database.
Retain all nonzero coupling terms; no threshold pruning or model substitution.
Capacitance-only extraction does not qualify the finite metal-return voltage
drop, via resistance, matching, density, antenna, external ring or electrical
performance. Those checks are separately passed/failed/not run, never implied.

Each stage gets a unique output directory and fresh global resource gate.
One allocated CPU,4GiB RAM reservation,2GiB bulk growth,180s export-LVS and
300s capacitance watchdogs plus5s kill grace. No automatic timeout ladder.
Original failures remain immutable. No random seed: not applicable.
