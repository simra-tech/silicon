#!/bin/sh
# B10 dev2c: offset (D23 deck) then full scale (mux deck, D16 amendment) at tt on CPU 103. Full-scale limit: measured
# 1115 s for postb8-isa-ffm40-rc, x 3 -> 3600 s.
N=${N:-sim/post/r1_adc_post_rc_mb10c.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
until grep -q "pex chain done" $G1_RESULTS_ROOT/r1_adc/t2p-logs/chain_pex104_dev2c.log; do sleep 30; done

ofs postb10d-ofs 103 tt mos_tt 27 1.2 "" 3.3
beh postb10d-isa-tt-rc 103 --deck isa --ref lay --corner mos_tt --temp 27 --vdd 1.2 --timeout 3600 --question "post-layout RC (layout B10 dev2c): mux sequence tt; gain, offset, full scale, IDD" --disposition "post-layout value (full scale, layout B10 dev2c)"
