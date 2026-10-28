. "$(dirname "$0")/common.sh"
# B8 (dev1 extraction) R2-4 under D23, proxy deck of T2m: op runs, ideal-port base netlists, tt and ss buffer / base runs
until grep -q "chain105a done" $G1_RESULTS_ROOT/r1_adc/b8-campaign-105a.log && grep -q "chain105b done" $G1_RESULTS_ROOT/r1_adc/b8-campaign-105b.log; do sleep 30; done
N=sim/post/r1_adc_post_rc_mb8.spice
OPP="v(xadc.xl.vref__p12) v(xadc.xl.vref__p13) v(xadc.xl.vref__p14) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p5) v(xadc.xl.vref__p15) v(xadc.xl.vref__p16) v(xadc.xl.vref__p17) v(xadc.xl.vrefl__p6) v(xadc.xl.vrefl__p7) v(xadc.xl.vss__p23) v(xadc.xl.vss__p27) v(xadc.xl.xslice_a.lsb_p)"
SS="--corner mos_ss --temp 125 --vdd 1.08"
beh postb8-op-tt-rc 105 $N --deck points --ref lay --points sim/r5/points/ref10.json --op-only --probe-extra "$OPP" --question "post-layout RC (layout B8): operating point tt with all slice reference port nodes" --disposition "post-layout op (RC, layout B8)"
beh postb8-op-ss125-rc 105 $N --deck points --ref lay $SS --points sim/r5/points/ref10.json --op-only --probe-extra "$OPP" --question "post-layout RC (layout B8): operating point ss125 with all slice reference port nodes" --disposition "post-layout op (RC, layout B8)"
python3 sim/post/make_sp_netlist.py $N sim/post/r1_adc_post_rc_mb8_sp_tt.spice postb8-op-tt-rc --per-port
python3 sim/post/make_sp_netlist.py $N sim/post/r1_adc_post_rc_mb8_sp_ss125.spice postb8-op-ss125-rc --per-port
DISP="post-layout value (R2-4 under D23, proxy deck, layout B8)"
d23 postb8-d23-ref-tt-buf 105 tt $N "R2-4 under D23, buffer run tt, 10 ref10 slots, proxy deck, layout B8 extraction"
d23 postb8-d23-ref-tt-base 105 tt sim/post/r1_adc_post_rc_mb8_sp_tt.spice "R2-4 under D23, base run tt (slice reference ports ideal), 10 slots, proxy deck, layout B8"
d23 postb8-d23-ref-ss125-buf 105 ss125 $N "R2-4 under D23, buffer run ss/125 C/1.08 V, 10 slots, proxy deck, layout B8" $SS
d23 postb8-d23-ref-ss125-base 105 ss125 sim/post/r1_adc_post_rc_mb8_sp_ss125.spice "R2-4 under D23, base run ss/125 C/1.08 V (slice reference ports ideal), 10 slots, proxy deck, layout B8" $SS
echo chain105c done
