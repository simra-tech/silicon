#!/bin/sh
N=${N:-sim/post/r1_adc_post_rc_mb10.spice}
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/ofs.sh"
until [ -f sim/post/runs/postb10-ofs-ffm40-v33/run.json ]; do sleep 30; done
ofs postb10c-ofs 105 ffm40 mos_ff -40 1.32 "_vdd132" 3.3
