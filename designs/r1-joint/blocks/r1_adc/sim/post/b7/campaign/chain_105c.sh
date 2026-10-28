. "$(dirname "$0")/common.sh"
waitrun postb6-win1024-tt-rc
SS="--corner mos_ss --temp 125 --vdd 1.08"; FF="--corner mos_ff --temp -40 --vdd 1.32"
P="--deck points --points sim/r5/points/fixtt.json"
# D23 drift diagnosis (offset tt -8.5, ff +1.5 LSB): schematic reference at the three corners (no layout)
for c in tt ss125 ffm40; do
  case $c in tt) F=""; TS="";; ss125) F="$SS"; TS="_vdd108";; ffm40) F="$FF"; TS="_vdd132";; esac
  python3 sim/post/run_post.py --id postb7-dsch-$c --cpu 105 --core recfast --ref ideal --vref 1.045 $P $F --timing r1_adc_timing_r5_n0_cq${TS}_pre33.inc \
    --question "D23 drift diagnosis: schematic (netlist of record, r1_adc5_core_fast) first conversion 0 V at $c, ideal VREF 1.045 V" --disposition "diagnostic only" || echo "FAILED postb7-dsch-$c"
done
# layout: every top-plate coupling moved to gnd and the comparator / lsb pairs balanced, tt and ff
for c in tt ffm40; do
  case $c in tt) F=""; TS="";; ffm40) F="$FF"; TS="_vdd132";; esac
  N=sim/post/b7/diag_mb7_e7all.spice beh postb7-de7all-$c 105 --ref lay-ideal --vref 1.045 $P $F --timing r1_adc_timing_r5_n0_cq${TS}_pre33.inc \
    --question "D23 drift diagnosis: B7 extraction with every top-plate coupling to gnd and the pairs balanced, first conversion 0 V at $c" --disposition "diagnostic only"
  beh postb7-dbase-$c 105 --ref lay-ideal --vref 1.045 $P $F --timing r1_adc_timing_r5_n0_cq${TS}_pre33.inc \
    --question "D23 drift diagnosis: B7 extraction as is, ideal VREF (lay-ideal), first conversion 0 V at $c" --disposition "diagnostic only"
done
echo diag105 done
# ff gate-level first conversion: measured 0.0096 us per wall minute (b6-ms-fc-ffm40-f0); 1.86 us -> 194 min; limit +30 % = 252 min
gl b7-ms-fc-ffm40 105 sim/post/b5/decks/b6s4/fc_ffm40.cir 15200 "first conversion, bit-exact and output window at ff / -40 C / 1.32 V, gate-level SAR, layout B7 (= B6 extraction), both frames; limit sized from the measured 0.0096 us/min plus 30 %"
echo chain105c done
