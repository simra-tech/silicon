#!/bin/sh
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/wif.sh"
until [ -f sim/post/runs/postb10-cr-ffm40-base/run.json ]; do sleep 60; done
echo "T2p: chain 104 reduced before start: CPU 104 is used for the B10 layout and checks; tail03 / sigsup03 run later on a free CPU"
