# T2n layout B8 post-layout campaign (sourced by chain_*.sh). POSIX sh.
# usage (host): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh sim/post/b8/campaign/chain_<name>.sh
cd "$(dirname "$0")/../../../.."   # designs/r1-joint/blocks/r1_adc
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
PROBES="v(xadc.xl.vref__p13) v(xadc.xl.vref__p16) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p6)"
d23() { # id cpu corner-tag netlist question [flags...]   (D23 proxy deck of T2m: behavioural SAR with gate-level timing)
  id=$1; cpu=$2; ct=$3; nl=$4; q=$5; shift 5
  python3 sim/post/run_post.py --id $id --cpu $cpu --deck points --core lay --netlist $nl --solver sparse --ref lay \
    --points sim/r5/points/ref10.json --save full --save-extra "$PROBES $(cat sim/post/b7/save_d23.txt)" \
    --post-include sim/post/b7/r1_adc5_post_d23_$ct.spice --core-cell r1_adc5_core_lay_d23 "$@" \
    --question "$q" --disposition "$DISP" || echo "FAILED $id"
}
beh() { # id cpu netlist args...   (behavioural SAR, sim/post/run_post.py)
  id=$1; cpu=$2; nl=$3; shift 3
  python3 sim/post/run_post.py --id $id --cpu $cpu --core lay --netlist $nl --solver sparse "$@" || echo "FAILED $id"
}
