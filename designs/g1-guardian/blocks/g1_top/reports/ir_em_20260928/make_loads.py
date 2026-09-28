#!/usr/bin/env python3
"""Load cases (sink currents per block supply pin group, amperes) for the chip-level IR/EM solve.

All values are simulated; none is measured. Sources:
  [q]  r4 full-chip layout-netlist deck, c_mid tt/27 C, armed quiet window 13.86-16 us, SUPPLY_uA / T2F lines of
       blocks/g1_top/sim/logs/cdl_c_mid_pex_tt_27C_gear_compact_cdle060c0c5_rtleco20260925_icx_maxstep1ns_functional_r4a.tail.txt
  [qo] same deck with the transistor-level oscillator, tt/27 C (..._osctl_..._r4a.tail.txt): osc 115.0 uA
  [m]  maximum over every chip-level log in blocks/g1_top/sim/logs with a SUPPLY_uA line (795 logs: r4 CDL deck and
       the c1414 hand-wired matrix; tt/ss/ff, -40..125 C, supply extremes): bgr 484.0 uA, sense 1704 uA (ff/125 C),
       t2f 54.37 uA / 2.605 uA, osc 150.3 uA (ff/-40 C, 1.32 V), trip 7.117 uA / 0.0946 uA, gate 0.117 uA / 0.0092 uA,
       IOVDD quiescent 139.9 uA
  [e]  trip event on the r4 CDL deck (results/waves, c_mid tt/ss125/ff-40): VDDA total peak minus its quiet average,
       largest at ss/125 C: 2.566 - 1.729 mA = 0.837 mA, added to SENSE; GATE pad current (v(gate)-v(gfet))/10 Ohm,
       peaks 29.6 mA sink / 29.2 mA source at tt, 39.5 / 38.3 mA at ff/-40 C -> 40 mA
  [d]  digital macro, OpenROAD report_power on the ECO macro (this record, psm/): typ 1.2 V 10 MHz vectorless
       1.152 mW -> 0.960 mA; bound fast 1.32 V -40 C 12.44 MHz activity 1.0 on every net 3.31 mW -> 2.51 mA
  [r]  rated pad drive (sg13g2_io cell names): TEMP_OUT 16 mA, SDO 4 mA, FAULT_N 4 mA, taken simultaneously with GATE
  [b]  bounds: SENSE_P/N input current <= 3.3 V / 9.97 kOhm (G1_SENSE input rppd) = 0.331 mA; VREF pad current
       <= 0.1 mA (BGR586 output resistance 22 kOhm into the external 10 nF: 48 uA at 1.05 V, doubled)
Every block's supply current returns on VSS (VDD and VDDA blocks), every IO-cell IOVDD current on IOVSS.
"""
import json, sys
from pathlib import Path
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
u = 1e-6; m = 1e-3
IO_DIG = ['Xpad10_gate', 'Xpad11_fault_n', 'Xpad12_en', 'Xpad14_sclk', 'Xpad15_sdi', 'Xpad16_sdo', 'Xpad17_temp_out']
Q = dict(vdd=dict(Xi_core_u_digital=0.960 * m, Xi_core_u_osc=115.0 * u, Xi_core_u_trip=5.158 * u, Xi_core_u_t2f=0.303 * u, Xi_core_u_gate=0.0037 * u),
         vdda=dict(Xi_core_u_bgr=319.707 * u, Xi_core_u_sense=1101.38 * u, Xi_core_u_t2f=41.72 * u, Xi_core_u_trip=0.0045 * u, Xi_core_u_gate=0.00056 * u),
         iovdd={p: 128.17 * u / len(IO_DIG) for p in IO_DIG})
W = dict(vdd=dict(Xi_core_u_digital=2.51 * m, Xi_core_u_osc=150.3 * u, Xi_core_u_trip=7.117 * u, Xi_core_u_t2f=2.605 * u, Xi_core_u_gate=0.117 * u),
         vdda=dict(Xi_core_u_bgr=484.0 * u, Xi_core_u_sense=(1704 + 837) * u, Xi_core_u_t2f=54.37 * u, Xi_core_u_trip=0.0946 * u, Xi_core_u_gate=0.0092 * u),
         iovdd={p: 139.9 * u / len(IO_DIG) for p in IO_DIG})
for p, i in (('Xpad10_gate', 40 * m), ('Xpad17_temp_out', 16 * m), ('Xpad16_sdo', 4 * m), ('Xpad11_fault_n', 4 * m)):
    W['iovdd'][p] += i
def vss(c):
    s = {}
    for d in (c['vdd'], c['vdda']):
        for k, v in d.items(): s[k] = s.get(k, 0.0) + v
    return s
L = dict(VDD=dict(quiescent=Q['vdd'], trip_worst=W['vdd']),
         VDDA=dict(quiescent=Q['vdda'], trip_worst=W['vdda']),
         VSS=dict(quiescent=vss(Q), trip_worst=vss(W)),
         IOVDD=dict(quiescent=Q['iovdd'], trip_worst=W['iovdd']),
         IOVSS=dict(quiescent=Q['iovdd'], trip_worst=W['iovdd']),
         GATE=dict(trip_worst={"Xpad10_gate@TopMetal1+TopMetal2": 40 * m}),
         SENSE_P=dict(trip_worst=dict(Xi_core_u_sense=0.331 * m)),
         SENSE_N=dict(trip_worst=dict(Xi_core_u_sense=0.331 * m)),
         VREF=dict(trip_worst=dict(Xpad18_vref=0.1 * m)),
         i_core_vref=dict(trip_worst=dict(Xpad18_vref=0.1 * m, Xi_core_u_sense=1 * u, Xi_core_u_t2f=1 * u)))
for net, cases in L.items():
    (out / ('%s.json' % net)).write_text(json.dumps(cases, indent=1) + '\n')
(out / 'all_loads.json').write_text(json.dumps(L, indent=1) + '\n')
print({n: {c: '%.4g A' % sum(v.values()) for c, v in cs.items()} for n, cs in L.items()})
