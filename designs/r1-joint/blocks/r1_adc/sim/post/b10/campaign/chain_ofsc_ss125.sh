#!/bin/sh
N=${N:-sim/post/r1_adc_post_rc_mb10.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"

ofs postb10c-ofs 104 ss125 mos_ss 125 1.08 "_vdd108" 3.3
