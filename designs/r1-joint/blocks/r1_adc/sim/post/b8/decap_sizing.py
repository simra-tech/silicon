#!/usr/bin/env python3
"""T2n (D25 step 1): size the local decoupling of the slice reference ports from the per-step CDAC charge and the
allowed reference error at the comparator strobe (0.25 LSB). Arithmetic only (charge-sharing bound: the B7 proxy
waveforms show the port droop still growing at the strobe, so no recovery before the strobe is assumed).
Inputs: netlist-of-record CDAC (schematic/r1_adc_r5.spice r1_cdac3_side), extracted node C of layout A/B (README),
the B7 measured droop at the strobe (postb7-d23-ref-tt-buf probes). usage: decap_sizing.py OUT.json"""
import json, sys
CU = 22.04e-15            # unit MIM 3.78 x 3.78 um (r1_cdac3_side)
CB = 27.5e-15             # bridge 4.23 x 4.23 um
VREF, VREFL = 1.050, 1.058  # slice-port DC values (B7 op run)
C_L = 127.5 * CU + CB + 64e-15          # LSB-array node: units + bridge + wiring C (layout A/B extraction)
C_T = 31 * CU + CB + 60e-15             # top plate: MSB units + bridge + wiring C
LSB_PER_LCU = 1.23        # one LSB-array unit in LSB (Cb / C_L attenuation against the 128-LSB MSB unit)
LSB_PER_MCU = 128.0
MIM = 1.5e-15             # F / um2 (PDK typical, area term)
OUT = {}
# LSB array (vrefl): bit j switches vrefl -> gnd with all lower LSB-array units still on vrefl (worst charge)
rows = []
units = [(7, 64), (6, 32), (5, 16), (4, 8), (3, 4), (2, 2), (1, 1), (0, 0.5)]
on = 127.5
for j, n in units:
    on -= n
    dvl = VREFL * n * CU / C_L                     # LSB-node step
    dq = dvl * on * CU                              # charge into the units that stay on vrefl
    dec = 13 - j                                    # decision whose strobe follows this switch
    imb = n * LSB_PER_LCU                           # P - N weight on vrefl after the switch (one side switched)
    dmax = 0.25 * VREFL / imb                       # allowed vrefl error at the strobe
    rows.append(dict(bit=j, units=n, decision=dec, dq_pC=round(dq * 1e12, 4), allowed_mV=round(dmax * 1e3, 3),
                     c_req_pF=round(dq / dmax * 1e12, 1)))
OUT['vrefl_per_slice'] = rows
# MSB array (vref): decisions 5..13 count (D23 metric); the MSB switches before decision 5 are C12..C9 (decisions 1-4,
# covered by the redundancy); C8 (1 unit) precedes decision 5. Its vref imbalance is the residue of decisions 1-4
# (up to 15 units = 1920 LSB at full-scale inputs, ref10 slots up to +-0.88 V).
dv = VREF * CU / C_T
dq8 = dv * 29 * CU
imb = 15 * LSB_PER_MCU
dmax = 0.25 * VREF / imb
OUT['vref_per_slice'] = dict(bit=8, decision=5, dq_pC=round(dq8 * 1e12, 4), allowed_mV=round(dmax * 1e3, 4),
                             c_req_pF=round(dq8 / dmax * 1e12, 1),
                             note='plus the vref disturbance coupled from the vrefl step through the shared follower gate ng (B7: -1.3 to -1.9 mV at decisions 6-8)')
creq_l = max(r['c_req_pF'] for r in rows)
creq_v = OUT['vref_per_slice']['c_req_pF']
OUT['required_pF_per_slice'] = dict(vrefl=creq_l, vref=creq_v)
area = 2 * (creq_l + creq_v) * 1e-12 / MIM
OUT['required_mim_um2_two_slices'] = round(area)
OUT['box_um2'] = round(439.0 * 205.42)
OUT['existing_decap_pF'] = dict(vref=4 * 4900 * MIM * 1e12, vrefl=2 * 4900 * MIM * 1e12)
OUT['label'] = 'arithmetic (estimate), not simulated; check: B7 measured vrefl droop at the decision-7 strobe -30 mV, ' \
               'predicted error 30 mV x 96 units x 1.23 LSB / 1.058 V = 3.3 LSB from vrefl alone (measured 4.30 LSB total)'
json.dump(OUT, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(OUT, indent=1))
