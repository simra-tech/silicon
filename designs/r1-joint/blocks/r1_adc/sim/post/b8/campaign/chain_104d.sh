. "$(dirname "$0")/common.sh"
# B8 dev2 (common-mode widening only): merge the extraction, then the D23 offset deck at tt / ff / ss, VDDA 3.3 V
P=$G1_RESULTS_ROOT/r1_adc/pex-b8-dev2
until grep -q "build rc 0" $P/build.console 2>/dev/null; do sleep 30; done
N=sim/post/r1_adc_post_rc_mb8b.spice
python3 sim/post/merge_parallel.py $P/build/r1_adc_post_rc.spice $N
sed -i "1s#[./]*$G1_RESULTS_ROOT#<G1_RESULTS_ROOT>#; 1s#\.\./\.\./\.\./\.\./\.\./\.\./\.\.<G1_RESULTS_ROOT>#<G1_RESULTS_ROOT>#" $N
sed -i "s#\"source\": \"[^\"]*pex-b8-dev2#\"source\": \"<G1_RESULTS_ROOT>/r1_adc/pex-b8-dev2#" sim/post/r1_adc_post_rc_mb8b_merge.json
ofs() { # tag mos temp vdd tsuf vdda
  beh postb8b-ofs-$1-v$(echo $6 | tr -d .) 104 $N --deck points --ref lay --noise none --vdda $6 --corner $2 --temp $3 --vdd $4 \
    --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq${5}_pre33.inc \
    --question "D23 offset (layout B8 dev2 extraction): first conversion 0 V, $1 VDDA $6 V, buffer + bandgap DC (no noise), behavioural SAR" \
    --disposition "post-layout value (static offset, D23 drift table, layout B8 dev2)"
}
ofs tt mos_tt 27 1.2 "" 3.3
ofs ffm40 mos_ff -40 1.32 _vdd132 3.3
ofs ss125 mos_ss 125 1.08 _vdd108 3.3
echo chain104d done
