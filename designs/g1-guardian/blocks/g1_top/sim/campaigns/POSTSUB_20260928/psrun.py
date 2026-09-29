#!/usr/bin/env python3
"""Post-submission campaign T4 launcher: run_top_cdl.py / run_top.py unchanged, two additions.

Usage (inside the pinned container, G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim):

    python3 campaigns/POSTSUB_20260928/psrun.py {cdl|top} [--ps-build DIR] [--ps-mc-seed N --ps-mc-dir DIR] <runner args>

1. --ps-build DIR: the runners' build directory (decks as run, compiled RTL, full waves, state files) is moved
   from build/g1_top to DIR (bulk storage). Only the module global BUILD changes; logs, JSON, deck copies and
   decimated waves stay where the runners write them.
2. --ps-mc-seed N (cdl only): PDK mismatch Monte Carlo on the built deck, applied after run_top_cdl.build_cdl_deck:
   * the corner .lib sections become the PDK's own *_mismatch sections (mos_<c>_mismatch for LV and HV MOS,
     res_typ_mismatch, cap_typ_mismatch, hbt_typ_mismatch; cornerDIO unchanged: it has no mismatch section);
   * every instance of a PDK device subckt that carries an mm_ok switch (sg13_lv/hv_nmos/pmos, rppd, rhigh, rsil,
     cap_cmim, cap_rfcmim) gets mm_ok=1, in the translated chip and in copies of every .include'd block netlist
     (copies written once to --ps-mc-dir, hash-recorded; the tracked netlists are not touched);
   * '.option seed=N' is placed after the model .lib lines (read at parse time, before the draws).
   The model cards are not modified: mm_ok is an instance parameter the PDK subckts expose for this purpose.
   The HBT mismatch section has no per-instance draw in this PDK revision (sg13g2_hbt_mod_mismatch.lib has no
   agauss), so HBTs take the typical card; recorded as such.
3. --ps-drop NAME (cdl only, case c_mid --timeline compact): the 3.3 V dropout decks armed_io0 / armed_io2 /
   trip_io0 of the power_io red team (DROP_CASES), built from the chip-of-record deck.
4. cdl runs sample their progress record every 60 s (run_bounded interval_s; the runner default is 5 s).
"""
import hashlib
import json
import os
import re
import sys

SIM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, SIM)

# 3.3 V dropout cases of review/redteam-20260927/power_io/FINDINGS.md section 5 (scripts/mkdecks.py there),
# applied to the c_mid compact deck exactly as that generator did: V33 (IOVDD = VDDA board rail) becomes a PWL,
# the load profile Vprof and the stop time change; nothing else.
DROP_CASES = {
    'armed_io0': ('pwl(0 3.3 13u 3.3 14u 0 17u 0 18u 3.3)', 'pwl(0 1 21u 1 21.02u 1.8)', 27,
                  'armed at 1 A, IOVDD=VDDA drop to 0 V (1 us fall, 3 us at 0 V, 1 us rise) with VDD and EN held; '
                  '1.8x fault 3 us after recovery'),
    'armed_io2': ('pwl(0 3.3 13u 3.3 14u 2.0 17u 2.0 18u 3.3)', 'pwl(0 1 21u 1 21.02u 1.8)', 27,
                  'armed at 1 A, IOVDD=VDDA sag to 2.0 V (1 us fall, 3 us hold, 1 us rise) with VDD and EN held; '
                  '1.8x fault 3 us after recovery'),
    'trip_io0': ('pwl(0 3.3 19u 3.3 20u 0 23u 0 24u 3.3)', 'pwl(0 1 1.6e-05 1 1.602e-05 1.8)', 28,
                 '1.8x fault at 16 us (hard trip), then IOVDD=VDDA drop to 0 V 19-24 us with VDD and EN held, '
                 'fault persisting'),
}


def drop_transform(deck, name):
    v33, prof, tstop, desc = DROP_CASES[name]
    deck, n1 = re.subn(r'(?m)^V33 rail33 0 dc 3\.3$', 'V33 rail33 0 ' + v33, deck)
    deck, n2 = re.subn(r'(?m)^Vprof iprof 0 pwl\(.*\)$', 'Vprof iprof 0 ' + prof, deck)
    deck, n3 = re.subn(r'(?m)^tran (\S+) \S+ 0 (\S+)$', lambda m: 'tran %s %gu 0 %s' % (m.group(1), tstop, m.group(2)), deck)
    if (n1, n2, n3) != (1, 1, 1):
        raise SystemExit('dropout transform failed: %r' % ((n1, n2, n3),))
    return '* psrun.py 3.3 V dropout case %s: %s\n' % (name, desc) + deck


MM_DEVICES = ('sg13_lv_nmos', 'sg13_lv_pmos', 'sg13_hv_nmos', 'sg13_hv_pmos', 'rppd', 'rhigh', 'rsil',
              'cap_cmim', 'cap_rfcmim')


def pop_opt(argv, name, has_value=True):
    if name not in argv:
        return None
    i = argv.index(name)
    if has_value:
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    del argv[i]
    return True


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def logical_lines(text):
    """Split SPICE text into logical lines (a line plus its '+' continuations), keeping the raw text."""
    out = []
    for line in text.split('\n'):
        if line.startswith('+') and out:
            out[-1].append(line)
        else:
            out.append([line])
    return out


def add_mm_ok(text):
    """Append mm_ok=1 to every X instance whose cell is a PDK device with an mm_ok switch. Returns (text, count)."""
    n = 0
    res = []
    for group in logical_lines(text):
        first = group[0]
        if first[:1] in ('X', 'x'):
            toks = ' '.join(g.lstrip('+') for g in group).split()
            cell = next((t for t in toks[1:] if '=' not in t and t.lower() in MM_DEVICES), None)
            # the cell name is the last token before the first name=value parameter
            pos = next((k for k, t in enumerate(toks) if '=' in t), len(toks))
            if pos >= 2 and toks[pos - 1].lower() in MM_DEVICES and not any(t.lower().startswith('mm_ok=') for t in toks):
                group[-1] = group[-1] + ' mm_ok=1'
                n += 1
            elif pos >= 2 and toks[pos - 1].lower() in MM_DEVICES:
                group = [re.sub(r'(?i)\bmm_ok=\S+', 'mm_ok=1', g) for g in group]
                n += 1
        res.extend(group)
    return '\n'.join(res), n


def mc_transform(deck, seed, mcdir, report):
    # 1. corner sections -> mismatch sections
    def libsub(m):
        sec = m.group(2)
        new = sec if sec.endswith('_mismatch') or sec.startswith('dio_') else sec + '_mismatch'
        return m.group(1) + new
    deck, nlib = re.subn(r'(?im)^(\.lib\s+\S+/corner(?:MOSlv|MOShv|RES|CAP|HBT)\.lib\s+)(\S+)\s*$', libsub, deck)
    report['lib_sections_switched'] = nlib
    report['lib_lines'] = re.findall(r'(?im)^\.lib\s+\S+\s+\S+\s*$', deck)
    # 2. mm_ok=1 on the deck's own instances
    deck, n_deck = add_mm_ok(deck)
    report['mm_ok_instances_in_deck'] = n_deck
    # 3. .include'd netlists -> mm_ok copies
    os.makedirs(mcdir, exist_ok=True)
    incs = {}

    def incsub(m):
        path = m.group(2).strip('"\'')
        if not os.path.isfile(path) or '/foss/pdks/' in path:
            return m.group(0)
        text = open(path, errors='replace').read()
        new, n = add_mm_ok(text)
        if n == 0:
            return m.group(0)
        src_sha = sha(path)
        out = os.path.join(mcdir, 'mm_%s_%s' % (src_sha[:12], os.path.basename(path)))
        if not os.path.exists(out):
            tmp = out + '.tmp%d' % os.getpid()
            with open(tmp, 'w') as f:
                f.write('* psrun.py mc copy of %s (sha256 %s): mm_ok=1 on %d PDK device instances\n' % (path, src_sha, n))
                f.write(new)
            os.replace(tmp, out)
        incs[path] = dict(src_sha256=src_sha, copy=out, copy_sha256=sha(out), mm_ok_instances=n)
        return m.group(1) + out
    deck = re.sub(r'(?im)^(\.include\s+)(\S+)\s*$', incsub, deck)
    report['includes'] = incs
    # 4. seed: '.option seed=N' is read while the netlist is parsed, i.e. before the agauss draws of the
    #    instance parameters (checked on a two-device deck: reproducible per seed, different between seeds;
    #    'setseed' inside .control acts only after a 'reset', which would re-load the d_cosim instance)
    libs = list(re.finditer(r'(?im)^\.lib\s+\S+\s+\S+\s*$', deck))
    k = libs[-1].end()
    deck = deck[:k] + '\n.option seed=%d' % seed + deck[k:]
    report['seed'] = seed
    deck = '* psrun.py PDK mismatch MC: seed %d, mm_ok=1 on %d deck + %d included instances\n' % (
        seed, n_deck, sum(v['mm_ok_instances'] for v in incs.values())) + deck
    return deck


def main():
    argv = sys.argv[1:]
    mode = argv.pop(0)
    build = pop_opt(argv, '--ps-build')
    seed = pop_opt(argv, '--ps-mc-seed')
    drop = pop_opt(argv, '--ps-drop')
    mcdir = pop_opt(argv, '--ps-mc-dir')
    sys.argv = [sys.argv[0]] + argv
    import run_top as RT
    if build:
        os.makedirs(build, exist_ok=True)
        RT.BUILD = build
    if mode == 'top':
        if seed:
            raise SystemExit('--ps-mc-seed is supported for cdl only')
        RT.main()
        return
    import run_top_cdl as RC
    if build:
        RC.BUILD = build
    # progress sampling every 60 s instead of 5 s (the progress.jsonl record is ~5 kB per sample)
    import functools
    RC.run_bounded = functools.partial(RC.run_bounded, interval_s=60)
    if drop:
        if drop not in DROP_CASES:
            raise SystemExit('--ps-drop: one of %s' % ', '.join(DROP_CASES))
        orig_d = RC.build_cdl_deck

        def build_drop(*args, **kw):
            deck, swaps, rep = orig_d(*args, **kw)
            return drop_transform(deck, drop), swaps, rep
        RC.build_cdl_deck = build_drop
    if seed:
        seed = int(seed)
        if not mcdir:
            raise SystemExit('--ps-mc-seed needs --ps-mc-dir')
        orig = RC.build_cdl_deck

        def build_mc(case, name, netlist, temp, corner, tag, *rest, **kw):
            deck, swaps, rep = orig(case, name, netlist, temp, corner, tag, *rest, **kw)
            report = {}
            deck = mc_transform(deck, seed, mcdir, report)
            with open(os.path.join(mcdir, 'mc_%s.json' % tag), 'w') as f:
                json.dump(report, f, indent=1)
            print('mc: seed %d, deck mm_ok %d, includes %s, lib sections switched %d' % (
                seed, report['mm_ok_instances_in_deck'],
                {os.path.basename(k): v['mm_ok_instances'] for k, v in report['includes'].items()},
                report['lib_sections_switched']))
            return deck, swaps, rep
        RC.build_cdl_deck = build_mc
    RC.main()


if __name__ == '__main__':
    main()
