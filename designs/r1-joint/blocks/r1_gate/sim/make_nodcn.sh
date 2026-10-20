#!/bin/sh
# Deck-local copy of the PDK IO spice file with the dantenna devices commented out (run inside the container).
# Usage: G1_RESULTS_ROOT=... flow/run.sh sh <this script>
sed -e 's/^\(X[A-Za-z0-9_]* .* dantenna .*\)$/* removed (nodcn): \1/' /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi > ${G1_RESULTS_ROOT}/r1_gate/sg13g2_io_nodcn.spi
grep -c "removed (nodcn)" ${G1_RESULTS_ROOT}/r1_gate/sg13g2_io_nodcn.spi
