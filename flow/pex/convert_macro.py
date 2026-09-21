#!/usr/bin/env python3
"""Translate KPEX MOS/HBT macro syntax to pinned ngspice subcircuits.

KPEX's exported MOS ports already use D/G/S/B. HBT ports are C/B/E/substrate;
bare HBT geometry is in micrometres. VSUBS is the macro's vss substrate.
No devices or nonzero-node capacitors are removed; shorted substrate capacitors
are retained as zero-voltage branches. No PDK model is edited.
"""
import argparse, hashlib, json, re
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args()
if a.output.exists():ap.error('refusing to overwrite')
lines=[]
for line in a.source.read_text().splitlines():
    if line.startswith('+'):lines[-1]+=' '+line[1:].strip()
    else:lines.append(line)
def node(s):
    if s.upper()=='VSUBS':return 'vss'
    return s.replace('\\','').replace('$','n_')
out=['* ngspice translation of '+a.source.name,
     '* Source SHA256 '+hashlib.sha256(a.source.read_bytes()).hexdigest()]
counts=dict(MOS=0,HBT=0,capacitors=0)
for line in lines:
    t=line.split()
    if not t or line.startswith('*'):continue
    if t[0].upper() in ['.SUBCKT','.ENDS']:out.append(' '.join(t));continue
    if t[0].startswith(('M$','Q$')):
        hbt=t[0].startswith('Q$');params=[]
        for p in t[6:]:
            k,v=p.split('=')
            if hbt and k.lower() in ['we','le'] and re.fullmatch(r'[0-9.eE+-]+',v):v+='u'
            params.append(k+'='+v)
        out.append('X'+t[0].replace('$','')+' '+' '.join(node(s) for s in t[1:5])+' '+t[5]+' '+' '.join(params))
        counts['HBT' if hbt else 'MOS']+=1
    elif t[0].startswith('Cext_'):
        v=t[3]
        if v.endswith('a'):v=f'{float(v[:-1])*1e-18:.12g}'
        out.append(' '.join([t[0],node(t[1]),node(t[2]),v]));counts['capacitors']+=1
    else:raise ValueError('Unsupported extracted element: '+line)
a.output.write_text('\n'.join(out)+'\n')
a.output.with_suffix('.conversion.json').write_text(json.dumps(dict(source=str(a.source),source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counts=counts),indent=2)+'\n')
print(counts)
