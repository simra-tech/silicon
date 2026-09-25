import sys, collections, re
def load(p):
    lines = []
    for raw in open(p):
        raw = raw.rstrip('\n')
        if raw.startswith('+') and lines: lines[-1] += ' ' + raw[1:].strip()
        elif raw and not raw.startswith('*'): lines.append(raw)
    return lines
def canon(p):
    L = load(p); ms = collections.Counter(); sub = None
    for ln in L:
        t = ln.split()
        if t[0].upper() == '.SUBCKT': sub = sub or ' '.join(t[1:]); continue
        if t[0].upper() == '.ENDS': continue
        n = lambda x: '$' if x.startswith('\\$') or x.startswith('$') else x
        if t[0].startswith('M'): ms[('M', tuple(n(x) for x in t[1:5]), tuple(t[5:]))] += 1
        elif t[0].startswith('C'): ms[('C', tuple(sorted(n(x) for x in t[1:3])), t[3])] += 1
        else: ms[('X', tuple(n(x) for x in t[1:]))] += 1
    return sub, ms
ref = canon(sys.argv[1])
for p in sys.argv[2:]:
    c = canon(p)
    print(p.split('/')[-3], 'subckt ports equal:', c[0] == ref[0], ' element multiset equal (unnamed nets abstracted):', c[1] == ref[1], ' elements', sum(c[1].values()))
