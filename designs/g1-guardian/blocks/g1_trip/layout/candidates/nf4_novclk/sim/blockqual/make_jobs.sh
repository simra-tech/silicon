#!/usr/bin/env bash
# Block qualification 2026-09-27: write the job list for dispatch.py (run from this directory with BULK set).
#   step 1  : decks from make_step1.sh (r4 and r3), ngspice -b from blocks/g1_trip/sim
#   window  : win_pex.py decks (candidate sim/), nominal controls + 30 seeds ss/1.08 V/-40 C (1001-1030) + 30 seeds ff/1.32 V/125 C (2001-2030)
#   kick    : review/redteam-20260927/trip_path/kick_rt.py worker, one bracket per job, tt, seeds 3001-3030, hard 200 / soft 153,
#             212 ns, VDDA 3.3 V, res_typ, start guess ud 0; the seed enters through the net argument (seed wrapper)
set -eu
: "${BULK:?}"; B=$BULK/r4-20260927/blockqual; HERE=$(pwd)
RUN="env G1_CPUSET={cpu} G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=$BULK G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim timeout 7200 flow/run.sh"
ng() { printf '%s\t%s sh -c '\''ngspice -b %s 2> %s.err | grep -av "Reference value" > %s.log'\''\n' "$1" "$RUN" "$2" "$2" "$2"; }
{
for d in $B/step1/r4_cmp* $B/step1/r4_settle_mos_tt* $B/step1/r4_dac* $B/step1/r3_cmp* $B/step1/r3_settle_mos_tt* $B/step1/r3_dac* $B/step1/r4_settle_mos_[sf]* $B/step1/r3_settle_mos_[sf]*; do ng s1_$(basename $d .cir) $d; done
mk() { mkdir -p $B/win/$1; python3 $HERE/../win_pex.py $B/win/$1 $2 $3 $4 $5 > /dev/null; ng win_$1 $B/win/$1/win_$3_$4V_$5C.cir; }
mk ctl_ss postlayout/g1_trip_nf4_novclk_pex.spice mos_ss 1.08 -40
mk ctl_ff postlayout/g1_trip_nf4_novclk_pex.spice mos_ff 1.32 125
mk ctlmm_ss $B/mm/seed1001.spice mos_ss 1.08 -40
for i in $(seq 1 30); do
  mk ss_s$((1000+i)) $B/mm/seed$((1000+i)).spice mos_ss_mismatch 1.08 -40
  mk ff_s$((2000+i)) $B/mm/seed$((2000+i)).spice mos_ff_mismatch 1.32 125
done
for i in $(seq 1 30); do s=$((3000+i)); for c in hard soft; do
  O=$B/kick/s${s}_$c; mkdir -p $O
  echo "mc$s $B/mm/seed$s.spice mos_tt_mismatch 1.2 27 $c 200 153 212 3.3 res_typ 0" > $O/q
  printf 'kick_s%s_%s\tBULK=%s python3 designs/g1-guardian/review/redteam-20260927/trip_path/kick_rt.py worker {cpu} %s %s/q\n' $s $c "$BULK" $O $O
done; done
} > $B/jobs.txt
wc -l $B/jobs.txt
