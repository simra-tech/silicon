#!/usr/bin/env python3
"""C169 standalone DAC deck generator (v3, b2 boundary, parallel Nx=1 units).
Terminal order is FIXED HERE: XSW d g s b -> XSW?? {node} {gate} {vseg} VSS.
A fix applied only to a deck, not its generator, returns on the next rebuild."""
import hashlib, subprocess, re

NUN = 150         # unary units of 4 LSB each (600 codes / 4), b1 boundary
NUNBITS = 4       # LSB per unary unit
NBIN = 2          # binary bits b0..b1 (handover margin 2.58->3.78 row corrected: b1 = 4 LSB, 1.2 pc parts with >=1 reversal)
VREF = 0.6404     # from the TOTAL: 0.3503 uA/unit (0.20 mV LSB @ 285.5 ohm), exp correction -9.6 mV

L = []
add = L.append
add('* C169 standalone v5: b1 boundary, HBT differential-pair steering (no nmos pass switches);')
add('* unary from b2 up: 4-LSB units, each 4x Nx=1 in parallel; pair steers on the logic differential.')
add('.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib hbt_typ_mismatch')
add('.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ')
add('.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib mos_tt_mismatch')
add('.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt_mismatch')
add('VCC_HBT VCC_HBT 0 DC 2.500')
add('VSS VSS 0 DC 0')
add(f'VREF ref 0 DC {VREF}')
add('VCODE code 0 DC 0')
add('XRLP VCC_HBT c_p sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1')
add('XRLN VCC_HBT c_n sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1')
for k in range(NBIN):                   # binary b0..b1: 2^k parallel Nx=1 units
    for u in range(2**k):
        add(f'XQB{k}_{u} vsegb{k} ref e_dacb{k} sub! npn13G2 Nx=1 mm_ok=1')
    add(f'XRCB{k} e_dacb{k} VSS sub! rppd w=1.0u l=5.4u m=1 b=0 mm_ok=1')
    add(f'XQPb{k} c_p bbar{k} vsegb{k} sub! npn13G2 Nx=1 mm_ok=1')
    add(f'XQNb{k} c_n b{k} vsegb{k} sub! npn13G2 Nx=1 mm_ok=1')
for j in range(1, NUN + 1):             # unary: NUNBITS x Nx=1 per unit
    for u in range(NUNBITS):
        add(f'XQU{j}_{u} vsegu{j} ref e_dacu{j} sub! npn13G2 Nx=1 mm_ok=1')
    add(f'XRCU{j} e_dacu{j} VSS sub! rppd w=1.037u l=5.4u m=4 b=0 mm_ok=1')
    add(f'XQPu{j} c_p ubar{j} vsegu{j} sub! npn13G2 Nx=1 mm_ok=1')
    add(f'XQNu{j} c_n u{j} vsegu{j} sub! npn13G2 Nx=1 mm_ok=1')
for k in range(NBIN):
    d = 2**k
    add(f'EB{k} b{k} 0 VALUE {{floor((v(code)*100+0.5)/{d})-2*floor((v(code)*100+0.5)/{2*d})}}')
    add(f'EBB{k} bbar{k} 0 VALUE {{1-(floor((v(code)*100+0.5)/{d})-2*floor((v(code)*100+0.5)/{2*d}))}}')
for j in range(1, NUN + 1):
    add(f'EU{j} u{j} 0 VALUE {{floor((v(code)*100+0.5)/{NUNBITS}) >= {j}}}')
    add(f'EUB{j} ubar{j} 0 VALUE {{1-(floor((v(code)*100+0.5)/{NUNBITS}) >= {j})}}')
add('.temp 27')
deck = '\n'.join(L) + '\n.end\n'
open('/tmp/c169-dac-standalone3.cir', 'w').write(deck)
print('generated, hash', hashlib.sha256(deck.encode()).hexdigest()[:16])
