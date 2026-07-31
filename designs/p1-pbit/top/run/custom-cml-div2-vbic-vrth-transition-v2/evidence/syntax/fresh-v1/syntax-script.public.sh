#!/bin/bash
# One syntax-only compile check: fresh pristine official tree -> 6 accepted patches
# -> base 92123daa -> V1 patch b57d3ff0 -> applied c571a9c6. No configure, no make,
# no configured/built tree reuse, no ngspice invocation.
set -u
TARBALL=$SOURCE_ARCHIVE
CAND=$CANDIDATE_ROOT
P1="$CAND/NGSPICE46-VBIC-VRTH-ORIGIN-DIAGNOSTIC-V2.patch"
P2="$CAND/NGSPICE46-VBIC-TEMPNODE-STAMP-DIAGNOSTIC-V3.patch"
P3="$CAND/NGSPICE46-VBIC-ITH-RHS-DECOMP-DIAGNOSTIC-V1.patch"
P4="$CAND/NGSPICE46-VBIC-ITH-TERM-DIAGNOSTIC-V2.patch"
P5="$CAND/NGSPICE46-VBIC-IBE-SOURCE-DIAGNOSTIC-V2.patch"
P6="$CAND/NGSPICE46-VBIC-TEMP-SCALE-DIAGNOSTIC-V1.patch"
P7="$CAND/NGSPICE46-VBIC-VRTH-TRANSITION-DIAGNOSTIC-V1.patch"
EXP1=b3abd28a43ee30204673eb1ea6f6fd5de0b049e2e03de168b25b94a2f86e2dcf
EXP2=ee6b2aa917c57a79d1694f885fa9b2ac593c5750da92b910ed2bae1eacdb27c9
EXP3=e8939ea16fc58d8998b495e7f5f524b1a272b164b43ae2e9771de224ce4f97ff
EXP4=01cc4f1fe6c078df51147cf1ab6b60714b3fe68e704053769777528a1f1f3b06
EXP5=2999b2afa9a34fdd501f02a2312be2b98f5f5f57c9d7bd0637321a61aa581075
EXP6=92123daa3d880ac25960b8758b1e4cb4440fc55cb30f100c5750b5aa20c3e292
EXP7=c571a9c68e959c570b1680ff5cf6e51bab5e97071b5f49b3875360e6cffc9898
BUILD_DIR=$FRESH_SYNTAX_ROOT
LOG_DIR="$BUILD_DIR/logs"

rm -rf "$BUILD_DIR"
mkdir -p "$LOG_DIR"
tar xzf "$TARBALL" -C "$BUILD_DIR"
SRC="$BUILD_DIR/ngspice-46"

{
    echo "=== SOURCE_LINEAGE_START $(date -u +%FT%TZ) ==="
    echo "TARBALL_SHA=$(sha256sum "$TARBALL" | cut -d' ' -f1)"
    echo "OFFICIAL_VBICLOAD_SHA=$(sha256sum "$SRC/src/spicelib/devices/vbic/vbicload.c" | cut -d' ' -f1)"
    echo "CONFIG_H_PRESENT=$(find "$SRC" -name 'config.h' -not -path '*/visualc/*' | wc -l)"
    echo "CONFIGURED_STATE=$(find "$SRC" \( -name 'config.log' -o -name 'config.status' \) | wc -l)"
    echo "BUILT_OBJECTS=$(find "$SRC" \( -name '*.o' -o -name '*.lo' \) | wc -l)"
    echo "SRC_NGSPICE=$(test -f "$SRC/src/ngspice" && echo yes || echo no)"
} > "$LOG_DIR/lineage.log" 2>&1

cd "$SRC" || exit 91
for i in 1 2 3 4 5 6 7; do
    eval P=\$P$i
    patch -p0 -i "$P" > "$LOG_DIR/apply_p$i.log" 2>&1
    patch_rc=$?
    hash=$(sha256sum src/spicelib/devices/vbic/vbicload.c | cut -d' ' -f1)
    printf 'P%s_EXIT=%s SHA=%s\n' "$i" "$patch_rc" "$hash" >> "$LOG_DIR/lineage.log"
    expected=$(eval echo \$EXP$i)
    if [ "$patch_rc" != "0" ] || [ "$hash" != "$expected" ]; then
        printf 'P%s_BOUNDARY_STOP expected=%s\n' "$i" "$expected" >> "$LOG_DIR/lineage.log"
        exit 60
    fi
done
echo "=== SOURCE_LINEAGE_END $(date -u +%FT%TZ) ===" >> "$LOG_DIR/lineage.log"

cd src/spicelib/devices/vbic || exit 92
{
    echo "=== SYNTAX_CMD: gcc -I. -I../../../../src/include -std=gnu11 -fopenmp -Wall -Wextra -Wmissing-prototypes -Wstrict-prototypes -Wnested-externs -Wold-style-definition -Wredundant-decls -Wconversion -Wno-unused-but-set-variable -fsyntax-only vbicload.c (no -DHAVE_CONFIG_H: no config.h in the pristine, unconfigured tree; configured/built tree reuse forbidden) ==="
    echo "=== SYNTAX_START $(date -u +%FT%TZ) ==="
} >> "$LOG_DIR/syntax.log" 2>&1
gcc -I. -I../../../../src/include -std=gnu11 -fopenmp \
    -Wall -Wextra -Wmissing-prototypes -Wstrict-prototypes -Wnested-externs \
    -Wold-style-definition -Wredundant-decls -Wconversion -Wno-unused-but-set-variable \
    -fsyntax-only vbicload.c >> "$LOG_DIR/syntax.log" 2>&1
echo "SYNTAX_EXIT=$?" >> "$LOG_DIR/syntax.log"
echo "=== SYNTAX_END $(date -u +%FT%TZ) ===" >> "$LOG_DIR/syntax.log"
echo "SYNTAX_CHAIN_DONE"
