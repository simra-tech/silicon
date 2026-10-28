# T2p layout B10 / code-level R2-4 campaign (sourced by chain_*.sh). POSIX sh.
# usage (host): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh sim/post/b10/campaign/chain_<name>.sh
cd "$(dirname "$0")/../../../.."   # designs/r1-joint/blocks/r1_adc
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
N=${N:-sim/post/r1_adc_post_rc_mb6.spice}
beh() { # id cpu args...   (behavioural SAR, sim/post/run_post.py)
  id=$1; cpu=$2; shift 2
  python3 sim/post/run_post.py --id $id --cpu $cpu --core lay --netlist $N --solver sparse "$@" || echo "FAILED $id"
}
PROBES="v(xadc.xl.vref__p13) v(xadc.xl.vref__p16) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p6)"
d23() { # id cpu corner-tag netlist question [corner flags...]   (D23 proxy deck of T2m: behavioural SAR with gate-level timing)
  id=$1; cpu=$2; ct=$3; nl=$4; q=$5; shift 5
  python3 sim/post/run_post.py --id $id --cpu $cpu --deck points --core lay --netlist $nl --solver sparse --ref lay \
    --points sim/r5/points/ref10.json --save full --save-extra "$PROBES $(cat sim/post/b7/save_d23.txt)" \
    --post-include sim/post/b7/r1_adc5_post_d23_$ct.spice --core-cell r1_adc5_core_lay_d23 "$@" \
    --question "$q" --disposition "post-layout value (code-level R2-4, D30 item 2, proxy deck)" || echo "FAILED $id"
}
