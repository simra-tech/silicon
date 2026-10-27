#!/bin/sh
# Full r1_ctrl verification run (revision 0.8: the 0.7 list plus the D22 group (tb_d22 + d22_ref.py bit-exact, chip-level d22 at three clocks); revision 0.7: the 0.5 list plus the v07 group at three clocks; revision 0.5: the list below is the 0.3 list plus: exhaustive r1_tapidx check,
# chip-level tests tap / ana / disc, SDC port check, Yosys CHECK pass): V3 position (tb_pos + pos_ref.py,
# 30-tick cases of 0.2 and 22-tick D18 frame cases), ADC weight correction
# (tb_adcw + adcw_ref.py), comparator calibration search model against the
# r1_safe MC data (cmpcal_ref.py) and the RTL on the same tables (tb_top calmc),
# chip-level testbenches b..f and cal (tb_top) at the RC corners, Yosys
# synthesis, summary + run.json.
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
sha256sum rtl/*.v tb/*.v tb/*.py sim/*.sh sim/*.py flow/synth.tcl flow/r1_ctrl.sdc flow/check_sdc_ports.py > "$OUT/inputs.sha256"
echo "rtl_concat $(cat rtl/*.v | sha256sum | cut -d' ' -f1)" >> "$OUT/versions.txt"

# (a) V3 position
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/tb_pos.vvp" rtl/r1_sinlut.v rtl/r1_pos.v tb/tb_pos.v > "$OUT/tb_pos.compile.log" 2>&1
# D18: the 36-tick cases (f36_*) are superseded (run r1ctrl_20261020_v03e); the encoder pair runs every
# 22-tick frame, with one 44-tick gap per PWM period (skip=68). r1_pos latency 19 ticks (2 CORDIC iterations per tick).
for c in ideal uncal cal cal_self cal_noise cal_neg fast_k0 fast_k30 fast_100k \
         f22_100k_gap f22_208k_gap f22_250k f22_250k_gap f22_250k_amax_gap f22_250k_alim_gap f22_250k_a2x_gap; do
  case "$c" in f22_100k_gap|f22_*amax*|f22_*alim*|f22_*a2x*) n=3000; pt=22 ;; f22_*) n=4000; pt=22 ;; *) n=2000; pt=30 ;; esac
  case "$c" in *_gap) sk=68 ;; *) sk=0 ;; esac
  python3 tb/pos_ref.py gen "$c" "$OUT" &&
  vvp -n "$OUT/tb_pos.vvp" +dir="$OUT" +case="$c" +n=$n +pair=$pt +skip=$sk +lat=19 > "$OUT/pos_${c}.log" 2>&1 &&
  python3 tb/pos_ref.py check "$c" "$OUT" > "$OUT/pos_${c}_check.log" 2>&1
done

# ADC weight correction
mkdir -p "$OUT/adcw"
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/adcw/tb_adcw.vvp" rtl/r1_adcw.v tb/tb_adcw.v > "$OUT/adcw/compile.log" 2>&1
python3 tb/adcw_ref.py gen "$OUT/adcw" > "$OUT/adcw/gen.log" 2>&1
for w in nom cal; do
  vvp -n "$OUT/adcw/tb_adcw.vvp" +dir="$OUT/adcw" +set=$w > "$OUT/adcw/tb_$w.log" 2>&1
done
python3 tb/adcw_ref.py check "$OUT/adcw" > "$OUT/adcw/check.log" 2>&1
# revision 0.4: one-hot weights read a single decision bit exactly (register map section 4.11)
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/adcw/tb_onehot.vvp" rtl/r1_adcw.v tb/tb_adcw_onehot.v > "$OUT/adcw/onehot.compile.log" 2>&1
vvp -n "$OUT/adcw/tb_onehot.vvp" > "$OUT/adcw/onehot.log" 2>&1

# (b..f, cal) chip level
iverilog -g2005 -Wall -Wno-timescale -DR1_CFG_FLOPS -DR1_CFG_GATED -o "$OUT/tb_top.vvp" rtl/*.v tb/tb_top.v > "$OUT/tb_top.compile.log" 2>&1
for t in biss ssi; do
  for ck in 23.810 33.333 47.619; do
    vvp -n "$OUT/tb_top.vvp" +test=$t +clk_ns=$ck > "$OUT/top_${t}_${ck}.log" 2>&1
  done
done
for t in spi gate safe cal; do
  vvp -n "$OUT/tb_top.vvp" +test=$t +clk_ns=33.333 > "$OUT/top_${t}_33.333.log" 2>&1
done
vvp -n "$OUT/tb_top.vvp" +test=cal +clk_ns=23.810 > "$OUT/top_cal_23.810.log" 2>&1
# revision 0.5: tap-index chain, ANA_CTRL decode, first-conversion discard
for t in tap ana disc; do
  vvp -n "$OUT/tb_top.vvp" +test=$t +clk_ns=33.333 > "$OUT/top_${t}_33.333.log" 2>&1
done
vvp -n "$OUT/tb_top.vvp" +test=tap +clk_ns=23.810 > "$OUT/top_tap_23.810.log" 2>&1
# revision 0.5: clock-domain crossing tests (SSI at the asynchronous worst phase, registered ma-domain reset)
for ck in 23.810 33.333 47.619; do
  vvp -n "$OUT/tb_top.vvp" +test=cdc +clk_ns=$ck > "$OUT/top_cdc_${ck}.log" 2>&1
done

# revision 0.7: R3 (EN synchroniser), R4 (threshold reset), OSC_TRIM lock, comparator mask, reset-value table
for ck in 23.810 33.333 47.619; do
  vvp -n "$OUT/tb_top.vvp" +test=v07 +clk_ns=$ck > "$OUT/top_v07_${ck}.log" 2>&1
done

# revision 0.8 (D22): channel offset/gain correction bit-exact against the integer model (5 cases x 4096 pairs),
# position error before/after the host correction; chip-level d22 (COS_GAIN, CRC coverage, raw min/max capture)
mkdir -p "$OUT/d22"
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/d22/tb_d22.vvp" rtl/r1_sinlut.v rtl/r1_pos.v tb/tb_d22.v > "$OUT/d22/compile.log" 2>&1
python3 tb/d22_ref.py gen "$OUT/d22" > "$OUT/d22/gen.log" 2>&1
for c in raw cor sat full lo; do
  vvp -n "$OUT/d22/tb_d22.vvp" +dir="$OUT/d22" +case=$c > "$OUT/d22/tb_$c.log" 2>&1
done
python3 tb/d22_ref.py check "$OUT/d22" > "$OUT/d22/check.log" 2>&1
for ck in 23.810 33.333 47.619; do
  vvp -n "$OUT/tb_top.vvp" +test=d22 +clk_ns=$ck > "$OUT/top_d22_${ck}.log" 2>&1
done

# revision 0.5: exhaustive r1_tapidx check (4096 pairs per cell type) against the Python form of the r1_safe formula
mkdir -p "$OUT/tapidx"
iverilog -g2005 -Wall -Wno-timescale -o "$OUT/tapidx/tb_tapidx.vvp" rtl/r1_tapidx.v tb/tb_tapidx.v > "$OUT/tapidx/compile.log" 2>&1
vvp -n "$OUT/tapidx/tb_tapidx.vvp" +out="$OUT/tapidx/tapidx_rtl.txt" > "$OUT/tapidx/tb.log" 2>&1
python3 tb/tapidx_ref.py check "$OUT/tapidx/tapidx_rtl.txt" "$OUT/tapidx/tapidx_result.json" > "$OUT/tapidx/check.log" 2>&1

# revision 0.5: every top-level port constrained in the SDC
python3 flow/check_sdc_ports.py rtl/r1_ctrl_top.v flow/r1_ctrl.sdc "$OUT/sdc_ports.json" > "$OUT/sdc_ports.log" 2>&1

# comparator calibration: Python model of the RTL search vs r1_safe cal_model (MC data,
# read-only from ../r1_safe/sim/results), then the RTL on the same comparator tables
mkdir -p "$OUT/cmpcal"
python3 tb/cmpcal_ref.py model "$OUT/cmpcal" ../r1_safe/sim/results > "$OUT/cmpcal/model.log" 2>&1
vvp -n "$OUT/tb_top.vvp" +test=calmc +clk_ns=33.333 +vec="$OUT/cmpcal/cmpcal_vec.txt" +out="$OUT/cmpcal/calmc_rtl.txt" > "$OUT/cmpcal/top_calmc.log" 2>&1
python3 tb/cmpcal_ref.py check "$OUT/cmpcal" > "$OUT/cmpcal/check.log" 2>&1

# synthesis
mkdir -p "$OUT/syn"
SYN_OUT="$OUT/syn" yosys -q -l "$OUT/syn/yosys.log" -c flow/synth.tcl > /dev/null 2>&1

python3 sim/summarize.py "$RID" "$OUT" "$SUM"
