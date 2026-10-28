#!/bin/sh
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/wif.sh"
until [ -f sim/post/runs/postb10-cr-ffm40-buf/run.json ]; do sleep 60; done
for v in int03 out03; do for c in tt ffm40; do wif $v 103 $c; done; done
