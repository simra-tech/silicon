. "$(dirname "$0")/common.sh"
until grep -q "chain103b done" $G1_RESULTS_ROOT/r1_adc/b7-campaign-103b.log; do sleep 60; done
beh postb7-inlb-tt-rc 103 --deck points --ref lay-ideal --vref 1.045 --points sim/r5/points/inlramp5b.json --question "post-layout RC (layout B7 = B6 extraction): reduced INL ramp half b, tt, ideal VREF 1.045 V" --disposition "post-layout value (INL bow tt, layout B7)"
echo chain103d done
