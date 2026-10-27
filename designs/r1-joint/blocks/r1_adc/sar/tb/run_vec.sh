#!/bin/sh
# T2j: run tb_sar_vec.v on vector cases inside the container (Icarus Verilog of the image).
#   G1_CPUSET=118 G1_WORKDIR=designs/r1-joint/blocks/r1_adc/sar G1_RESULTS_ROOT=<bulk> \
#     flow/run.sh sh tb/run_vec.sh <run-id> <mode: rtl | gl> [<netlist.v> <sdf> <corner tag>] -- <case> ...
# Writes <G1_RESULTS_ROOT>/r1_adc_sar/<run-id>/{<case>.log, <case>.out, compile.log, inputs.sha256}.
# gl mode: the PDK cell models (sg13g2_stdcell.v, sg13g2_udp.v; Icarus prints 'sorry: ifnone with an
# edge-sensitive path' for the flip-flop specify blocks and ignores those conditions), the netlist and SDF annotation (MAXIMUM of the given corner file).
set -u
RID="$1"; MODE="$2"; shift 2
NET=""; SDF=""; CTAG=""
if [ "$MODE" = gl ]; then NET="$1"; SDF="$2"; CTAG="$3"; shift 3; fi
[ "$1" = "--" ] && shift
B="$G1_RESULTS_ROOT/r1_adc_sar/$RID"
if [ -e "$B" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$B"
export LD_LIBRARY_PATH=/foss/tools/iverilog/lib
CELLS=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
UDPS=/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_udp.v
iverilog -V 2>&1 | head -1 > "$B/tools.txt"
RC=0
for C in "$@"; do
  if [ "$MODE" = gl ]; then
    sha256sum "$NET" "$SDF" >> "$B/inputs.sha256"
    iverilog -g2005 -Wno-timescale -DGL -DSDF="\"$SDF\"" -DFUNCTIONAL=0 -DSCHED="\"tb/vec/${C}_sched.vh\"" \
      -DSTIM="\"tb/vec/${C}_stim.vh\"" -DOUT="\"$B/$C.out\"" -gspecify -ginterconnect -Tmax -o "$B/$C.vvp" tb/tb_sar_vec.v "$NET" "$CELLS" "$UDPS" \
      >> "$B/compile.log" 2>&1 || { echo "compile failed $C" >&2; RC=2; continue; }
  else
    sha256sum rtl/r1_adc_sar.v tb/tb_sar_vec.v "tb/vec/${C}_stim.vh" >> "$B/inputs.sha256"
    iverilog -g2005 -Wall -Wno-timescale -DSCHED="\"tb/vec/${C}_sched.vh\"" -DSTIM="\"tb/vec/${C}_stim.vh\"" \
      -DOUT="\"$B/$C.out\"" -o "$B/$C.vvp" tb/tb_sar_vec.v rtl/r1_adc_sar.v >> "$B/compile.log" 2>&1 \
      || { echo "compile failed $C" >&2; RC=2; continue; }
  fi
  vvp -n "$B/$C.vvp" > "$B/$C.log" 2>&1 || RC=3
  rm -f "$B/$C.vvp"
done
exit $RC
