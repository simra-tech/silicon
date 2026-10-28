#!/bin/sh
# Code-level R2-4 (D30 item 2) at ff / -40 C / 1.32 V on the B7 extraction: base run (slice reference ports ideal at the
# ff operating point postb10-op-ffm40-b7). Deck limit as chain_cr103.sh.
. "$(dirname "$0")/common.sh"
FF="--corner mos_ff --temp -40 --vdd 1.32"
d23 postb10-cr-ffm40-base 104 ffm40 sim/post/r1_adc_post_rc_mb6_sp_ffm40.spice "code-level R2-4 (D30 item 2), base run ff / -40 C / 1.32 V (slice reference ports ideal), 10 slots, proxy deck, layout B7" $FF --timeout 5700
