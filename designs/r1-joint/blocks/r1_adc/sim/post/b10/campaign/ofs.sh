# D23 offset deck (first conversion 0 V, buffer + bandgap DC, no noise, behavioural SAR) on a B10 extraction.
# ofs <id-prefix> <cpu> <tag> <mos> <temp> <vdd> <timing suffix> <vdda>; limit 3600 s (measured 1279 s, postb8-ofs-ffm40-v33)
ofs() {
  beh $1-$3-v$(echo $8 | tr -d .) $2 --deck points --ref lay --noise none --vdda $8 --corner $4 --temp $5 --vdd $6 \
    --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq${7}_pre33.inc --timeout 3600 \
    --question "D23 offset (layout B10 extraction $N): first conversion 0 V, $3 VDDA $8 V, buffer + bandgap DC (no noise), behavioural SAR" \
    --disposition "post-layout value (static offset and drift, D23 / D30, layout B10)"
}
