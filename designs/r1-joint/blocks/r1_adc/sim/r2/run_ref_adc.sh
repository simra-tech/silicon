#!/bin/sh
# run_ref_adc.sh <cpu>: tb_adc2_ref.cir with r1_refbuf and with the ideal VREF at the buffer DC level
cd "$(dirname "$0")/../.."
O="OPTS=reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12"
B="--sub CORNER=mos_tt --sub TEMP=27 --sub VDD=1.2 --sub TSTOP=8.7u --sub TMAX=0.2n --sub VSTART=0 --sub VSTEP=0 --sub CORE=r1_adc2_core_fast --sub TIMING=r1_adc_timing_r2.inc"
python3 sim/run_ngspice.py --deck sim/r2/tb_adc2_ref.cir --run-id r2-ref-adc-tt-buf-a --cpuset $1 $B --sub "$O" \
  --sub "REFLINES=Vdda vdda 0 3.3
Vbg vbg 0 1.045
XREF vbg vref vdda 0 r1_refbuf msf=16 mib=80 ndec=6 ncg=1" --sub REFMODE=buf \
  --question "ADC conversions (both slices, real CDAC switching) with VREF from r1_refbuf (msf 16, mib 80, 44 pF MIM)"
python3 sim/run_ngspice.py --deck sim/r2/tb_adc2_ref.cir --run-id r2-ref-adc-tt-ideal-a --cpuset $1 $B --sub "$O" \
  --sub "REFLINES=Vref vref 0 1.003997" --sub REFMODE=ideal \
  --question "ADC conversions with an ideal VREF at the buffer DC level 1.003997 V (reference for r2-ref-adc-tt-buf-a)"
