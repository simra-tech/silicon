#!/bin/sh
# Code-level R2-4 (D30 item 2) at ff / -40 C / 1.32 V on the B7 extraction: buffer run.
# Deck limit: tstop 7.73 us at the measured 0.164 us per wall minute of postb7-d23-ref-ss125-buf (CPU 103) = 47 min;
# ff rate not measured on this deck, so +100 % -> 5700 s.
. "$(dirname "$0")/common.sh"
FF="--corner mos_ff --temp -40 --vdd 1.32"
d23 postb10-cr-ffm40-buf 103 ffm40 sim/post/r1_adc_post_rc_mb6.spice "code-level R2-4 (D30 item 2), buffer run ff / -40 C / 1.32 V, 10 ref10 slots, proxy deck, layout B7 (= B6 extraction)" $FF --timeout 5700
