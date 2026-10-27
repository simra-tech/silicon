#!/usr/bin/env python3
"""T2 post-layout harness (2026-10-26): write the wrapper sim/post/r1_adc5_post.spice and the deck variants
sim/post/tb_post_points.cir and sim/post/tb_post_isa.cir from the revision-5 decks (sim/r5/tb_adc5_points.cir,
sim/r5/tb_adc5_isa.cir). Pure Python; run on the host after any change of the layout contract.

Wrapper r1_adc5_core_lay: the pins of r1_adc5_core (same order) + vbg nb vdda. Inside:
  * XL = r1_adc_lay_pr (layout-mapped or post-layout netlist; ports TOP_PORTS + vref vrefl), XSAR = r1_sar5_logic of the
    netlist of record, connected through the sar_* nets of the layout contract.
  * clk = clk30; ain_* = sinp ... isbn; vref_in = vbg; ibias = nb; vss = gnd.
  * vrefa = vref and vrefla = vrefl of the laid-out r1_refbuf5 (internal nets, probe ports). vrefb / vreflb are
    E-source copies (no load) for the post-processors that read v(vrefb) / v(vreflb). A deck must not drive vrefb /
    vreflb. The ideal-reference base runs drive vrefa and vrefla with ideal sources (the buffer stays connected and
    biased; the source holds the node).
  * The 35 unconnected checklist pins and vcm / vcm2 (no internal net in the layout) are tied to gnd by 1 kOhm
    (stand-in for the r1_ctrl drivers / the CM source; it matters only once parasitic coupling to them exists).
The decks: the r1_adc5_core instance of the r5 deck takes @CORECELL@ and @COREEXTRA@ (empty for the netlist of record;
'vbg nbr vdda' + r1_adc5_core_lay for the layout); the include line takes @NETLISTS@.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BLOCK, 'layout'))
import r1_adc_netlist as N   # noqa: E402

pname = lambda n: n.replace('[', '_').replace(']', '')
CORE = ('sinp sinn cosp cosn isap isan isbp isbn trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb '
        + ' '.join('stba%d' % k for k in range(14)) + ' ' + ' '.join('stbb%d' % k for k in range(14))
        + ' rawa rawb topap topan topbp topbn vdd vrefa vrefb vrefla vreflb gnd').split()
# r1_sar5_logic port order (netlist of record) -> net in the wrapper
SAR = ('oap oan obp obn oanp obnp mclk wina winb trka0 trka1 trkb0 trkb1 lata latb '
       + ' '.join('stba%d' % k for k in range(14)) + ' ' + ' '.join('stbb%d' % k for k in range(14))
       + ' clka clkab clkb clkbb clkna clknab clknb clknbb '
       + ' '.join('cpa%d' % k for k in range(12, -1, -1)) + ' ' + ' '.join('cna%d' % k for k in range(12, -1, -1)) + ' '
       + ' '.join('cpb%d' % k for k in range(12, -1, -1)) + ' ' + ' '.join('cnb%d' % k for k in range(12, -1, -1))
       + ' rawa rawb vdd gnd').split()
SAR_LAY = {'oap', 'oan', 'obp', 'obn', 'oanp', 'obnp', 'mclk', 'clka', 'clkab', 'clkb', 'clkbb', 'clkna', 'clknab', 'clknb',
           'clknbb'} | {'c%s%s%d' % (pn, ch, k) for pn in 'pn' for ch in 'ab' for k in range(13)}
TOPMAP = {'clk': 'clk30', 'ain_sin_p': 'sinp', 'ain_sin_n': 'sinn', 'ain_cos_p': 'cosp', 'ain_cos_n': 'cosn',
          'ain_isa_p': 'isap', 'ain_isa_n': 'isan', 'ain_isb_p': 'isbp', 'ain_isb_n': 'isbn', 'ibias': 'nb',
          'vdda': 'vdda', 'vdd': 'vdd', 'vss': 'gnd', 'vref_in': 'vbg', 'topap': 'topap', 'topan': 'topan',
          'topbp': 'topbp', 'topbn': 'topbn', 'sar_trka0': 'trka0', 'sar_trka1': 'trka1', 'sar_trkb0': 'trkb0',
          'sar_trkb1': 'trkb1'}


def wrapper():
    L = ['* r1_adc5_post.spice -- wrapper of the r1_adc layout netlist with the pins of r1_adc5_core (+ vbg nb vdda),',
         '* written by sim/post/gen_post_decks.py (do not edit). Include after schematic/r1_adc_r5.spice (r1_sar5_logic)',
         '* and a layout netlist that defines r1_adc_lay_pr (sim/post/r1_adc_lay0.spice or a post-layout netlist).',
         '.subckt r1_adc5_core_lay %s vbg nb vdda' % ' '.join(CORE)]
    conn, ties = [], []
    for p in N.TOP_PORTS:
        if p in TOPMAP:
            conn.append(TOPMAP[p])
        elif p.startswith('sar_'):
            s = p[4:]
            assert s in SAR_LAY or s in ('oann', 'obnn'), p
            conn.append(p)
        else:
            n = 'nc_' + pname(p)
            conn.append(n)
            ties.append('Rnc_%s %s gnd 1k' % (pname(p), n))
    conn += ['vrefa', 'vrefla']
    L.append('XL ' + ' '.join(conn) + ' r1_adc_lay_pr')
    L += ties
    L.append('Evrefb vrefb 0 vrefa 0 1')
    L.append('Evreflb vreflb 0 vrefla 0 1')
    sc = []
    for s in SAR:
        sc.append('sar_' + s if s in SAR_LAY else s)
    L.append('XSAR ' + ' '.join(sc) + ' r1_sar5_logic')
    L += ['.ends r1_adc5_core_lay', '']
    used = set(conn) | set(sc)
    for s in SAR_LAY:
        assert 'sar_' + s in used
    open(os.path.join(HERE, 'r1_adc5_post.spice'), 'w').write('\n'.join(L))


def deck(src, dst, note):
    s = open(os.path.join(BLOCK, 'sim', 'r5', src)).read()
    assert s.count('.include schematic/r1_adc_r5.spice') == 1
    s = s.replace('.include schematic/r1_adc_r5.spice', '@NETLISTS@')
    if 'r1_adc5_core\n' in s:
        s = s.replace('vrefla vreflb 0 r1_adc5_core\n', 'vrefla vreflb 0 @COREEXTRA@ @CORECELL@\n')
        assert '@CORECELL@' in s
    s = '* %s: generated by sim/post/gen_post_decks.py from sim/r5/%s (%s)\n' % (dst, src, note) + s
    open(os.path.join(HERE, dst), 'w').write(s)


def points():
    """sim/post/points/win3.json: frame 0 start-up (0 V, not used); 3 windows x 25 points, +-6 LSB around the transitions
    1023/1024, 2047/2048, 3071/3072 (centres of sim/results/r5/mc_window_check.json; the outer ones extrapolated there),
    spacing 0.5 x 466.5 uV (1.95 conversions per LSB of 454.9 uV), slice B +1/4 LSB: cornwin5.json + the 1024 window."""
    import json
    import numpy as np
    C = json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r5', 'mc_window_check.json')))
    L = C['lsb_V']
    win = np.arange(-12, 13) * 0.5 * L
    a = np.concatenate([[0.0]] + [C['slices']['a']['window_centres_V'][k] + win for k in (0, 1, 2)])
    b = np.concatenate([[0.0]] + [C['slices']['b']['window_centres_V'][k] + win + 0.25 * L for k in (0, 1, 2)])
    os.makedirs(os.path.join(HERE, 'points'), exist_ok=True)
    json.dump({'a': [round(float(x), 7) for x in a], 'b': [round(float(x), 7) for x in b],
               'note': 'frame 0 start-up (0 V, not used); 3 windows x 25 points: +-6 LSB at 1023/1024, 2047/2048, 3071/3072, '
                       '2 per 466.5 uV (1.95 per LSB); B +1/4 LSB (sim/post/gen_post_decks.py)', 'windows': 3, 'per_window': 25},
              open(os.path.join(HERE, 'points', 'win3.json'), 'w'), indent=0)


def points_b(gk, c0, run, half=6.0, step_lsb=1.0 / 3, prefix='winb'):
    """layout B (2026-10-26): sim/post/points/winb_<code>.json, one window per file around the transition into code
    1024, 2048 or 3072 of each slice, predicted from the layout B mux run (code = c0 + gk * vin, per slice, frames 0
    and 2 at +-0.4 V). Window +-half LSB at step_lsb LSB of layout B; frame 0 start-up (0 V, not used)."""
    import json
    import numpy as np
    for c in (1024, 2048, 3072):
        P = {}
        for sl in 'ab':
            L = 1.0 / gk[sl]
            v0 = (c - 0.5 - c0[sl]) * L
            n = int(round(half / step_lsb))
            P[sl] = [0.0] + [round(float(v0 + k * step_lsb * L), 7) for k in range(-n, n + 1)]
        L = 2.0 / (gk['a'] + gk['b'])
        json.dump(dict(P, note='layout B fine window at code %d: +-%.1f LSB, step %.3f LSB, centres from %s (gk %s, c0 %s); frame 0 start-up (0 V, not used) (sim/post/gen_post_decks.py points_b)'
                       % (c, half, step_lsb, run, gk, c0), windows=1, per_window=len(P['a']) - 1, step_V=step_lsb * L, lsb_V=L),
                  open(os.path.join(HERE, 'points', '%s_%d.json' % (prefix, c)), 'w'), indent=0)
        print('%s_%d.json' % (prefix, c), len(P['a']), P['a'][1], P['a'][-1])


if __name__ == '__main__' and sys.argv[1:2] == ['winb']:
    points_b({'a': (2977 - 1100) / 0.8, 'b': (2976 - 1095) / 0.8}, {'a': (2977 + 1100) / 2.0, 'b': (2976 + 1095) / 2.0},
             'postb-isa-tt-rc')
elif __name__ == '__main__' and sys.argv[1:2] == ['winb2']:
    points_b({'a': (2960 - 1115) / 0.8, 'b': (2961 - 1111) / 0.8}, {'a': (2960 + 1115) / 2.0, 'b': (2961 + 1111) / 2.0},
             'postb2-isa-tt-rc', prefix='winb2')
elif __name__ == '__main__' and sys.argv[1:2] == ['winb2c']:
    # 2026-10-27: centres from a straight-line fit of the B2 windows 2048 and 3072 (ideal VREF 1.045 V forced; the
    # mux-run centres put the 3072 window 12 codes high, run postb2-win3072-tt-rc)
    import json as _j
    import numpy as _np
    F = {}
    for sl in 'ab':
        V, C = [], []
        for c in (2048, 3072):
            P = _j.load(open(os.path.join(HERE, 'points', 'winb2_%d.json' % c)))
            seq = _j.load(open(os.path.join(HERE, 'results', 'postb2_win%d_tt_rc.json' % c)))[sl]['windows']['0']['code_sequence']
            v = sorted(P[sl][1:])
            V += v[:len(seq)]; C += seq
        F[sl] = list(_np.polyfit(V, C, 1))
    points_b({k: F[k][0] for k in 'ab'}, {k: F[k][1] for k in 'ab'}, 'postb2-win2048-tt-rc + postb2-win3072-tt-rc (fit)', prefix='winb2c')
elif __name__ == '__main__':
    wrapper()
    points()
    deck('tb_adc5_points.cir', 'tb_post_points.cir', 'include line -> NETLISTS substitution; instance in INSTANCES')
    deck('tb_adc5_isa.cir', 'tb_post_isa.cir', 'include line -> NETLISTS substitution; core cell -> COREEXTRA CORECELL substitutions')
    print('wrote r1_adc5_post.spice tb_post_points.cir tb_post_isa.cir')
