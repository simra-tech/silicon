#!/bin/sh
# B10 dev2c static window at code 3072, tt, ideal VREF 1.045 V (B4 window centres) on CPU 103 after postb10d-isa-ffm40-rcr.
# Limit 30000 s: measured 12845 s (postb8-win1024-tt-rc) and 8875 s (postb8-win3072-tt-rc), x 2.3.
N=${N:-sim/post/r1_adc_post_rc_mb10c.spice}
. "$(dirname "$0")/common.sh"
until [ -f sim/post/runs/postb10d-isa-ffm40-rcr/run.json ]; do sleep 30; done
beh postb10d-win3072-tt-rc 103 --deck points --ref lay-ideal --vref 1.045 --points sim/post/points/winb4_3072.json --timeout 30000 \
  --question "post-layout RC (layout B10 dev2c): static window at code 3072, tt, ideal VREF 1.045 V, B4 window centres" \
  --disposition "post-layout value (static window, layout B10 dev2c)"
