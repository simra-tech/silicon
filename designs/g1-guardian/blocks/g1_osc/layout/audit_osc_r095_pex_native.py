#!/usr/bin/env python3
"""Compare every OSC CPEX native device/terminal to the strict-LVS CDL.

The PEX input intentionally omits MIM physical layers; the unchanged converter
re-inserts those 11 schematic devices. This audit is not a substitute for the
stock filled-GDS LVS, and does not qualify RC accuracy or circuit performance.
"""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path, pex):
    devices = {}
    parasitic = []
    ports = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('*') or line.startswith('+'):
            continue
        t = line.split()
        if t[0].lower() == '.subckt':
            ports = t[2:]
            continue
        if line.startswith('.'):
            continue
        if pex and t[0].startswith('Cext_'):
            parasitic.append(t)
            continue
        if pex:
            assert t[0].startswith('X'), t[0]
            key = t[0][1:]
        else:
            assert t[0][0] in 'MRDC', t[0]
            key = t[0][1:]
        assert key not in devices, key
        kind = key[0]
        n = {'M': 4, 'R': 3, 'D': 2, 'C': 2}[kind]
        nets = t[1:1 + n]
        model = t[1 + n]
        params = {}
        for x in t[2 + n:]:
            k, v = x.split('=', 1)
            params[k.lower()] = v.lower()
        devices[key] = (kind, nets, model, params)
    assert ports is not None
    return ports, devices, parasitic


def numeric(x):
    if x.endswith('u'):
        return Decimal(x[:-1]) * Decimal('1e-6')
    if x.endswith('f'):
        return Decimal(x[:-1]) * Decimal('1e-15')
    if x.endswith('a'):
        return Decimal(x[:-1]) * Decimal('1e-18')
    return Decimal(x)


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--native', type=Path, required=True)
    a.add_argument('--pex', type=Path, required=True)
    a.add_argument('--report', type=Path, required=True)
    args = a.parse_args()
    src_ports, src, _ = parse(args.native, False)
    dst_ports, dst, caps = parse(args.pex, True)
    required_ports = ['en', 'trim[0]', 'trim[1]', 'trim[2]', 'trim[3]', 'osc_clk', 'VDD', 'VSS']
    assert src_ports == required_ports, src_ports
    assert dst_ports == ['en', 'trim0', 'trim1', 'trim2', 'trim3', 'osc_clk', 'vdd', 'vss'], dst_ports
    assert set(src) == set(dst), (sorted(set(src) - set(dst)), sorted(set(dst) - set(src)))
    assert len(src) == 81 and len(caps) == 609, (len(src), len(caps))
    netmap = {d: s for d, s in zip(dst_ports, src_ports)}
    reverse = {s: d for d, s in netmap.items()}
    counts = {'M': 0, 'R': 0, 'D': 0, 'C': 0}
    for key in sorted(src):
        sk, sn, sm, sp = src[key]
        dk, dn, dm, dp = dst[key]
        assert sk == dk and sm == dm and len(sn) == len(dn), key
        assert set(sp) <= set(dp), (key, sp, dp)
        for k, v in sp.items():
            assert numeric(v) == numeric(dp[k]), (key, k, v, dp[k])
        if sk == 'M':
            assert dp.get('ng') == '1', key
        for s, d in zip(sn, dn):
            prior = netmap.setdefault(d, s)
            assert prior == s, (key, 'collapsed/different PEX net', d, s, prior)
            prior2 = reverse.setdefault(s, d)
            assert prior2 == d, (key, 'split PEX net', s, d, prior2)
        counts[sk] += 1
    assert counts == {'M': 51, 'R': 18, 'D': 1, 'C': 11}, counts
    assert len(set(x[0] for x in caps)) == len(caps)
    for c in caps:
        assert len(c) == 4 and c[1] in netmap and c[2] in netmap, c
        assert numeric(c[3]).is_finite() and numeric(c[3]) > 0, c
    report = {
        'status': 'passed',
        'auditor_sha256': sha(Path(__file__)),
        'scope': 'exact converted CPEX native primitive parameters and terminal-net bijection vs strict-LVS CDL; 609 positive extracted capacitances',
        'not_claimed': ['stock PEX-input internal LVS match', 'MIM plate parasitics', 'wire resistance', 'circuit performance', 'chip density'],
        'native_sha256': sha(args.native), 'pex_sha256': sha(args.pex),
        'counts': counts, 'parasitic_capacitors': len(caps),
        'net_bijection_count': len(netmap),
        'ports': src_ports,
    }
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
