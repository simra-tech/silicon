#!/bin/sh
# Layout E8 (track T3l): fast C estimate (kpex --magic CC, about 15 s) of the flat channel of an R-view run (run_pexr.sh),
# then pex/pair_loads_magic.py. Used to place the x1 C trim before the kpex 2.5D extraction; not a record.
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/run_magic_c.sh <pex run id> <label>
set -u
PR=$1; LAB=$2
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=${G1_CPUSET:-108}; G1_WORKDIR=designs/r1-joint/blocks/r1_afe
export G1_RESULTS_ROOT G1_CPUSET G1_WORKDIR
D=$G1_RESULTS_ROOT/r1_afe/$PR
flow/run.sh kpex --pdk ihp-sg13g2 --threads 1 --gds $D/r1_afe_ch_flat.gds --schematic layout/r1_afe_lvs.cdl --cell r1_afe_ch --magic --magic_mode CC --out_dir $D/magic > $D/magic_console.log 2>&1
python3 designs/r1-joint/blocks/r1_afe/pex/pair_loads_magic.py $LAB=$D/magic/r1_afe_ch_flat__r1_afe_ch/magic_CC/r1_afe_ch.pex.spice
