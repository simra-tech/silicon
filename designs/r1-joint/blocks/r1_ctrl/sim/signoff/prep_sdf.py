#!/usr/bin/env python3
"""Make the t7 netlist and SDF loadable in Icarus (name-only changes, no delay change).
Instance names with '.', '[' or ']' (CTS clock buffers, escaped identifiers) are replaced by '_';
Icarus' SDF reader cannot resolve escaped names. INTERCONNECT entries are dropped (they crash the
reader on the same names; they are wire delays of 0 to a few tens of ps). The min:typ:max triples are collapsed to one value (Icarus ignores the selection argument); VOLTAGE/PROCESS/TEMPERATURE header lines are dropped. Counts are printed."""
import re, sys
nl_in, sdf_in, nl_out, sdf_out, pick = sys.argv[1:6]   # pick: max | typ | min
san = lambda n: re.sub(r'[^A-Za-z0-9_]', '_', n)
txt = open(nl_in).read()
cnt = [0]
def f(m):
    cnt[0] += 1
    return m.group(1) + san(m.group(2)) + m.group(3)
# cell instance with escaped name: "<celltype> \name (" at line start
txt = re.sub(r'^(\s*sg13g2_\w+\s+)\\(\S+)(\s)', f, txt, flags=re.M)
open(nl_out, 'w').write(txt)
print('netlist: renamed', cnt[0], 'escaped instance names')
s = open(sdf_in).read()
n_ic = len(re.findall(r'\n\s*\(INTERCONNECT ', s))
s = re.sub(r'\n\s*\(INTERCONNECT [^\n]*', '', s)
c2 = [0]
def g(m):
    c2[0] += 1
    return '(INSTANCE ' + san(m.group(1).replace('\\', '')) + ')'
s = re.sub(r'\(INSTANCE ([^)\s]*\\[^)\s]*)\)', g, s)
s = re.sub(r'\n \(CELL\n  \(CELLTYPE "r1_ctrl_top"\)\n  \(INSTANCE\)\n  \(DELAY\n   \(ABSOLUTE\n   \)\n  \)\n \)', '', s)   # top-level block left empty
s = re.sub(r'\n\s*\((VOLTAGE|PROCESS|TEMPERATURE) [^\n]*', '', s)
idx = {'min': 1, 'typ': 2, 'max': 3}[pick]
n_tr = [0]
def h(m):
    n_tr[0] += 1
    return '(' + (m.group(idx) or m.group(2) or m.group(3) or m.group(1)) + ')'
s = re.sub(r'\(([-0-9.]*):([-0-9.]*):([-0-9.]*)\)', h, s)
print('sdf: collapsed', n_tr[0], 'min:typ:max triples to', pick)
open(sdf_out, 'w').write(s)
print('sdf: renamed', c2[0], 'instances, dropped', n_ic, 'INTERCONNECT entries')
