#!/usr/bin/env python3
"""Prove limited DC branch semantics, not physical substrate attachment."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def qualify(model, macros, wrapper, source):
    for parameter in ('isa', 'isp'):
        assert re.search(r'`MPRcz\(\s*'+parameter+r'\s*,\s*0\.0\s*,', model)
    for branch in ('b_pc1', 'b_pc2'):
        index = branch[-1]
        contributions = re.findall(r'I\('+branch+r'\)\s*<\+\s*([^;]+);', model)
        assert contributions == ['Ip'+index, 'ddt(Qcp'+index+')'], contributions
        assert re.search(r'if \(Is'+index+r'>0\.0\) begin.*?end else begin\s*'
                         r'Id'+index+r'\s*=\s*0\.0;\s*Ib'+index+r'\s*=\s*0\.0;\s*'
                         r'Ip'+index+r'\s*=\s*0\.0;', model, re.S)
        assert 'Is'+index+'      =  a'+index+'_um2*isa_t+p'+index+'_um*isp_t;' in model
    records = [line.split() for line in source.splitlines() if re.match(r'^XR\S*\s', line)]
    assert len(records) == 399 and len({r[0] for r in records}) == 399
    assert all(r[3] == 'vss' and r[4] in ('rhigh', 'rppd') for r in records)
    for name in ('rhigh', 'rppd'):
        body = re.search(r'(?ims)^\.subckt\s+'+name+r'\s+1 2 bn\s*$(.*?)^\.ends\s+'+name+r'\s*$', wrapper).group(1)
        assert not re.search(r'\b(?:isa|isp)\s*=', body, re.I)
        assert '+dfinf=1e-4' in body and '+dp=1000' in body
        assert '+postsim=0' in body and '+c1=1 c2=1' in body and '+rc=rz' in body
        assert re.search(r'^NR1 1 bn 2 dt ', body, re.M)
    assert 'Vc1      = -type*V(b_pc1);' in model and 'Vc2      = -type*V(b_pc2);' in model
    assert '`r3Ibody(Irb,geff,Vrb,Vc1,Vc2,' in model
    assert 'V1ci     = -Vc2;' in macros and 'V1ci     = -Vc1;' in macros
    assert 'dpfctr   =  1.0-df*sqrt(pe+VrbEff);' in macros
    return collections.Counter(r[4] for r in records)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--models', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    root = next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
    source = root/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    assert sha(source) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    inputs = {str(p): sha(p) for p in (source, a.models, Path(__file__).resolve())}
    bundle = json.loads(a.models.read_text())
    files = [('libs.tech/verilog-a/r3_cmc/r3_cmc-patched.va', '8a2c7a9049a1c4a47617bfd0a444bc76169b39e1399337ec580ff588b5924417'),
             ('libs.tech/verilog-a/r3_cmc/r3_cmc_macros.include', '66e1bf0b43495a9c17454a1ac203171db5488edc7e19563f4f645389ba7eebb4'),
             ('libs.tech/ngspice/models/resistors_mod.lib', '7c77da0c0419c8a332550da3f934f530262bd452734090db827b68ff88d09c43')]
    for name, expected in files:
        assert bundle[name]['sha256'] == expected
    model, macros, wrapper = ['\n'.join(bundle[name]['lines'])+'\n' for name, _ in files]
    original = source.read_text()
    count = qualify(model, macros, wrapper, original)
    negative = []
    cases = [('nonzero_isa_default', model.replace('isa       ,   0.0', 'isa       ,   1.0'), macros, wrapper, original),
             ('extra_static_substrate_branch', model+'\nI(b_pc1) <+ 1e-9;\n', macros, wrapper, original),
             ('missing_resistor', model, macros, wrapper, re.sub(r'^XR1\s[^\n]*\n', '', original, count=1, flags=re.M)),
             ('wrapper_diode_override', model, macros, wrapper.replace('+dfinf=1e-4', '+isa=1e-9\n+dfinf=1e-4'), original)]
    for name, m, mac, w, s in cases:
        rejected = False
        try:
            qualify(m, mac, w, s)
        except (AssertionError, AttributeError):
            rejected = True
        assert rejected, name
        negative.append(dict(name=name, rejected=True))
    assert all(sha(Path(p)) == h for p, h in inputs.items())
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(dict(status='passed restricted exact-model DC branch proof',
        inputs=inputs, source_resistors=399, per_model=dict(count), negative_controls=negative,
        static_NC_current='zero in the unchanged stationary R3CMC model: Is1=Is2=0, hence Ip1=Ip2=0; ddt contributions zero at DC',
        NC_voltage_independence='failed: NC voltage remains an input to body-current calculation',
        physical_substrate_mapping='not run/unresolved; this proof supplies no local substrate potential or contact/spreading network',
        AC_transient_NC_zero='not applicable; model retains capacitive current',
        model_changes='not applicable; in-memory negative controls only',
        new_analog_simulation='not run'), indent=2)+'\n')


if __name__ == '__main__':
    main()
