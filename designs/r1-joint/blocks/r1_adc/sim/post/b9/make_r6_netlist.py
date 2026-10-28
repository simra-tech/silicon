#!/usr/bin/env python3
"""T2o (PLAN.md D28, 2026-10-28): revision-6 what-if variants of an extracted r1_adc netlist (all three top subckts
r1_adc_lay, r1_adc_lay_pr, r1_adc_lay_sar are changed the same way). Diagnostic and pre-layout checks only; the
post-layout numbers of record come from the B9 extraction.
  --strobe r6        revision-6 comparator strobe: the input of the r1_cmp4_clkgen delay chain (gates of xckg_xpd0 /
                     xckg_xnd0) moves from clk to vss, so the chain output x is constantly high and
                     mclk = NAND(clk, x) = NOT clk: the comparator resets at the rising clk edge (same gate as before)
                     and evaluates from the falling edge (16.67 ns) to the next rising edge.
  --buf NET:k,...    multiply m of the buffer devices: vrefl -> xref_xmsfl_s* and xref_xmibl_s* (r1_refbuf msfl / mibl),
                     vref -> xref_xmsf_s* and xref_xmib_s* (msf / mib), dec -> xref_xcd_u*, decl -> xref_xcdl_u*,
                     cg -> xref_xcg_u*. Width-scaled devices keep their extracted wiring (an estimate of the drawn change).
  --r-scale NETS:k   multiply the extracted wiring R (lines Rw<k> / Rt<k>) of the nets in NETS (comma list) by k
usage: make_r6_netlist.py <in.spice> <out.spice> [--strobe r6] [--buf vrefl:3,vref:1] [--r-scale vref,vrefl:0.5] ..."""
import re, sys
src, out = sys.argv[1], sys.argv[2]
opt = sys.argv[3:]
strobe = None; buf = {}; scale = {}
for i, o in enumerate(opt):
    if o == '--strobe':
        strobe = opt[i + 1]
    if o == '--buf':
        for kv in opt[i + 1].split(','):
            k, v = kv.split(':'); buf[k] = float(v)
    if o == '--r-scale':
        s, k = opt[i + 1].split(':')
        for n in s.split(','):
            scale[n] = float(k)
DEV = {'vrefl': ('xref_xmsfl_s', 'xref_xmibl_s'), 'vref': ('xref_xmsf_s', 'xref_xmib_s'), 'dec': ('xref_xcd_u',),
       'decl': ('xref_xcdl_u',), 'cg': ('xref_xcg_u',)}
def net(n):
    return re.sub(r'__[pi]\d+$', '', n)
n_ck = n_m = n_r = 0
L = []
for ln in open(src).read().split('\n'):
    t = ln.split(' ')
    if strobe == 'r6' and re.match(r'Xxckg_x[pn]d0 ', ln):
        assert net(t[2]) == 'clk', ln
        t[2] = 'vss'; ln = ' '.join(t); n_ck += 1
    for k, f in buf.items():
        for pre in DEV[k]:
            if re.match(r'X%s\d+ ' % pre, ln):
                mm = re.search(r' m=(\d+)', ln)
                newm = int(mm.group(1)) * f
                assert abs(newm - round(newm)) < 1e-9, (ln, f)
                ln = ln[:mm.start()] + ' m=%d' % round(newm) + ln[mm.end():]; n_m += 1
    if scale and re.match(r'R[wt]\d+ ', ln):
        na, nb = net(t[1]), net(t[2])
        if na in scale or nb in scale:
            t[3] = '%.6g' % (float(t[3]) * scale.get(na, scale.get(nb))); ln = ' '.join(t); n_r += 1
    L.append(ln)
hdr = '* %s: revision-6 what-if variant of %s (%s; sim/post/b9/make_r6_netlist.py): %d clkgen gates moved, %d device m scaled, %d R scaled' % (
    out.split('/')[-1], src.split('/')[-1], ' '.join(opt), n_ck, n_m, n_r)
open(out, 'w').write(hdr + '\n' + '\n'.join(L))
print(hdr)
