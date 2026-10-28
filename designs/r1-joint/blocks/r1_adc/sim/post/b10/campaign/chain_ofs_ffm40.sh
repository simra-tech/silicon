#!/bin/sh
N=${N:-sim/post/r1_adc_post_rc_mb10.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
ofs postb10-ofs 105 ffm40 mos_ff -40 1.32 "_vdd132" 3.3
