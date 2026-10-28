#!/bin/sh
# B10 dev2c: offset (D23 deck) then full scale (mux deck, D16 amendment) at ffm40 on CPU 105. Full-scale limit: measured
# 1115 s for postb8-isa-ffm40-rc, x 3 -> 3600 s.
N=${N:-sim/post/r1_adc_post_rc_mb10c.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
until grep -q "pex chain done" $G1_RESULTS_ROOT/r1_adc/t2p-logs/chain_pex104_dev2c.log; do sleep 30; done
until [ -f sim/post/runs/postb10-dg-bswz-ffm40/run.json ]; do sleep 30; done
ofs postb10d-ofs 105 ffm40 mos_ff -40 1.32 "_vdd132" 3.3
beh postb10d-isa-ffm40-rc 105 --deck isa --ref lay --corner mos_ff --temp -40 --vdd 1.32 --timeout 3600 --question "post-layout RC (layout B10 dev2c): mux sequence ffm40; gain, offset, full scale, IDD" --disposition "post-layout value (full scale, layout B10 dev2c)"
