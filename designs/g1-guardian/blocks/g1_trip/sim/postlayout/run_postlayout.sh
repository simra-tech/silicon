#!/usr/bin/env bash
# Post-layout runs of G1_TRIP on the kpex 2.5D CC netlist (g1_trip_pex.spice).
# Usage (repo root): G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim flow/run.sh bash postlayout/run_postlayout.sh [dac|cmp|all]
# (tb_trip_cmp_sch.cir is the same comparator deck on the schematic netlist sim/netlist/g1_trip.spice, for the reference column)
set -u
mkdir -p postlayout/logs ../../../../../build/g1_trip/postlayout
B=../../../../../build/g1_trip/postlayout
what=${1:-all}
dac() { # MOS RES TEMP
  tag="pex_dac_$1_$2_$3C"
  sed -e "s/@@MOS@@/$1/" -e "s/@@RES@@/$2/" -e "s/@@TEMP@@/$3/" postlayout/tb_trip_dac_pex.cir > $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"
  python3 - postlayout/logs/$tag.log <<'PY'
import sys, re
log = open(sys.argv[1]).read()
v = {}
for m in re.finditer(r"DACS code= +(\d+) +out= +(-?[0-9.e+-]+) +err_LSB= +(-?[0-9.e+-]+) +iref_uA= +(-?[0-9.e+-]+)", log):
    v[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
if len(v) == 256:
    t = [v[k][0] for k in range(256)]
    lsb = (t[255] - t[0]) / 255
    inl = [(t[k] - t[0]) / lsb - k for k in range(256)]
    dnl = [(t[k + 1] - t[k]) / lsb - 1 for k in range(255)]
    print("DACS 256 codes: code0=%.5f V code128=%.5f V code255=%.5f V LSB=%.4f mV I(VREF)=%.2f uA" % (t[0], t[128], t[255], lsb * 1e3, v[128][2]))
    print("DACS endpoint fit: INL max |%.3f| LSB (code %d), DNL max |%.3f| LSB (code %d); absolute error vs 1.04*(255+code)/530: min %.3f max %.3f LSB"
          % (max(inl, key=abs), max(range(256), key=lambda k: abs(inl[k])), max(dnl, key=abs), max(range(255), key=lambda k: abs(dnl[k])) + 1,
             min(x[1] for x in v.values()), max(x[1] for x in v.values())))
else:
    print("DACS: %d of 256 codes found" % len(v))
for line in log.splitlines():
    if line.startswith("DACH") or line.startswith("SETTLE"):
        print(line)
PY
}
cmp() { # MOS VDD TEMP FCLK(MHz) [sch]
  local T=$(python3 -c "print(1e-6/$4)"); local TH=$(python3 -c "print(0.5e-6/$4)")
  local T2=$(python3 -c "print(20e-9+1e-6/$4)"); local TE=$(python3 -c "print(20e-9+1.45e-6/$4)")
  local deck=postlayout/tb_trip_cmp_pex.cir; local pfx=pex
  if [ "${5:-}" = sch ]; then deck=postlayout/tb_trip_cmp_sch.cir; pfx=sch; fi
  tag="${pfx}_cmp_delay_$1_$2V_$3C_$4MHz"
  sed -e "s/@@MOS@@/$1/" -e "s/@@VDD@@/$2/" -e "s/@@TEMP@@/$3/" -e "s/@@TPER@@/$T/g" -e "s/@@THALF@@/$TH/g" \
      -e "s/@@T2@@/$T2/g" -e "s/@@TEND@@/$TE/g" $deck > $B/$tag.cir
  ngspice -b $B/$tag.cir > postlayout/logs/$tag.log 2>&1
  echo "== $tag"; grep -E "^(VTH|DELAY|KICK)" postlayout/logs/$tag.log
}
{
echo "# G1_TRIP post-layout results (kpex 2.5D CC), $(date -u +%Y-%m-%dT%H:%MZ), $(ngspice -v | grep -o 'ngspice-[0-9]*')"
if [ "$what" = cmp ] || [ "$what" = all ]; then
  # 5 MHz strobe (the specified comparator clock): the hard comparator's kick on icmp comes 100 ns
  # before the measured soft strobe; at 10 MHz it is only 50 ns before and the 1 mV overdrive is lost
  # in the kick residue (the schematic netlist behaves the same, see the sch_ runs)
  cmp mos_tt 1.2 27 5 sch
  cmp mos_tt 1.2 27 5
  cmp mos_ss 1.08 -40 5 sch
  cmp mos_ss 1.08 -40 5
fi
if [ "$what" = dac ] || [ "$what" = all ]; then
  dac mos_tt res_typ 27
fi
} | tee -a postlayout/results_postlayout.txt
