#!/usr/bin/env python3
"""G1_T2F post-layout runner: the block testbench (../tb_g1_t2f.spice.tmpl, same options, loads and
measurements via ../ctl_freq.txt) on the kpex netlist g1_t2f_pex.spice, bandgap in its schematic view.
Inside the pinned container, from the repository root:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/sim/postlayout flow/run.sh python3 run_postlayout.py all [-j N]
suites: ftemp (PTAT -40 25 27 100 125 175 C, REF -40 27 125 175 C), supply (3.0/3.3/3.6 V, both modes, 27 C), all
"""
import argparse, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, '..')
DECKS, LOGS, RES = (os.path.join(HERE, d) for d in ('decks', 'logs', 'results'))
TMPL = open(os.path.join(HERE, 'tb_g1_t2f_pex.spice.tmpl')).read()
CTL = open(os.path.join(SIM, 'ctl_freq.txt')).read()
NA, NB = 8, 24


def deck(name, kind, temp, mode, vdd='3.3', vdd12='1.2', tend='32u'):
    subs = {'KIND': kind, 'HBT': 'hbt_typ', 'MOS': 'mos_tt', 'RES': 'res_typ', 'CAP': 'cap_typ', 'VDD': vdd, 'VDD12': vdd12,
            'TEMP': str(temp), 'MODE': 'ref' if mode else 'ptat', 'MODEV': vdd if mode else '0', 'TEND': tend,
            'NA': str(NA), 'NB': str(NB), 'WRDATA': ''}
    text = TMPL.replace('@@CONTROL@@', CTL)
    for k, v in subs.items():
        text = text.replace(f'@@{k}@@', v)
    path = os.path.join(DECKS, name + '.cir')
    open(path, 'w').write(text)
    return path


def gen(suite):
    d = []
    if suite in ('ftemp', 'all'):
        for t in (-40, 25, 27, 100, 125, 175):
            d.append(deck(f'ftemp_ptat_T{t}', 'post-layout f(T)', t, 0, tend='40u' if t < 0 else '32u'))
        for t in (-40, 27, 125, 175):
            d.append(deck(f'ftemp_ref_T{t}', 'post-layout f(T)', t, 1, tend='40u' if t < 0 else '32u'))
    if suite in ('supply', 'all'):
        for v in ('3.0', '3.3', '3.6'):
            d.append(deck(f'supply_ptat_vdd{v}_T27', 'post-layout supply', 27, 0, vdd=v))
            d.append(deck(f'supply_ref_vdd{v}_T27', 'post-layout supply', 27, 1, vdd=v))
    return d


def run_one(path):
    log = os.path.join(LOGS, os.path.basename(path).replace('.cir', '.log'))
    with open(log, 'w') as f:
        subprocess.run(['ngspice', '-b', os.path.basename(path)], cwd=DECKS, stdout=f, stderr=subprocess.STDOUT)


def parse(suite):
    rows = []
    for f in sorted(os.listdir(LOGS)):
        if f.startswith(suite + '_') and f.endswith('.log'):
            d = {'deck': f[:-4]}
            for line in open(os.path.join(LOGS, f), errors='replace'):
                m = re.match(r'^(\w+)\s*=\s*([-+0-9.eE]+)', line.strip())
                if m:
                    d[m.group(1)] = float(m.group(2))
            rows.append(d)
    if rows:
        keys = ['deck'] + sorted({k for r in rows for k in r if k != 'deck'})
        with open(os.path.join(RES, f'{suite}_summary.csv'), 'w') as out:
            out.write(','.join(keys) + '\n')
            for r in rows:
                out.write(','.join(str(r.get(k, '')) for k in keys) + '\n')
        print(f'{suite}: {len(rows)} logs -> results/{suite}_summary.csv')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('suite')
    ap.add_argument('-j', type=int, default=4)
    ap.add_argument('--parse-only', action='store_true')
    a = ap.parse_args()
    for p in (DECKS, LOGS, RES):
        os.makedirs(p, exist_ok=True)
    open(os.path.join(DECKS, '.spiceinit'), 'w').write(open(os.path.join(SIM, '.spiceinit')).read())
    if not a.parse_only:
        decks = gen(a.suite)
        print(f'{len(decks)} decks, {a.j} parallel')
        with ThreadPoolExecutor(a.j) as ex:
            list(ex.map(run_one, decks))
    for s in (['ftemp', 'supply'] if a.suite == 'all' else [a.suite]):
        parse(s)
