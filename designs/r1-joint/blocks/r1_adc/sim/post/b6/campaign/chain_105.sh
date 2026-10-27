. "$(dirname "$0")/common.sh"
beh postb6-fc-tt-rc 105 --deck points --ref lay-ideal --vref 1.045 --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq_pre33.inc --question "post-layout RC (layout B6): first conversion tt 0 V, 33 ns hold; behavioural SAR reference for the gate-level run" --disposition "post-layout value (first conversion tt, layout B6)"
beh postb6-fc-ss125-rc 105 --deck points --ref lay-ideal --vref 1.045 --corner mos_ss --temp 125 --vdd 1.08 --points sim/post/points/ffb.json --timing r1_adc_timing_r5_n0_cq_vdd108_pre33.inc --question "post-layout RC (layout B6): first conversion ss/125 C/1.08 V, -0.80 V; behavioural SAR reference" --disposition "post-layout value (first conversion ss125, layout B6)"
beh postb6-isa-tt-rc 105 --deck isa --ref lay --question "post-layout RC (layout B6): mux sequence tt; gain, offset, full scale, IDD" --disposition "post-layout value (mux tt, layout B6)"
beh postb6-isa-ss125-rc 105 --deck isa --ref lay --corner mos_ss --temp 125 --vdd 1.08 --question "post-layout RC (layout B6): mux sequence ss125; gain, offset, full scale" --disposition "post-layout value (mux ss125, layout B6)"
beh postb6-isa-ffm40-rc 105 --deck isa --ref lay --corner mos_ff --temp -40 --vdd 1.32 --question "post-layout RC (layout B6): mux sequence ffm40; gain, offset, full scale" --disposition "post-layout value (mux ffm40, layout B6)"
gl b6-ms-fc-tt 105 fc_tt 7200 "first conversion tt 0 V, gate-level SAR, layout B6 (bit-exact vs postb6-fc-tt-rc, output window)"
gl b6-ms-fc-ss125 105 fc_ss125 7200 "first conversion ss/125 C/1.08 V, gate-level SAR, layout B6 (bit-exact vs postb6-fc-ss125-rc, output window)"
echo chain105 done
