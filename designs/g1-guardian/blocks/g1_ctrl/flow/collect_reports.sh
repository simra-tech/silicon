#!/usr/bin/env bash
# Copy the signoff evidence of a LibreLane run (flow/runs/<tag>, gitignored)
# into ../reports/librelane_<tag>/ (tracked). Usage: collect_reports.sh <tag>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAG="$1"; RUN="$HERE/runs/$TAG"; OUT="$HERE/../reports/librelane_$TAG"
mkdir -p "$OUT"
cp "$RUN/final/metrics.json"                       "$OUT/metrics.json"
cp "$RUN/resolved.json"                            "$OUT/config_resolved.json"
cp "$RUN"/*-klayout-drc/reports/drc.klayout.json   "$OUT/drc.klayout.json"
cp "$RUN"/*-klayout-drc/klayout-drc.log            "$OUT/klayout_drc.log"
cp "$RUN"/*-magic-drc/reports/drc.magic.rpt        "$OUT/drc.magic.rpt"
cp "$RUN"/*-magic-drc/magic-drc.log                "$OUT/magic_drc.log"
cp "$RUN"/*-netgen-lvs/reports/lvs.netgen.rpt      "$OUT/lvs.netgen.rpt"
cp "$RUN"/*-netgen-lvs/netgen-lvs.log              "$OUT/netgen_lvs.log"
cp "$RUN"/*-klayout-xor/klayout-xor.log            "$OUT/klayout_xor.log"
cp "$RUN"/*-openroad-stapostpnr/summary.rpt        "$OUT/sta_summary.rpt"
for c in typ_1p20V_25C fast_1p32V_m40C slow_1p08V_125C; do
    cp "$RUN"/*-openroad-stapostpnr/nom_$c/checks.rpt "$OUT/sta_checks_${c%%_*}.rpt"
done
# the last antenna check after detailed routing
last_ant=$(ls -d "$RUN"/*-openroad-checkantennas* | sort | tail -1)
cp "$last_ant/reports/antenna_summary.rpt"         "$OUT/antenna_summary.rpt"
cp "$last_ant/reports/antenna.rpt"                 "$OUT/antenna.rpt"
grep -E "^(design__|antenna|route__|synthesis__|timing__|clock__|power__|ir__)" "$RUN/final/metrics.csv" > /dev/null 2>&1 || true
echo "collected into ${OUT#$HERE/../}"; ls "$OUT"
