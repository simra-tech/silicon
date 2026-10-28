. "$(dirname "$0")/common.sh"
waitrun postb6-win1024-tt-rc
# ff gate-level first conversion: measured 0.0096 us per wall minute (b6-ms-fc-ffm40-f0); 1.86 us -> 194 min; limit +30 % = 252 min
gl b7-ms-fc-ffm40 105 sim/post/b5/decks/b6s4/fc_ffm40.cir 15200 "first conversion, bit-exact and output window at ff / -40 C / 1.32 V, gate-level SAR, layout B7 (= B6 extraction), both frames; limit sized from the measured 0.0096 us/min plus 30 %"
echo chain105b done
