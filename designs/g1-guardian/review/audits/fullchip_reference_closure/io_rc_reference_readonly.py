#!/usr/bin/env python3
"""Pinned read-only RC source/PCell/model/annotation reconciliation; no simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import re

PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate-summary',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    paths={name:PDK/path for name,path in dict(
        CDL='libs.ref/sg13g2_io/cdl/sg13g2_io.cdl',
        SPICE='libs.ref/sg13g2_io/spice/sg13g2_io.spi',
        model='libs.tech/ngspice/models/resistors_mod.lib',
        technology='libs.tech/klayout/python/sg13g2_pycell_lib/sg13g2_tech.json',
        callback='libs.tech/klayout/python/sg13g2_pycell_lib/ihp/utility_functions.py').items()}
    source={k:p.read_text() for k,p in paths.items()}
    bodies={k:re.search(r'(?im)^\.subckt sg13g2_RCClampResistor .*?^\.ends[^\n]*',source[k],re.S).group(0) for k in ('CDL','SPICE')}
    cdlrows=[l for l in bodies['CDL'].splitlines() if l.startswith('RR')]
    spicerows=[l for l in bodies['SPICE'].splitlines() if l.startswith('XR')]
    assert len(cdlrows)==len(spicerows)==26
    assert all(l.split()[3]=='5.239K' and '$[rppd]' in l and 'l=20u w=1u' in l for l in cdlrows)
    assert all('rppd R=5.239K l=20u w=1u' in l for l in spicerows)
    model=re.search(r'(?im)^\.subckt rppd\b.*?^\.ends rppd[^\n]*',source['model'],re.S).group(0)
    assert not re.search(r'\bR\b',model,re.I), 'Standalone passed R is unexpectedly consumed in wrapper'
    assert 'NR1 1 bn 2 dt res_rppd L=leff W=weff m=m' in model
    callback=source['callback'].split('def CbResCalc(',1)[1].split('def CbResCurrent(',1)[0]
    formula='result = l/weff*(b+1)*rspec+(2.0/kappa*weff+ps)*b/weff*rspec+2.0/w*rzspec'
    assert formula in callback and "suffix = 'G2'" in callback
    technology=json.loads(source['technology'])
    def find(x):
        if isinstance(x,dict):
            if 'rppdG2_rspec' in x:return x
            for v in x.values():
                found=find(v)
                if found is not None:return found
    t=find(technology);assert t
    selected={k:t[k] for k in ('rppdG2_rspec','rppdG2_lwd','rppd_rzspec','rppd_kappa')}
    assert selected=={'rppdG2_rspec':'260.0','rppdG2_lwd':'0.006u','rppd_rzspec':'35e-6','rppd_kappa':'1.85'}
    calculated=20/(1+.006)*260+2/1*35
    assert round(calculated)==5239
    prep=json.loads(a.candidate_summary.read_text());rc=next(c for c in prep['cells'] if c['kind']=='rc')
    texts=next(t for t in rc['texts'] if t['layer']==[63,0])['values']
    assert len(texts)==26 and all("rppd r=7.938k" in t for t in texts)
    result=dict(status='passed pinned read-only source/calculator observations; electrical qualification not run',
        PDK_commit=(PDK/'COMMIT').read_text().strip(),
        inputs={name:dict(path=str(p.relative_to(PDK)),sha256=sha(p)) for name,p in paths.items()},
        candidate_preparation_sha256=sha(a.candidate_summary),source_chain_records=26,
        both_CDL_and_SPICE_numeric_R_ohm=5239,native_annotation_numeric_R_ohm=7938,
        current_PCell_parameters=selected,calculator_expression='20/(1+0.006)*260+2*35',
        calculated_PCell_R_ohm=calculated,rounded_CDL_match=True,
        calculator_formula_literal=formula,
        model_observation='Pinned rppd wrapper contains no standalone R token; primitive resistance uses L/W, rsh_rppd, xw and rc. Passed legacy R is not referenced by this wrapper.',
        source_cell_bodies=bodies,model_wrapper=model,
        interpretation='7.938k drawing annotations are inconsistent with current pinned PCell calculation and both electrical source views. Their historical origin is not established; no automatic text/model edit.',
        not_run=['ngspice acceptance/behavior of extra R argument','compact-model operating resistance','RC clamp transient/ESD','fullchip adoption'],
        not_applicable=['simulation seed','model/rule changes'],script_sha256=sha(Path(__file__)))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])


if __name__=='__main__':main()
