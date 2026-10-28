. "$(dirname "$0")/common.sh"
until grep -q "chain103a done" $G1_RESULTS_ROOT/r1_adc/b7-campaign-103a.log; do sleep 60; done
SS="--corner mos_ss --temp 125 --vdd 1.08"
d23 postb7-d23-ref-tt-buf 103 tt sim/post/r1_adc_post_rc_mb6.spice "R2-4 under D23, buffer run tt, 10 ref10 slots, behavioural SAR with the gate-level output timing (proxy), layout B7 (= B6 extraction)"
d23 postb7-d23-ref-tt-base 103 tt sim/post/r1_adc_post_rc_mb6_sp_tt.spice "R2-4 under D23, base run tt (slice reference ports ideal), 10 slots, proxy deck"
beh postb7-op-ss125-rc 103 --deck points --ref lay $SS --points sim/r5/points/ref10.json --op-only --probe-extra "v(xadc.xl.vref__p12) v(xadc.xl.vref__p13) v(xadc.xl.vref__p14) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p5) v(xadc.xl.vref__p15) v(xadc.xl.vref__p16) v(xadc.xl.vref__p17) v(xadc.xl.vrefl__p6) v(xadc.xl.vrefl__p7) v(xadc.xl.vss__p23) v(xadc.xl.vss__p27) v(xadc.xl.xslice_a.lsb_p)" --question "operating point ss125 with all slice reference port nodes (layout B7 = B6 extraction)" --disposition "post-layout op (RC)"
python3 sim/post/make_sp_netlist.py sim/post/r1_adc_post_rc_mb6.spice sim/post/r1_adc_post_rc_mb6_sp_ss125.spice postb7-op-ss125-rc --per-port || echo "FAILED make_sp ss125"
N=sim/post/r1_adc_post_rc_mb6_sp_ss125.spice beh postb7-op-ss125-sp 103 --deck points --ref lay $SS --points sim/r5/points/ref10.json --op-only --probe-extra "v(xadc.xl.vref__p12) v(xadc.xl.vref__p13) v(xadc.xl.vref__p14) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p5) v(xadc.xl.vref__p15) v(xadc.xl.vref__p16) v(xadc.xl.vref__p17) v(xadc.xl.vrefl__p6) v(xadc.xl.vrefl__p7) v(xadc.xl.vss__p23) v(xadc.xl.vss__p27) v(xadc.xl.xslice_a.lsb_p)" --question "R2-4 base netlist check ss125: slice reference ports forced at the buffer-OP values" --disposition "diagnosis"
d23 postb7-d23-ref-ss125-buf 103 ss125 sim/post/r1_adc_post_rc_mb6.spice "R2-4 under D23, buffer run ss/125 C/1.08 V, 10 slots, proxy deck" $SS
d23 postb7-d23-ref-ss125-base 103 ss125 sim/post/r1_adc_post_rc_mb6_sp_ss125.spice "R2-4 under D23, base run ss/125 C/1.08 V, 10 slots, proxy deck" $SS
echo chain103b done
