#!/usr/bin/env python3
"""Post-layout netlist and decks of r1_isense (host python3, standard library).

  python3 make_post.py <pex rc dir> <deck out dir>

1. <pex rc dir>/r1_isense_post.spice: the netlist of record (schematic/r1_isense.spice) with the body of subckt
   r1_isense_ch replaced by the extracted channel (pex_build.py: layout devices, wiring R, kpex 2.5D C, MIM from the
   netlist). The r1_isense top (two identical channel instances) is unchanged: both channels use the same extraction.
2. Post-layout copies of the revision-2 decks in <deck out dir>: tb_isense_dc.cir (include line replaced), and from sim/gen_tb_isense_stb.py (R1_NET = the post netlist): stbpre, stb, stbaz, stbstep, stbcm. The
   loop-gain probes are inserted as in the schematic decks, but by terminal nets: the driver-side terminals of the
   extracted devices (XMOx/XMLx drains on outp/outn, XCCx on outp/outn, XM1/XM2 gates on sa/sb, XMF1 gate on vcms,
   XA1/XA2 gates on h1/h2) move to the probe node; the probe source connects it to the net's main node. Those terminals
   lose their own wiring resistance (Metal, a few ohms); everything else is the full RC netlist.
"""
import os, re, sys, importlib.util
PEX, OUTD = sys.argv[1:3]
VAR = sys.argv[3] if len(sys.argv) > 3 else ''      # '' full RC, '_c' devices + C (wiring R shorted), '_r' devices + R
HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.abspath(os.path.join(HERE, '..', '..'))
REC = os.path.join(BLK, 'schematic', 'r1_isense.spice')
ext = open(os.path.join(PEX, 'r1_isense_ch_pex%s.spice' % VAR)).read()
a = ext.index('.subckt r1_isense_ch '); b = ext.index('.ends', a)
body_ext = ext[a:b] + '.ends r1_isense_ch'
# ---- layout revision c: the extracted channel has the ports vss (quiet), vss_o, vss_sw. The post-layout r1_isense_ch
# keeps the 12 ports of the netlist of record: the quiet pin becomes the internal node vssq, and the block-level wiring
# from each channel port to the star at the block vss pin (top cell r1_isense, not in the channel extraction) is added
# as resistors estimated by square count and via count (layout/r1_isense_layout.py top_returns; Metal2-4 0.088 ohm/sq,
# 9 ohm per Via cut, sg13g2_typ.itf as pex_build.py). STAR = channel A (default) or B (gap star + feed down the vss_o
# column), from the environment variable R1_STAR.
STAR = {
    # channel A: quiet trunk stub 1.4 um (0.08); vss_o: column 0.10 + 2x2 Via3 2.25 + 2x2 Via2 2.25 + bar 0.32 + 3x2 Via2
    # 1.5 + 3x2 Via3 1.5 = 7.9; vss_sw: 2 Via2 4.5 + bar 0.45 + 3 Via2 3.0 + 3 Via3 3.0 = 11.0 (ohm)
    'a': dict(rq=0.08, ro=7.9, rsw=11.0, feed=0.0),
    # channel B: gap star: quiet 6 Via3 1.5 + 6 Via2 1.5 + bar 0.3 + 4 Via2 2.25 + 4 Via3 2.25 = 7.8; vss_sw 4 Via3 2.25;
    # vss_o 0; feed = vss_o column gap -> channel A landing 145 um / 1.2 um = 10.6 + channel A's landing path 7.8 = 18.4
    'b': dict(rq=7.8, ro=0.0, rsw=2.25, feed=18.4)}
# layout c, Kelvin pedestal reference (2026-10-26): the channel port vss_k (vss end of the RPA arm) runs on its own
# Metal3 line (router wire 0.30 um) to the landing at the block vss pin stub. Square count from the generator
# (r1_isense_layout.json top.kelvin.paths): channel A 10.4 um = 35 sq, channel B 156 um = 520 sq; 0.088 ohm/sq,
# no via. It joins the pin directly, not the star.
RK = {'a': 3.1, 'b': 45.8}
SPLIT = ' vss_o ' in body_ext.split('\n', 1)[0] + ' '
if SPLIT:
    sv = STAR[os.environ.get('R1_STAR', 'a')]
    L = body_ext.split('\n')
    hdr = L[0].split()
    KEL = hdr[-1] == 'vss_k'
    if KEL:
        hdr = hdr[:-1]
    assert hdr[-3:] == ['vss', 'vss_o', 'vss_sw'], hdr
    out = [' '.join(hdr[:-2])]
    for ln in L[1:-1]:
        f = ln.split()
        if f and not ln.startswith('*'):
            f = ['vssq' if x == 'vss' else x for x in f]
            ln = ' '.join(f)
        out.append(ln)
    out += ['* ---- layout c: block-level star wiring (estimated, see make_post.py STAR, channel %s)' % os.environ.get('R1_STAR', 'a'),
            'Rstar_q vssq vstar %g' % max(sv['rq'], 1e-4), 'Rstar_o vss_o vstar %g' % max(sv['ro'], 1e-4),
            'Rstar_sw vss_sw vstar %g' % max(sv['rsw'], 1e-4), 'Rstar_feed vstar vss %g' % max(sv['feed'], 1e-4)]
    if KEL:
        out += ['* ---- layout c: Kelvin line of the RPA arm to the block vss pin (estimated, RK, channel %s)'
                % os.environ.get('R1_STAR', 'a'), 'Rkelvin vss_k vss %g' % RK[os.environ.get('R1_STAR', 'a')]]
    out += [L[-1]]
    body_ext = '\n'.join(out)
rec = open(REC).read()
a = rec.index('.subckt r1_isense_ch '); b = rec.index('.ends r1_isense_ch', a) + len('.ends r1_isense_ch')
post = ('* r1_isense POST-LAYOUT netlist: netlist of record with r1_isense_ch replaced by the layout extraction\n'
        '* (layout/pex/pex_build.py + make_post.py); r1_ls kept for reference (unused inside the extracted channel)\n'
        + rec[:a] + body_ext + rec[b:])
POST = os.path.join(PEX, 'r1_isense_post%s.spice' % VAR)
open(POST, 'w').write(post)
os.makedirs(OUTD, exist_ok=True)
INC = '.include /work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice'
for d in ('tb_isense_dc.cir',):
    t = open(os.path.join(BLK, 'sim', d)).read()
    assert t.count(INC) == 1
    open(os.path.join(OUTD, d), 'w').write(t.replace(INC, '.include ' + POST))
    # layout b: the same deck with a fixed bias current @@IBIAS@@ (r1_bias output range 3.5-7.7 uA, INTERFACES.md)
    IBL = 'Ibias vdda ibias dc {5u*(@@TEMP@@+273.15)/300.15}'
    assert t.count(IBL) == 1
    open(os.path.join(OUTD, d.replace('.cir', '_ib.cir')), 'w').write(
        t.replace(INC, '.include ' + POST).replace(IBL, '* r1_bias output (sweep over its PVT range 3.5-7.7 uA, fixed per run)\nIbias vdda ibias dc @@IBIAS@@'))

# ---- stb decks
PINS = set('isp isn outp outn vref vcm ibias az_lv azh_lv vdda vdd vss'.split())


def net_of(node):
    return re.sub(r'__[pi]\d+$', '', node)


import json
MAIN = json.load(open(os.path.join(PEX, 'r1_isense_ch_pex_rnets.json')))['mainnode']


def main_of(net):
    return MAIN.get(net, net)


RULES = [  # (kind, gate net, other S/D or cap net, net to move, new node)  terminal on `move` -> new node
    ('mos', 'x1a', 'outp', 'outp', 'outpi'), ('mos', 'x1b', 'outn', 'outn', 'outni'),
    ('mos', 'vbl', 'outp', 'outp', 'outpi'), ('mos', 'vbl', 'outn', 'outn', 'outni'),
    ('cap', 'cza', 'outp', 'outp', 'outpi'), ('cap', 'czb', 'outn', 'outn', 'outni'),
    ('mos', 'sa', 'f1', 'sa', 'sai'), ('mos', 'sb', 'f2', 'sb', 'sbi'),
    ('mos', 'vcms', 'vcmfb', 'vcms', 'vcmsy'),
    ('mos', 'h1', 'f1', 'h1', 'h1g'), ('mos', 'h2', 'f2', 'h2', 'h2g')]


def stb_sub_post(hold):
    s = body_ext.replace('.subckt r1_isense_ch ', '.subckt r1_isense_ch_stb ')
    out, hits = [], {}
    for ln in s.splitlines():
        f = ln.split()
        if ln.startswith('XM') and len(f) >= 6:
            d, g, sr, bb = f[1:5]
            for k, (kind, gn, on, mv, new) in enumerate(RULES):
                if kind != 'mos' or net_of(g) != gn or on not in (net_of(d), net_of(sr)):
                    continue
                if mv == gn:
                    f[2] = new
                else:
                    if net_of(d) == mv:
                        f[1] = new
                    if net_of(sr) == mv:
                        f[3] = new
                hits[k] = hits.get(k, 0) + 1
            ln = ' '.join(f)
        elif ln.startswith('Xxc') and 'cap_cmim' in ln:
            for k, (kind, gn, on, mv, new) in enumerate(RULES):
                if kind == 'cap' and {net_of(f[1]), net_of(f[2])} == {gn, on}:
                    f[1 if net_of(f[1]) == mv else 2] = new
                    hits[k] = hits.get(k, 0) + 1
            ln = ' '.join(f)
        out.append(ln)
    assert sorted(hits) == list(range(len(RULES))), ('probe rules without a device', hits)
    m = main_of
    P = ['* ---- loop-gain probes (test only; Tian double injection), post-layout: probe node <-> net main node',
         'Vpop outpi %s dc 0 ac {vo_p}' % m('outp'), 'Vpon outni %s dc 0 ac {vo_n}' % m('outn'),
         'Ipop 0 outpi dc 0 ac {io_p}', 'Ipon 0 outni dc 0 ac {io_n}',
         'Vpsa %s sai dc 0 ac {vi_p}' % m('sa'), 'Vpsb %s sbi dc 0 ac {vi_n}' % m('sb'),
         'Ipsa 0 %s dc 0 ac {ii_p}' % m('sa'), 'Ipsb 0 %s dc 0 ac {ii_n}' % m('sb'),
         'Vpc %s vcmsy dc 0 ac {vc}' % m('vcms'), 'Ipc 0 %s dc 0 ac {ic}' % m('vcms'),
         'Vpq1 %s h1g dc 0 ac {va_p}' % m('h1'), 'Vpq2 %s h2g dc 0 ac {va_n}' % m('h2'),
         'Ipq1 0 %s dc 0 ac {ja_p}' % m('h1'), 'Ipq2 0 %s dc 0 ac {ja_n}' % m('h2')]
    if hold:
        P += ['Lhd1 %s hd1 1G' % m('h1'), 'Vhd1 hd1 0 dc @@VH1@@', 'Lhd2 %s hd2 1G' % m('h2'), 'Vhd2 hd2 0 dc @@VH2@@']
    txt = '\n'.join(out)
    return txt.replace('.ends r1_isense_ch', '\n'.join(P) + '\n.ends r1_isense_ch_stb')


os.environ['R1_NET'] = POST
spec = importlib.util.spec_from_file_location('gstb', os.path.join(BLK, 'sim', 'gen_tb_isense_stb.py'))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
G.stb_sub = stb_sub_post
# node names used by the analysis lines of the decks (xa.h1 etc.): map to the extracted main nodes
def fix(t):
    for n in ('sa', 'sb', 'h1', 'h2', 'vcms'):
        t = t.replace('xa.%s)' % n, 'xa.%s)' % main_of(n)).replace('xdut.%s)' % n, 'xdut.%s)' % main_of(n))
    return t
open(os.path.join(OUTD, 'tb_isense_stbpre.cir'), 'w').write(fix(G.PRE))
open(os.path.join(OUTD, 'tb_isense_stb.cir'), 'w').write(fix(G.stb_deck(False, [1, 2, 3, 4, 5], 'stb', 'r1_isense POST-LAYOUT loop gain, NORMAL state (az = azh = 0), shunt levels 0 / +100 mV / -20 mV')))
open(os.path.join(OUTD, 'tb_isense_stbaz.cir'), 'w').write(fix(G.stb_deck(True, [1, 2, 3, 6, 7], 'stbaz', 'r1_isense POST-LAYOUT loop gain, AZ CLOSED state (az = azh = 1), zero shunt current')))
open(os.path.join(OUTD, 'tb_isense_stbazi.cir'), 'w').write(fix(G.stb_deck(True, [1, 2, 3, 6, 7], 'stbazi', 'r1_isense POST-LAYOUT loop gain, INTERMEDIATE state (az = 1, azh = 0: RF arms at VCM, hold open), zero shunt current', azh=False)))
# layout b: cross-check deck for the input-gate break (loop 4): besides the Tian return ratio it writes the single
# voltage-injection ratio Tv = -v(network side)/v(gate side) of the same probe. At the gate the load side draws no DC
# current, so Tv equals the loop gain at low frequency and is independent of the Tian current-injection run.
_d = fix(G.stb_deck(False, [1, 4], 'stbdiag', 'r1_isense POST-LAYOUT loop gain cross-check at the input gates (Tian and voltage-only ratio), normal state'))
_a = '    let tdb = db(tl)'
_b = 'wrdata @@OUT@@_t$&fid tdb tph'
assert _d.count(_a) == 1 and _d.count(_b) == 1
_d = _d.replace(_a, _a + '\n    let tv = -v1/(v1-1)\n    let tvdb = db(tv)\n    let tvph = 180/pi*cph(tv)').replace(_b, _b + ' tvdb tvph')
open(os.path.join(OUTD, 'tb_isense_stbdiag.cir'), 'w').write(_d)
open(os.path.join(OUTD, 'tb_isense_stbstep.cir'), 'w').write(G.STEP)
open(os.path.join(OUTD, 'tb_isense_stbcm.cir'), 'w').write(G.CMSTEP)
print('wrote', POST, 'and decks in', OUTD)
