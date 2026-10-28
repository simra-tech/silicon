. "$(dirname "$0")/common.sh"
# B8: offset at VDDA 3.0 / 3.6 V (tt, ss, ff), then the mux sequence (full scale) at tt / ss / ff, after the proxy chain
until grep -q "chain105c done" $G1_RESULTS_ROOT/r1_adc/b8-campaign-105c.log; do sleep 30; done
N=sim/post/r1_adc_post_rc_mb8.spice
ofs() { # tag mos temp vdd tsuf vdda
  beh postb8-ofs-$1-v$(echo $6 | tr -d .) 105 $N --deck points --ref lay --noise none --vdda $6 --corner $2 --temp $3 --vdd $4 \
    --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq${5}_pre33.inc \
    --question "D23 offset (layout B8 dev1 extraction): first conversion 0 V, $1 VDDA $6 V, buffer + bandgap DC (no noise), behavioural SAR" \
    --disposition "post-layout value (static offset, D23 drift table, layout B8)"
}
for v in 3.0 3.6; do ofs tt mos_tt 27 1.2 "" $v; ofs ss125 mos_ss 125 1.08 _vdd108 $v; ofs ffm40 mos_ff -40 1.32 _vdd132 $v; done
beh postb8-isa-tt-rc 105 $N --deck isa --ref lay --question "post-layout RC (layout B8): mux sequence tt; gain, offset, full scale, IDD" --disposition "post-layout value (mux tt, layout B8)"
beh postb8-isa-ss125-rc 105 $N --deck isa --ref lay --corner mos_ss --temp 125 --vdd 1.08 --question "post-layout RC (layout B8): mux sequence ss125; full scale" --disposition "post-layout value (mux ss125, layout B8)"
beh postb8-isa-ffm40-rc 105 $N --deck isa --ref lay --corner mos_ff --temp -40 --vdd 1.32 --question "post-layout RC (layout B8): mux sequence ffm40; full scale" --disposition "post-layout value (mux ffm40, layout B8)"
echo chain105d done
