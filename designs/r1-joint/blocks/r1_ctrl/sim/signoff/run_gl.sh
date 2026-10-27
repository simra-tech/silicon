#!/bin/sh
# Gate-level run of the chip-level testbench on the t7 post-layout netlist.
# From the repository root:
#   G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl G1_RESULTS_ROOT=<root> \
#     flow/run.sh sh sim/signoff/run_gl.sh <run-id> <mode>      mode: slow | typ | zd
#   slow: SDF nom_slow_1p08V_125C, MAXIMUM; typ: SDF nom_typ_1p20V_25C, TYPICAL; zd: no SDF (zero delay)
# Revision 0.6: LLRUN=<hardening run id>; the 0.5 tests tap and ana also run (add them to GL_JOBS); disc, cdc, cal are GLSKIP (README 0.6).
# Revision 0.7: the v07 group (ports and SPI only) at three clocks is in the default list.
# Revision 0.6 default list: tap ana ssi spi gate safe biss (cal needs thr_*/cal_*, disc and cdc need nets the netlist does not have: not run).
# Tests (same set as sim/run_all.sh, 315 RTL checks): biss, ssi at 23.810 33.333 47.619 ns; spi gate safe cal at 33.333; cal at 23.810.
set -u
export LD_LIBRARY_PATH=/foss/tools/iverilog/lib
RID="$1"; MODE="$2"; PAR="${3:-4}"
LL=${LLRUN:-r1ctrl_ll_20261021_t7}   # hardening run whose netlist and SDF are simulated (0.6: r1ctrl_ll_20261021_t9)
T7=$G1_RESULTS_ROOT/r1_ctrl/$LL/flow/runs/$LL/final
V=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog
OUT="$G1_RESULTS_ROOT/r1_ctrl/$RID/$MODE"
mkdir -p "$OUT"
case "$MODE" in
  slow) SDFSRC="$T7/sdf/nom_slow_1p08V_125C/r1_ctrl_top__nom_slow_1p08V_125C.sdf"; SDFMODE=MAXIMUM; PICK=max; SDFARG=x ;;
  typ)  SDFSRC="$T7/sdf/nom_typ_1p20V_25C/r1_ctrl_top__nom_typ_1p20V_25C.sdf"; SDFMODE=TYPICAL; PICK=typ; SDFARG=x ;;
  zd)   SDFARG="" ;;
  *) echo "bad mode" >&2; exit 2 ;;
esac
# SDF back-annotation needs specify blocks and interconnect delays compiled in (Icarus omits them by default)
IVFLAGS=""; [ -n "$SDFARG" ] && IVFLAGS="-gspecify -ginterconnect"
if [ -z "${GL_JOBS:-}" ]; then
{ echo "date_utc $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "mode $MODE"; iverilog -V 2>&1 | head -1
  echo "pdk_commit $(cat /foss/pdks/ihp-sg13g2/COMMIT)"
  sha256sum "$T7/nl/r1_ctrl_top.nl.v" tb/tb_top.v sim/signoff/mk_gl_tb.sh
  [ -n "$SDFARG" ] && sha256sum "$T7"/sdf/*/*.sdf; } > "$OUT/versions.txt"
sh sim/signoff/mk_gl_tb.sh tb/tb_top.v "$OUT/tb_top_gl0.v"
python3 sim/signoff/mk_gl_tb_v05.py "$OUT/tb_top_gl0.v" "$OUT/tb_top_gl.v" "$T7/nl/r1_ctrl_top.nl.v"   # revision 0.5 probes
NL="$T7/nl/r1_ctrl_top.nl.v"
if [ -n "$SDFARG" ]; then
  python3 sim/signoff/prep_sdf.py "$T7/nl/r1_ctrl_top.nl.v" "$SDFSRC" "$OUT/nl_sdf.v" "$OUT/delays.sdf" "$PICK" > "$OUT/prep_sdf.log" 2>&1 || exit 1
  NL="$OUT/nl_sdf.v"
fi
iverilog -g2005 $IVFLAGS -Wno-timescale -o "$OUT/tb_gl.vvp" "$V/sg13g2_udp.v" "$V/sg13g2_stdcell.v" \
   "$NL" "$OUT/tb_top_gl.v" > "$OUT/compile.log" 2>&1 || { echo "compile failed" >&2; exit 1; }
fi
[ -n "$SDFARG" ] && SDFARG="+sdf=$OUT/delays.sdf +sdfmode=$SDFMODE"
cd "$OUT"
# GL_JOBS="biss:33.333 ..." reruns a subset with the compiled model of the first call (no recompile)
JOBS="${GL_JOBS:-v07:23.810 v07:33.333 v07:47.619 tap:33.333 ana:33.333 ssi:23.810 spi:33.333 gate:33.333 safe:33.333 ssi:33.333 ssi:47.619 biss:23.810 biss:33.333 biss:47.619}"   # 0.6: tap, ana added; cal, disc, cdc are GLSKIP (README 0.6) and not in the default list
for j in $JOBS; do echo "$j"; done | xargs -P "$PAR" -I{} sh -c '
  t=${1%%:*}; ck=${1##*:}
  s=$(date +%s)
  vvp -n tb_gl.vvp +test=$t +clk_ns=$ck '"$SDFARG"' > top_${t}_${ck}.log 2>&1
  echo "rc=$? wall_s=$(( $(date +%s) - s ))" > top_${t}_${ck}.rc' _ {}
