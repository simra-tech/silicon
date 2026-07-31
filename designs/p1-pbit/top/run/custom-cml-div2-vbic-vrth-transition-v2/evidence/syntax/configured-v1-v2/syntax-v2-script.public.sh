#!/bin/bash
# One syntax-only invocation on the external repaired source V2 using the
# retained configured tree (working dir + generated config.h). No copy/modify.
set -u
TREE=$CONFIGURED_SYNTAX_ROOT/ngspice-46
LOG=$CONFIGURED_SYNTAX_ROOT/syntax_check_v2.log
CAND=$CANDIDATE_ROOT
REP="$CAND/vbicload_vrth_transition_diag_v2.c"

cd "$TREE" || exit 91
{
    echo "=== PRE_SYNTAX_STATE $(date -u +%FT%TZ) ==="
    echo "REPAIRED_SOURCE_SHA=$(sha256sum "$REP" | cut -d' ' -f1)"
    echo "TREE_SOURCE_SHA=$(sha256sum src/spicelib/devices/vbic/vbicload.c | cut -d' ' -f1)"
    echo "HEADER_SHA=$(sha256sum src/include/ngspice/config.h | cut -d' ' -f1)"
    echo "OBJECT_FILES=$(find src \( -name '*.o' -o -name '*.lo' -o -name '*.loT' -o -name '*.la' -o -name '*.a' \) | wc -l)"
    echo "SRC_NGSPICE=$(test -f src/ngspice && echo yes || echo no)"
    echo "=== SYNTAX_CMD: gcc -DHAVE_CONFIG_H -I. -I../../../../src/include -std=gnu11 -fopenmp -Wall -Wextra -Wmissing-prototypes -Wstrict-prototypes -Wnested-externs -Wold-style-definition -Wredundant-decls -Wconversion -Wno-unused-but-set-variable -fsyntax-only <external repaired source> (configured-tree source untouched) ==="
    echo "=== SYNTAX_START $(date -u +%FT%TZ) ==="
} > "$LOG" 2>&1

cd "$TREE/src/spicelib/devices/vbic" || exit 92
gcc -DHAVE_CONFIG_H -I. -I../../../../src/include -std=gnu11 -fopenmp \
    -Wall -Wextra -Wmissing-prototypes -Wstrict-prototypes -Wnested-externs \
    -Wold-style-definition -Wredundant-decls -Wconversion -Wno-unused-but-set-variable \
    -fsyntax-only "$REP" >> "$LOG" 2>&1
echo "SYNTAX_EXIT=$?" >> "$LOG"

cd "$TREE" || exit 93
{
    echo "=== POST_SYNTAX_STATE $(date -u +%FT%TZ) ==="
    echo "REPAIRED_SOURCE_SHA=$(sha256sum "$REP" | cut -d' ' -f1)"
    echo "TREE_SOURCE_SHA=$(sha256sum src/spicelib/devices/vbic/vbicload.c | cut -d' ' -f1)"
    echo "HEADER_SHA=$(sha256sum src/include/ngspice/config.h | cut -d' ' -f1)"
    echo "=== SYNTAX_END $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
echo "SYNTAX_V2_CHAIN_DONE"
