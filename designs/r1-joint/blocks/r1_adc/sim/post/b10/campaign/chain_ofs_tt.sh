#!/bin/sh
N=${N:-sim/post/r1_adc_post_rc_mb10.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
ofs postb10-ofs 103 tt mos_tt 27 1.2 "" 3.3
