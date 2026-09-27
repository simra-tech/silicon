#!/usr/bin/env bash
# usage: sweep.sh <outdir> <variant...>   (host side: writes decks; then run run_decks.sh in the container)
set -eu
OUT=$1; shift
for v in "$@"; do
  for c in "mos_tt 1.2 27" "mos_ss 1.08 -40" "mos_ff 1.32 125" "mos_ff 1.32 -40" "mos_ss 1.08 125"; do
    python3 "$(dirname "$0")/gen_sweep.py" "$OUT" "$v" $c
  done
done
