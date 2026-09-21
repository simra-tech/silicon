#!/usr/bin/env bash
# Monte Carlo offset run. Usage (repo root):
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/sim flow/run.sh bash run_sense_mc.sh run N TEMP SEED   (one job)
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_sense/sim flow/run.sh bash run_sense_mc.sh sum TEMP          (merge all seeds)
set -u
mkdir -p logs ../../../../../build/g1_sense
B=../../../../../build/g1_sense
if [ "$1" = run ]; then
  N=$2; T=$3; S=$4
  sed -e "s/@@N@@/$N/" -e "s/@@TEMP@@/$T/" -e "s/@@SEED@@/$S/" tb_sense_mc.cir > $B/sense_mc_${T}C_s$S.cir
  ngspice -b $B/sense_mc_${T}C_s$S.cir > logs/sense_mc_${T}C_s$S.log 2>&1
  exit
fi
T=$2
cat logs/sense_mc_${T}C_s*.log | grep "^MC[AB]" > results_sense_mc_${T}C.txt
python3 - results_sense_mc_${T}C.txt <<'PY' | tee -a results_sense_mc_${T}C.txt
import sys, statistics as st
lines=open(sys.argv[1]).read().splitlines()
rows=[l.split() for l in lines]
def val(r,k):
    if k not in r: return None
    i=r.index(k)+1
    if i>=len(r): return None          # ngspice occasionally drops a value from an echo line
    try: return float(r[i])
    except ValueError: return None
def col(k): return [v for v in (val(r,k) for r in rows) if v is not None]
print("# G1_SENSE offset MC, mos_tt_mismatch (lv+hv) + res_typ_mismatch, 27 C, seeds = one per log file (rndseed 1,2)")
for k in ("vos_tot_cm0=","vos_ota=","vped=","vos_tot_cm0.3="):
    v=col(k); print("%-16s n=%d mean=%+.3e sigma=%.3e min=%+.3e max=%+.3e" % (k, len(v), st.mean(v), st.pstdev(v), min(v), max(v)))
A={};B={};pairs=[]
for j,r in enumerate(rows):
    if r[0]=="MCA": a=val(r,"vos_tot_cm0=")
    if r[0]=="MCB" and j>0 and rows[j-1][0]=="MCA":
        b=val(r,"vos_tot_cm0.3=")
        if a is not None and b is not None: pairs.append(b-a)
print("cm_delta(0.3V)   n=%d mean=%+.3e sigma=%.3e  -> offset change for a 0.3 V common-mode step (resistor mismatch)" % (len(pairs), st.mean(pairs), st.pstdev(pairs)))
PY
