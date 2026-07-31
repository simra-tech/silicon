#!/bin/bash
# One clean full build: official a0d1699a -> 8 retained patches -> configure once -> make -j4 once.
# No executable invocation, no simulation.
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
P8="$CAND/NGSPICE46-VBIC-VRTH-TRANSITION-DIAGNOSTIC-V2.patch"
EXP1=b3abd28a43ee30204673eb1ea6f6fd5de0b049e2e03de168b25b94a2f86e2dcf
EXP2=ee6b2aa917c57a79d1694f885fa9b2ac593c5750da92b910ed2bae1eacdb27c9
EXP3=e8939ea16fc58d8998b495e7f5f524b1a272b164b43ae2e9771de224ce4f97ff
EXP4=01cc4f1fe6c078df51147cf1ab6b60714b3fe68e704053769777528a1f1f3b06
EXP5=2999b2afa9a34fdd501f02a2312be2b98f5f5f57c9d7bd0637321a61aa581075
EXP6=92123daa3d880ac25960b8758b1e4cb4440fc55cb30f100c5750b5aa20c3e292
EXP7=c571a9c68e959c570b1680ff5cf6e51bab5e97071b5f49b3875360e6cffc9898
EXP8=59d875679da675ef8daedbd151e91b39b27a13ae197530af40650c62e3e75172
BUILD_DIR=$BUILD_ROOT
LOG_DIR="$BUILD_DIR/logs"

rm -rf "$BUILD_DIR"
mkdir -p "$LOG_DIR"
tar xzf "$TARBALL" -C "$BUILD_DIR"
SRC="$BUILD_DIR/ngspice-46"

{
    echo "=== PRE_BUILD_STATE_START $(date -u +%FT%TZ) ==="
    echo "TARBALL_SHA=$(sha256sum "$TARBALL" | cut -d' ' -f1)"
    echo "OFFICIAL_VBICLOAD_SHA=$(sha256sum "$SRC/src/spicelib/devices/vbic/vbicload.c" | cut -d' ' -f1)"
    echo "OBJECT_FILES=$(find "$SRC" \( -name '*.o' -o -name '*.lo' -o -name '*.loT' -o -name '*.la' -o -name '*.a' \) | wc -l)"
    echo "GEN_CONFIG_STATE=$(find "$SRC" \( -name 'config.log' -o -name 'config.status' \) | wc -l)"
    echo "UNIX_CONFIG_H=$(find "$SRC" -name 'config.h' -not -path '*/visualc/*' | wc -l)"
    echo "SHIPPED_VISUALC_CONFIG_H=$(find "$SRC" -path '*/visualc/*' -name 'config.h' | wc -l)"
    echo "SHIPPED_MAKEFILES=$(find "$SRC" -name 'Makefile' | wc -l)"
    echo "BUILD_LOGS=$(find "$SRC" -name '*.log' | wc -l)"
    echo "DEPS_DIRS=$(find "$SRC" -name '.deps' -type d | wc -l)"
    echo "SRC_NGSPICE=$(test -f "$SRC/src/ngspice" && echo yes || echo no)"
    echo "MAKE_PROCESSES=$(pgrep -c make || echo 0)"
    echo "NGSPICE_PROCESSES=$(pgrep -c ngspice || echo 0)"
} > "$LOG_DIR/pre_build.log" 2>&1

cd "$SRC" || exit 91
for i in 1 2 3 4 5 6 7 8; do
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

{
    echo "=== CONFIGURE_CMD: ./configure --prefix=$BUILD_DIR/install --with-x=no --with-readline=no --enable-xspice --disable-debug ==="
    echo "=== CONFIGURE_START $(date -u +%FT%TZ) ==="
    ./configure \
        --prefix="$BUILD_DIR/install" \
        --with-x=no \
        --with-readline=no \
        --enable-xspice \
        --disable-debug
    echo "CONFIGURE_EXIT=$?"
    echo "=== CONFIGURE_END $(date -u +%FT%TZ) ==="
} > "$LOG_DIR/configure.log" 2>&1

CFG_EXIT=$(grep -o 'CONFIGURE_EXIT=[0-9]*' "$LOG_DIR/configure.log" | cut -d= -f2)
if [ "$CFG_EXIT" = "0" ]; then
    {
        echo "=== BUILD_CMD: make -j4 ==="
        echo "=== MAKE_START $(date -u +%FT%TZ) ==="
        make -j4
        echo "MAKE_EXIT=$?"
        echo "=== MAKE_END $(date -u +%FT%TZ) ==="
    } > "$LOG_DIR/make.log" 2>&1
else
    echo "MAKE_EXIT=SKIPPED" > "$LOG_DIR/make.log"
fi

{
    echo "=== POST_BUILD_STATE_START $(date -u +%FT%TZ) ==="
    echo "FINAL_SOURCE_SHA=$(sha256sum "$SRC/src/spicelib/devices/vbic/vbicload.c" | cut -d' ' -f1)"
    echo "SRC_NGSPICE=$(test -f "$SRC/src/ngspice" && echo yes || echo no)"
    if [ -f "$SRC/src/ngspice" ]; then
        echo "EXE_SIZE=$(stat -c %s "$SRC/src/ngspice")"
        echo "EXE_SHA=$(sha256sum "$SRC/src/ngspice" | cut -d' ' -f1)"
    fi
    echo "MAKE_PROCESSES=$(pgrep -c make || echo 0)"
    echo "NGSPICE_PROCESSES=$(pgrep -c ngspice || echo 0)"
} > "$LOG_DIR/post_build.log" 2>&1

echo "BUILD_CHAIN_DONE"
