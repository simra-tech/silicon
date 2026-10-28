. "$(dirname "$0")/common.sh"
# B8: static windows 1024 and 3072 at tt (B4 window centres, ideal VREF), after the offset chain on CPU 104
until grep -q "chain104a done" $G1_RESULTS_ROOT/r1_adc/b8-campaign-104a.log; do sleep 30; done
N=sim/post/r1_adc_post_rc_mb8.spice
for w in 1024 3072; do
beh postb8-win$w-tt-rc 104 $N --deck points --ref lay-ideal --vref 1.045 --points sim/post/points/winb4_$w.json --question "post-layout RC (layout B8): static window at code $w, tt, ideal VREF 1.045 V, B4 window centres" --disposition "post-layout value (static window tt, layout B8)"
done
echo chain104b done
