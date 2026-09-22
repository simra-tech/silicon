# Resistor-bank r2: only offending M3 landing extensions

R1 stock DRC failed73 M3.b markers; strict LVS passed. Each marker is the
0.16µm vertical gap between two0.84µm-high M3 via landings at the same x and
adjacent1µm collector tracks. Retain the original GDS, source, reports and code.

Identify both landing centers of every exact retained marker and require each
center to occur in the frozen Via2/Via3 ledger. Change only those M3 landings'
height from0.84 to0.72µm:0.61µm total cut span plus0.055µm enclosure at each
end. Cut geometry, center/pitch/count, all M1/M2/M4 landings, global collectors,
all399 native placements, net names and source-derived CDL stay unchanged.
Expected former pad-to-pad gap becomes0.28µm. Stock rules still decide legality.

Generate under a fresh0.15GiB resource gate, one CPU,180seconds. Before stock
require original839-probe/40-net graph and5nm checks, byte-identical CDL and
native-device ledger, serialized all-layer XOR confined to M3, M3 removals only
inside the declared old pad windows, unchanged text inventory, and complete
0.055µm M3 enclosure of every Via2/Via3 cut. Record actual changed centers,
removed area, geometry hashes and derived script hash. No additional edits or
automatic stock launch/route ladder follow. New DRC/LVS remain **not run** until
review. All first-pilot electrical, full-star and PEX limitations remain.
