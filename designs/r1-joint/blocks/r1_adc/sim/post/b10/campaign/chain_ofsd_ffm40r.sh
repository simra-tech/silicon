#!/bin/sh
# B10 dev2c ffm40 on CPU 103 after the tt chain (CPU 105 is still held by the timed-out postb10-dg-bswz-ffm40 ngspice).
N=${N:-sim/post/r1_adc_post_rc_mb10c.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
until [ -f sim/post/runs/postb10d-isa-tt-rc/run.json ]; do sleep 30; done
beh postb10d-ofs-ffm40-v33r 103 --deck points --ref lay --noise none --vdda 3.3 --corner mos_ff --temp -40 --vdd 1.32 \
    --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq_vdd132_pre33.inc --timeout 3600 \
    --question "D23 offset (layout B10 extraction $N): first conversion 0 V, ffm40 VDDA 3.3 V, buffer + bandgap DC (no noise), behavioural SAR" \
    --disposition "post-layout value (static offset and drift, D23 / D30, layout B10)"
beh postb10d-isa-ffm40-rcr 103 --deck isa --ref lay --corner mos_ff --temp -40 --vdd 1.32 --timeout 3600 --question "post-layout RC (layout B10 dev2c): mux sequence ffm40; gain, offset, full scale, IDD" --disposition "post-layout value (full scale, layout B10 dev2c)"
