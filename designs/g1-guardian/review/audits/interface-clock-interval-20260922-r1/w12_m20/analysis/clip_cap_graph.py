"""Strict SPICE capacitor parsing and explicit extracted-net alias handling."""
import math
import re


def parse_capacitors(text):
    statements = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('*'):
            continue
        if line.startswith('+'):
            if not statements:
                raise ValueError('orphan continuation')
            statements[-1] += ' ' + line[1:].strip()
        else:
            statements.append(line)
    caps = []
    names = set()
    for line in statements:
        fields = line.split()
        if not fields[0].lower().startswith('c'):
            continue
        if len(fields) != 4 or fields[0].lower() in names:
            raise ValueError('malformed or duplicate capacitor: '+line)
        names.add(fields[0].lower())
        match = re.fullmatch(r'([\d.eE+\-]+)([afpnu]?)', fields[3])
        if match is None:
            raise ValueError('unsupported capacitor value: '+fields[3])
        value = float(match[1])*{'a': 1e-18, 'f': 1e-15, 'p': 1e-12,
                                'n': 1e-9, 'u': 1e-6, '': 1}[match[2]]
        if not math.isfinite(value) or value <= 0:
            raise ValueError('capacitance must be positive and finite')
        caps.append((fields[1], fields[2], value))
    if not caps:
        raise ValueError('no capacitors')
    nodes = sorted({node for a, b, value in caps for node in (a, b)})
    aliases = {}
    for node in nodes:
        labels = node.split('|')
        targets = set(labels) & {'P', 'N'}
        if len(targets) > 1 or (targets and 'VSUBS' in labels):
            raise ValueError('target short in extracted connectivity: '+node)
        if not all(label in {'P', 'N', 'VSUBS'} or label.startswith(('FILL_L', 'CTX_L')) for label in labels):
            raise ValueError('unidentified extracted net: '+node)
        if targets:
            aliases[node] = next(iter(targets))
        elif 'VSUBS' in labels:
            aliases[node] = 'VSUBS'
        elif any(label.startswith('CTX_L') for label in labels):
            # This fill is actually connected to a context conductor.
            aliases[node] = next(label for label in labels if label.startswith('CTX_L'))
        else:
            aliases[node] = node
    for target in ['P', 'N']:
        if sum(value == target for value in aliases.values()) != 1:
            raise ValueError('missing or disconnected target '+target)
    normalized = [(aliases[a], aliases[b], value) for a, b, value in caps]
    if any(a == b for a, b, value in normalized):
        raise ValueError('self-capacitor after alias handling')
    return normalized, aliases
