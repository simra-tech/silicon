# T2m layout B7 post-layout campaign (sourced by chain_*.sh). POSIX sh.
# usage (host): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh sim/post/b7/campaign/chain_<name>.sh
cd "$(dirname "$0")/../../../.."   # designs/r1-joint/blocks/r1_adc
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
N=${N:-sim/post/r1_adc_post_rc_mb6.spice}
beh() { # id cpu args...   (behavioural SAR, sim/post/run_post.py)
  id=$1; cpu=$2; shift 2
  python3 sim/post/run_post.py --id $id --cpu $cpu --core lay --netlist $N --solver sparse "$@" || echo "FAILED $id"
}
# corner table: tag process temp vdd timing-suffix
ofs() { # id-prefix cpu tag mos temp vdd tsuf vdda
  beh $1-$3-v$(echo $8 | tr -d .) $2 --deck points --ref lay --noise none --vdda $8 --corner $4 --temp $5 --vdd $6 \
    --points sim/r5/points/fixtt.json --timing r1_adc_timing_r5_n0_cq${7}_pre33.inc \
    --question "D23 offset (layout B7 set): first conversion 0 V, $3 VDDA $8 V, buffer + bandgap DC (no noise), behavioural SAR" \
    --disposition "post-layout value (static offset, D23 drift table)"
}
waitrun() { # wait until sim/post/runs/<id>/run.json exists (a run of another chain finished)
  until [ -f sim/post/runs/$1/run.json ]; do sleep 60; done
}
gl() { # id cpu deck timeout question   (gate-level SAR, runner sim/post/b6/run_b6.py)
  python3 sim/post/b6/run_b6.py --id $1 --cpu $2 --deck $3 --timeout $4 --question "$5" || echo "FAILED $1"
}
PROBES="v(xadc.xl.vref__p13) v(xadc.xl.vref__p16) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p6)"
d23() { # id cpu corner-tag netlist question [corner flags...]   (D23 proxy: behavioural SAR with gate-level timing)
  id=$1; cpu=$2; ct=$3; nl=$4; q=$5; shift 5
  python3 sim/post/run_post.py --id $id --cpu $cpu --deck points --core lay --netlist $nl --solver sparse --ref lay \
    --points sim/r5/points/ref10.json --save full --save-extra "$PROBES $(cat sim/post/b7/save_d23.txt)" \
    --post-include sim/post/b7/r1_adc5_post_d23_$ct.spice --core-cell r1_adc5_core_lay_d23 "$@" \
    --question "$q" --disposition "post-layout value (R2-4 under D23, proxy deck)" || echo "FAILED $id"
}
