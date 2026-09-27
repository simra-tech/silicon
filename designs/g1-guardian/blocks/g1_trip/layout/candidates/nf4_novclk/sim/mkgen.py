#!/usr/bin/env python3
"""Write a g1_novclk generator variant (ngspice syntax, PDK devices as X instances; the CDL uses the same
devices with M prefix).  python3 mkgen.py <var> <n_long> <L_long> <Wn_long> <Wp_long> [<wp_nor> <wn_nor> <wp_inv> <wn_inv> <wp_nand> <wn_nand>]
Topology: clk -> n_long inverters with long L (odd count) -> sharpening inverter -> dly (in phase with clk)
          cks = NOT NOR(clk, dly) = OR(clk, dly);   ckh = NAND(clk, dly)"""
import sys, os
a = sys.argv[1:]
var, n, L, wn, wp = a[0], int(a[1]), a[2], a[3], a[4]
wpo, wno, wpi, wni, wpa, wna = (a[5:11] if len(a) >= 11 else ['2', '0.5', '4', '2', '1.5', '1'])
assert n % 2 == 1
lines = ['* g1_novclk variant %s: %d long-L stages (n %s/%s, p %s/%s) + sharpener; NOR p %s n %s; INV p %s n %s; NAND p %s n %s'
         % (var, n, wn, L, wp, L, wpo, wno, wpi, wni, wpa, wna),
         '.subckt g1_novclk clk cks ckh vdd vss']
prev = 'clk'
for i in range(n):
    o = 'dl%d' % (i + 1)
    lines += ['XMDP%d %s %s vdd vdd sg13_lv_pmos w=%su l=%su ng=1 m=1' % (i + 1, o, prev, wp, L),
              'XMDN%d %s %s vss vss sg13_lv_nmos w=%su l=%su ng=1 m=1' % (i + 1, o, prev, wn, L)]
    prev = o
lines += ['XMSP dly %s vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1' % prev,
          'XMSN dly %s vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1' % prev,
          # NOR2(clk, dly) -> norb
          'XMOP1 nor1 clk vdd vdd sg13_lv_pmos w=%su l=0.13u ng=1 m=1' % wpo,
          'XMOP2 norb dly nor1 vdd sg13_lv_pmos w=%su l=0.13u ng=1 m=1' % wpo,
          'XMON1 norb clk vss vss sg13_lv_nmos w=%su l=0.13u ng=1 m=1' % wno,
          'XMON2 norb dly vss vss sg13_lv_nmos w=%su l=0.13u ng=1 m=1' % wno,
          # soft clock = NOT norb
          'XMIP cks norb vdd vdd sg13_lv_pmos w=%su l=0.13u ng=1 m=1' % wpi,
          'XMIN cks norb vss vss sg13_lv_nmos w=%su l=0.13u ng=1 m=1' % wni,
          # hard clock = NAND2(clk, dly)
          'XMAP1 ckh clk vdd vdd sg13_lv_pmos w=%su l=0.13u ng=1 m=1' % wpa,
          'XMAP2 ckh dly vdd vdd sg13_lv_pmos w=%su l=0.13u ng=1 m=1' % wpa,
          'XMAN1 ckh clk nand1 vss sg13_lv_nmos w=%su l=0.13u ng=1 m=1' % wna,
          'XMAN2 nand1 dly vss vss sg13_lv_nmos w=%su l=0.13u ng=1 m=1' % wna,
          '.ends g1_novclk']
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'variants', 'g1_novclk_%s.spice' % var), 'w').write('\n'.join(lines) + '\n')
