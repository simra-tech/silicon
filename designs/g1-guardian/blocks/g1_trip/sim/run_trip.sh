#!/usr/bin/env bash
# G1_TRIP simulations. Usage (repo root):
#   G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim flow/run.sh bash run_trip.sh <what> [args]
# what: delay [corners] | dac | dacmc [N] | cmpmc N VCM SEED | cmpmc_sum VCM | kick
set -u
mkdir -p logs ../../../../../build/g1_trip
B=../../../../../build/g1_trip
what=${1:-delay}
delay_run() { # MOS VDD VCM TEMP FCLK(MHz)
  local T=$(python3 -c "print(1e-6/$5)"); local TH=$(python3 -c "print(0.5e-6/$5)")
  local T2=$(python3 -c "print(20e-9+1e-6/$5)"); local TF=$(python3 -c "print(20e-9+0.5e-6/$5)")
  local TF1=$(python3 -c "print(21e-9+0.5e-6/$5)"); local TE=$(python3 -c "print(20e-9+1.9e-6/$5)")
  tag="cmp_delay_$1_$2V_cm$3_$4C_$5MHz"
  sed -e "s/@@MOS@@/$1/" -e "s/@@VDD@@/$2/" -e "s/@@VCM@@/$3/" -e "s/@@TEMP@@/$4/" -e "s/@@TPER@@/$T/g" -e "s/@@THALF@@/$TH/g" \
      -e "s/@@T2@@/$T2/g" -e "s/@@TFLIP@@/$TF/g" -e "s/@@TFLIP1@@/$TF1/g" -e "s/@@TEND@@/$TE/g" tb_cmp_delay.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > logs/$tag.log 2>&1
  echo "== $tag"; grep "^DELAY" logs/$tag.log
}
case $what in
delay)
  { echo "# comparator delay, $(date -u +%FT%H:%MZ)"
    for cm in 0.5 0.75 1.0; do delay_run mos_tt 1.2 $cm 27 10; done
    delay_run mos_tt 1.2 0.5 27 5
    if [ "${2:-}" = corners ]; then
      for T in -40 85 125 175; do delay_run mos_tt 1.2 0.5 $T 10; done
      delay_run mos_ss 1.08 0.5 175 10; delay_run mos_ss 1.08 0.5 -40 10; delay_run mos_ff 1.32 0.5 27 10
      delay_run mos_ss 1.08 0.5 175 5
    fi
  } | tee results_cmp_delay.txt ;;
dac)
  { echo "# DAC transfer/settling/impedance, $(date -u +%FT%H:%MZ)"
    for c in "mos_tt res_typ 27" "mos_ss res_wcs 175" "mos_ff res_bcs -40"; do set -- $c
      sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@TEMP@@/$3/" tb_dac.cir > $B/dac_$1_$2_$3.cir
      ngspice -b $B/dac_$1_$2_$3.cir > logs/dac_$1_$2_$3.log 2>&1
      echo "== dac $1 $2 $3C"; grep -E "^(DAC|ROUT|SETTLE)" logs/dac_$1_$2_$3.log
    done
  } | tee results_dac.txt ;;
dacmc)
  N=${2:-100}
  # string-only subckt extracted from the schematic netlist (resistors only; the mux carries no DC current)
  { echo ".subckt g1_dac8_string vref vss"; grep "^XRU" netlist/g1_dac8.spice; echo ".ends"; } > netlist/g1_dac8_string.spice
  python3 - $N <<'PY'
import sys
n=int(sys.argv[1]); taps=" ".join("v(x1.t%d)"%k for k in range(256))
d=open("tb_dac_mc.cir").read().replace("@@N@@",str(n)).replace("@@TEMP@@","27")
# replace the placeholder inner loop by a print of all taps
import re
d=re.sub(r"  let inlmax = 0\n.*?  end\n", "  print %s\n" % taps, d, flags=re.S)
open("../../../../../build/g1_trip/dac_mc.cir","w").write(d)
PY
  ngspice -b $B/dac_mc.cir > logs/dac_mc_n$N.log 2>&1
  python3 - logs/dac_mc_n$N.log <<'PY' | tee results_dac_mc.txt
import sys,re,statistics as st
log=open(sys.argv[1]).read()
samples=[]; cur={}
for m in re.finditer(r"v\(x1\.t(\d+)\) = (-?[0-9.]+e[-+][0-9]{2})", log):
    k=int(m.group(1)); cur[k]=float(m.group(2))
    if k==255:
        if len(cur)==256: samples.append([cur[i] for i in range(256)])
        cur={}
inl=[];dnl=[];lsbs=[];ped=[];fs=[]
for t in samples:
    lsb=(t[255]-t[0])/255; lsbs.append(lsb); ped.append(t[0]); fs.append(t[255])
    inl.append(max(abs((t[k]-t[0])/lsb-k) for k in range(256)))
    dnl.append(max(abs((t[k+1]-t[k])/lsb-1) for k in range(255)))
print("# DAC string MC (rppd res_typ_mismatch), n=%d samples, endpoint-fit" % len(samples))
print("LSB mean=%.6f V sigma=%.3e ; tap0 mean=%.5f sigma=%.2e ; tap255 mean=%.5f sigma=%.2e" % (st.mean(lsbs),st.pstdev(lsbs),st.mean(ped),st.pstdev(ped),st.mean(fs),st.pstdev(fs)))
print("INL_max |LSB|: mean=%.4f max=%.4f ; DNL_max |LSB|: mean=%.4f max=%.4f" % (st.mean(inl),max(inl),st.mean(dnl),max(dnl)))
PY
  ;;
cmpmc)
  N=${2:-25}; CM=${3:-0.75}; SEED=${4:-1}
  PWL=$(python3 -c "
pts=['0 -0.016']
for k in range(1,65):
    t=70e-9+(k-1)*100e-9; v=-0.016+0.0005*k
    pts.append('%.4e %.6f %.4e %.6f'%(t,-0.016+0.0005*(k-1),t+1e-9,v))
print(' '.join(pts))")
  sed -e "s/@@N@@/$N/" -e "s/@@VCM@@/$CM/" -e "s/@@TEMP@@/27/" -e "s/@@SEED@@/$SEED/" -e "s/@@PWL@@/$PWL/" tb_cmp_mc.cir > $B/cmp_mc_cm${CM}_s$SEED.cir
  ngspice -b $B/cmp_mc_cm${CM}_s$SEED.cir > logs/cmp_mc_cm${CM}_s$SEED.log 2>&1
  ;;
cmpmc_sum)
  CM=${2:-0.75}
  cat logs/cmp_mc_cm${CM}_s*.log | grep "^MC" > results_cmp_mc_cm$CM.txt
  python3 - results_cmp_mc_cm$CM.txt <<'PY' | tee -a results_cmp_mc_cm$CM.txt
import sys,statistics as st
v=[float(l.split()[-1]) for l in open(sys.argv[1]) if "vos_V=" in l]
print("# comparator offset MC (mos_tt_mismatch, 27C, 10 MHz, 0.5 mV staircase, seeds one per log) n=%d" % len(v))
print("Vos mean=%+.3e V sigma=%.3e V min=%+.3e max=%+.3e" % (st.mean(v),st.pstdev(v),min(v),max(v)))
PY
  ;;
kick)
  { echo "# kickback, $(date -u +%FT%H:%MZ)"
    for vsh in 0.0300 0.0250 0.0498; do
      sed -e "s/@@VSH@@/$vsh/" tb_kickback.cir > $B/kick_$vsh.cir
      ngspice -b $B/kick_$vsh.cir > logs/kick_$vsh.log 2>&1
      echo "== Vsh=$vsh"; grep -E "^(QUIET|KICK|DECISION)" logs/kick_$vsh.log
    done
  } | tee results_kickback.txt ;;
esac
