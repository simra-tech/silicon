#!/bin/sh
. "$(dirname "$0")/common.sh"; . "$(dirname "$0")/wif.sh"
for v in sig05 tail03; do for c in tt ffm40; do wif $v 105 $c; done; done
