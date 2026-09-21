#!/usr/bin/env bash
# Replay only Magic streamout from a retained assembly run, then compare its
# pre-fill output with the corresponding retained pre-fill KLayout streamout.
# Invoke inside the pinned EDA container from repository root:
#   bash designs/g1-guardian/blocks/g1_padring/flow/run_streamout_namespaced.sh <run> <new-out>
set -euo pipefail
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <assembly run> <new output dir>" >&2
    exit 2
fi
RUN=$(cd "$1" && pwd)
OUT=$2
HELPER=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/streamout_namespace.py
python3 "$HELPER" prepare --run "$RUN" --out "$OUT"
OUT=$(cd "$OUT" && pwd)
SCRIPTS=/usr/local/lib/python3.12/dist-packages/librelane/scripts
export _TCL_ENV_IN="$OUT/_env.tcl"
export _MAGIC_SCRIPT="$SCRIPTS/magic/def/mag_gds.tcl"
(
    cd "$OUT"
    timeout 180s magic -dnull -noconsole \
        -rcfile /foss/pdks/ihp-sg13g2/libs.tech/magic/ihp-sg13g2.magicrc \
        "$SCRIPTS/magic/wrapper.tcl" > magic.log 2>&1
)
python3 "$HELPER" compare --left "$OUT/g1_chip_top.magic.gds" \
    --right "$RUN/57-klayout-streamout/g1_chip_top.klayout.gds" \
    --report "$OUT/xor_geometry.json"
