#!/bin/sh
# Layout E5 (track T3): wiring-R-only netlist of one layout run (development view, no capacitance).
# The KLayout LVS runset of kpex 0.3.12 (sg13g2.lvs, with the options kpex uses) on the flat channel and top-only layouts,
# then pex/pex_rc_build.py with noc=1. kpex itself does not run LVS without an engine flag (pex-e5-dev14 try 1).
# usage (host, repo root): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh designs/r1-joint/blocks/r1_afe/pex/run_pexr.sh <layout run id> <pex run id>
set -u
LR=$1; PR=$2
cd "$(dirname "$0")/../../../../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; G1_CPUSET=${G1_CPUSET:-108}; G1_WORKDIR=designs/r1-joint/blocks/r1_afe
export G1_RESULTS_ROOT G1_CPUSET G1_WORKDIR
B=$G1_RESULTS_ROOT/r1_afe; L=$B/$LR; D=$B/$PR; mkdir -p $D
K=/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2/libs.tech/kpex/sg13g2.lvs
O="-rd thr=1 -rd run_mode=deep -rd spice_net_names=true -rd spice_comments=false -rd scale=false -rd verbose=false -rd schematic_simplify=false -rd net_only=false -rd top_lvl_pins=true -rd combine=false -rd combine_devices=false -rd purge=false -rd purge_nets=false -rd no_simplify=true"
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$L/r1_afe.gds -rd out=$D/r1_afe_ch_flat.gds -rd cell=r1_afe_ch > $D/prep_ch.log 2>&1
flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=$L/r1_afe.gds -rd out=$D/r1_afe_top_flat.gds -rd cell=top_only > $D/prep_top.log 2>&1
mkdir -p $D/lvs_ch/r1_afe_ch_flat__r1_afe_ch $D/lvs_top/r1_afe_top_flat__r1_afe
flow/run.sh klayout -b -r $K -rd input=$D/r1_afe_ch_flat.gds -rd report=$D/lvs_ch/r1_afe_ch_flat__r1_afe_ch/r1_afe_ch.lvsdb.gz -rd schematic=/work/designs/r1-joint/blocks/r1_afe/layout/r1_afe_lvs.cdl $O > $D/lvs_ch_console.log 2>&1; echo "kpex-deck lvs ch rc $?" >> $D/pexr.log
flow/run.sh klayout -b -r $K -rd input=$D/r1_afe_top_flat.gds -rd report=$D/lvs_top/r1_afe_top_flat__r1_afe/r1_afe.lvsdb.gz -rd schematic=/work/designs/r1-joint/blocks/r1_afe/layout/r1_afe_lvs.cdl $O > $D/lvs_top_console.log 2>&1; echo "kpex-deck lvs top rc $?" >> $D/pexr.log
flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=$D/lvs_ch/r1_afe_ch_flat__r1_afe_ch -rd ktopdir=$D/lvs_top/r1_afe_top_flat__r1_afe -rd ports=$L/r1_afe_ports.json -rd noc=1 -rd out=$D/pexr > $D/pexr_build.log 2>&1; echo "build rc $?" >> $D/pexr.log
echo done >> $D/pexr.log
