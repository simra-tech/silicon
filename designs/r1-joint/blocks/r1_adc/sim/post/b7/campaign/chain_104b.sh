. "$(dirname "$0")/common.sh"
waitrun postb6-win3072-tt-rc
for h in a b; do
beh postb7-inl$h-tt-rc 104 --deck points --ref lay-ideal --vref 1.045 --points sim/r5/points/inlramp5$h.json --question "post-layout RC (layout B7 = B6 extraction): reduced INL ramp half $h, tt, ideal VREF 1.045 V" --disposition "post-layout value (INL bow tt, layout B7)"
done
echo chain104b done
