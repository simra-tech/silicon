#!/usr/bin/env python3
"""Rebuild the chip's canonical CDL and its comparison-only projection with a new g1_digital.

  regen_chip_cdl.py --canonical <g1_chip_top_1414_r2.cdl> --pnl <new g1_digital.pnl.v> \
      --out <g1_chip_top_1414_r3.cdl> --projection-out <comparison_only.cdl> --report <json>

* canonical: the `.SUBCKT g1_digital ... .ENDS` block is replaced by
  verilog_to_subckt(<pnl>) from g1_padring/flow/lvs/assemble_chip_cdl.py (the method
  of digital-cleanflat-lvs-20260923-r1: standard-cell pin order from the CDL's own
  sg13g2_* subcircuits). The port line must be identical to the old one; every
  other line of the file is kept byte-for-byte (checked).
* projection (comparison only, NOT canonical): the one source-only dummy
  `MP0 vdd vdd vdd vdd sg13_hv_pmos ...` line of G1_VSS_DERIVATIVE__sg13g2_LevelDown is
  removed, the projection used for every projected-reference LVS of the chip
  (three all-VDD pad dummies = three instances of that subcircuit). The flat
  reference is then written by flatten_reference.rb.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.normpath(os.path.join(HERE, '../../../g1_padring/flow/lvs/assemble_chip_cdl.py'))


def load_v2s():
    # assemble_chip_cdl.py runs its CLI at import time; execute only its definitions
    src = open(ASM).read()
    cut = src.index('lib_texts = [open(f).read() for f in libs]')
    ns = {'__name__': 'assemble_chip_cdl_defs'}
    exec(compile(src[:cut].replace('args = sys.argv[1:]', 'args = ["x", "y"]'), ASM, 'exec'), ns)
    return ns['verilog_to_subckt'], ns['subckt_pins']


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--canonical', required=True)
    ap.add_argument('--pnl', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--projection-out', required=True)
    ap.add_argument('--report', required=True)
    ap.add_argument('--header', default='r3: g1_digital subcircuit regenerated from the ECO powered netlist')
    a = ap.parse_args()
    v2s, subckt_pins = load_v2s()
    text = open(a.canonical).read()
    m = re.search(r'^\.SUBCKT g1_digital .*?^\.ENDS\n', text, re.S | re.M)
    assert m and text.count('.SUBCKT g1_digital ') == 1
    old = m.group(0)
    pins = subckt_pins(text)
    # `assign <port> = <net>;` (e.g. the ECO's tie-high osc_en: assign osc_en = net390;) is
    # not read by verilog_to_subckt; resolve it by renaming <net> to <port> (token-exact)
    # in a derived copy of the netlist. Any other assign form is refused.
    vtext = open(a.pnl).read()
    assigns = re.findall(r'^\s*assign\s+(.*?);\s*$', vtext, re.M)
    aliases = {}
    for asg in assigns:
        mm = re.fullmatch(r'([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)', asg.strip())
        assert mm, 'unsupported assign: ' + asg
        lhs, rhs = mm.groups()
        assert re.search(r'\boutput\s+%s\s*;' % lhs, vtext), 'assign to a non-port: ' + asg
        assert rhs not in aliases.values() and lhs not in aliases
        aliases[rhs] = lhs
    pnl_used = a.pnl
    if aliases:
        body = re.sub(r'^\s*assign\s+.*?;\s*\n', '', vtext, flags=re.M)
        body = re.sub(r'^\s*wire\s+(%s)\s*;\s*\n' % '|'.join(map(re.escape, aliases)), '', body, flags=re.M)
        body = re.sub(r'\b(%s)\b' % '|'.join(map(re.escape, aliases)), lambda m: aliases[m.group(1)], body)
        pnl_used = a.out + '.assign_resolved.pnl.v'
        open(pnl_used, 'w').write(body)
    top, new, counts, nc = v2s(pnl_used, pins, {})
    assert top == 'g1_digital'
    # top-level bus spelling restoration (as in digital-cleanflat-lvs-20260923-r1):
    # verilog_to_subckt writes dac_soft[7] as dac_soft_7_; the chip CDL uses dac_soft[7]
    oldports = old.splitlines()[0].split()[2:]
    bus = {re.sub(r'\[(\d+)\]$', r'_\1_', p): p for p in oldports if re.search(r'\[\d+\]$', p)}
    toks = re.split(r'(\s+)', new)
    assert not any(t in bus.values() for t in toks)
    new = ''.join(bus.get(t, t) for t in toks)
    assert ''.join({v: k for k, v in bus.items()}.get(t, t) for t in re.split(r'(\s+)', new)) == ''.join(toks)
    assert old.splitlines()[0] == new.splitlines()[0], 'g1_digital port line changed'
    out = text[:m.start()] + new + text[m.end():]
    out = '* ' + a.header + '\n' + out
    assert out[len(a.header) + 3:].replace(new, old, 1) == text          # everything else byte-identical
    open(a.out, 'w').write(out)
    # projection
    sm = re.search(r'^\.SUBCKT G1_VSS_DERIVATIVE__sg13g2_LevelDown .*?^\.ENDS\n', out, re.S | re.M)
    dummy = 'MP0 vdd vdd vdd vdd sg13_hv_pmos m=1 w=4.65u l=450.00n ng=1\n'
    assert sm and sm.group(0).count(dummy) == 1
    body = sm.group(0).replace(dummy, '')
    proj = out[:sm.start()] + body + out[sm.end():]
    assert proj.replace(body, sm.group(0), 1) == out                     # exact inverse
    open(a.projection_out, 'w').write(proj)
    users = len(re.findall(r'/ G1_VSS_DERIVATIVE__sg13g2_LevelDown\s*$', out, re.M))
    rep = dict(canonical_in=a.canonical, canonical_in_sha256=sha(text), pnl=a.pnl,
               pnl_sha256=sha(open(a.pnl, 'rb').read()), assigns_resolved=aliases, pnl_used=pnl_used, canonical_out=a.out, canonical_out_sha256=sha(out),
               old_g1_digital_sha256=sha(old), new_g1_digital_sha256=sha(new),
               g1_digital_identical=(old == new), instances=sum(counts.values()), unconnected_pins=nc,
               projection_out=a.projection_out, projection_sha256=sha(proj),
               projection_removed='one MP0 line of G1_VSS_DERIVATIVE__sg13g2_LevelDown',
               leveldown_instances=users, projection_reverse_exact=True)
    json.dump(rep, open(a.report, 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
