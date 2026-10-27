# T2l layout B6 post-layout campaign (sourced by chain_*.sh). Run from anywhere; POSIX sh.
# usage (host): G1_RESULTS_ROOT=<bulk>; export G1_RESULTS_ROOT; sh sim/post/b6/campaign/chain_10X.sh (one chain per CPU 103 / 104 / 105)
cd "$(dirname "$0")/../../../.."   # designs/r1-joint/blocks/r1_adc
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT}"; export G1_RESULTS_ROOT
N=sim/post/r1_adc_post_rc_mb6.spice
D=sim/post/b5/decks/b6s4
beh() { # id cpu args...
  id=$1; cpu=$2; shift 2
  python3 sim/post/run_post.py --id $id --cpu $cpu --core lay --netlist $N --solver sparse "$@" || echo "FAILED $id"
}
gl() { # id cpu deck timeout question
  python3 sim/post/b6/run_b6.py --id $1 --cpu $2 --deck $D/$3.cir --timeout $4 --question "$5" || echo "FAILED $1"
}
