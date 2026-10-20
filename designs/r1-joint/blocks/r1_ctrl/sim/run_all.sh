#!/bin/sh
# Full r1_ctrl verification run (revision 0.2): V3 position (tb_pos + pos_ref.py),
# ADC weight correction (tb_adcw + adcw_ref.py), chip-level testbenches b..f and
# cal (tb_top) at the RC corners, Yosys synthesis, summary + run.json.
# From the repository root:
#   G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl \
#   G1_RESULTS_ROOT=/opt/sim/<user>/r1-traces/sims flow/run.sh sh sim/run_all.sh <run-id>
# Bulk outputs: $G1_RESULTS_ROOT/r1_ctrl/<run-id>/ ; summary: sim/results/<run-id>/
set -u
export LD_LIBRARY_PATH=/foss/tools/iverilog/lib
RID="$1"
OUT="$G1_RESULTS_ROOT/r1_ctrl/$RID"
SUM="sim/results/$RID"
if [ -e "$OUT" ] || [ -e "$SUM" ]; then echo "run id $RID exists" >&2; exit 1; fi
mkdir -p "$OUT" "$SUM"
{
  echo "date_utc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "iverilog $(iverilog -V 2>&1 | head -1)"
  echo "yosys $(yosys -V)"
  echo "python $(python3 -c 'import sys,numpy;print(sys.version.split()[0],"numpy",numpy.__version__)')"
  echo "pdk_commit $(cat /foss/pdks/ihp-sg13g2/COMMIT)"
} > "$OUT/versions.txt"
sha256sum rtl/*.v tb/* sim/*.sh flow/synth.tcl > "$OUT/inputs.sha256"

# (a) V3 position
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/tb_pos.vvp" rtl/r1_sinlut.v rtl/r1_pos.v tb/tb_pos.v > "$OUT/tb_pos.compile.log" 2>&1
for c in ideal uncal cal cal_self cal_noise cal_neg fast_k0 fast_k30 fast_100k; do
  python3 tb/pos_ref.py gen "$c" "$OUT" &&
  vvp -n "$OUT/tb_pos.vvp" +dir="$OUT" +case="$c" +n=2000 > "$OUT/pos_${c}.log" 2>&1 &&
  python3 tb/pos_ref.py check "$c" "$OUT" > "$OUT/pos_${c}_check.log" 2>&1
done

# ADC weight correction
mkdir -p "$OUT/adcw"
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/adcw/tb_adcw.vvp" rtl/r1_adcw.v tb/tb_adcw.v > "$OUT/adcw/compile.log" 2>&1
python3 tb/adcw_ref.py gen "$OUT/adcw" > "$OUT/adcw/gen.log" 2>&1
for w in bin cal; do
  vvp -n "$OUT/adcw/tb_adcw.vvp" +dir="$OUT/adcw" +set=$w > "$OUT/adcw/tb_$w.log" 2>&1
done
python3 tb/adcw_ref.py check "$OUT/adcw" > "$OUT/adcw/check.log" 2>&1

# (b..f, cal) chip level
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/tb_top.vvp" rtl/*.v tb/tb_top.v > "$OUT/tb_top.compile.log" 2>&1
for t in biss ssi; do
  for ck in 23.810 33.333 47.619; do
    vvp -n "$OUT/tb_top.vvp" +test=$t +clk_ns=$ck > "$OUT/top_${t}_${ck}.log" 2>&1
  done
done
for t in spi gate safe cal; do
  vvp -n "$OUT/tb_top.vvp" +test=$t +clk_ns=33.333 > "$OUT/top_${t}_33.333.log" 2>&1
done

# synthesis
mkdir -p "$OUT/syn"
SYN_OUT="$OUT/syn" yosys -q -l "$OUT/syn/yosys.log" -c flow/synth.tcl > /dev/null 2>&1

python3 sim/summarize.py "$RID" "$OUT" "$SUM"
