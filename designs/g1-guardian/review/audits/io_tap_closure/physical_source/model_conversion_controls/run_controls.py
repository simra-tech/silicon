#!/usr/bin/env python3
"""Two native geometry cases: source arithmetic and unchanged ptap1 I–V only."""
import argparse
import ast
from decimal import Decimal,localcontext
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import numpy as np

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def expression(line,field,values):
    text,=re.findall(field+r'=\[ev7? \\\{\s*(.*?)\\\}',line)
    for key,value in values.items():text=text.replace('@'+key,str(value))
    tree=ast.parse(text.strip(),mode='eval')
    allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.UAdd,ast.USub)
    assert all(isinstance(n,allowed) for n in ast.walk(tree))
    return eval(compile(tree,'pinned_symbol_expression','eval'),{'__builtins__':{}},{})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT']);pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    proof=bulk/'io-physical-ap-source-20260923-r2/summary.json';j=json.loads(proof.read_text())
    assert j['source_sha256']=='796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf'
    models=pdk/'libs.tech/ngspice/models/resistors_mod.lib'
    rect=pdk/'libs.tech/xschem/sg13g2_pr/ptap1.sym';ring=rect.with_name('ptap1_ring.sym')
    utility=pdk/'libs.tech/klayout/python/sg13g2_pycell_lib/ihp/utility_functions.py'
    expected={models:'7c77da0c0419c8a332550da3f934f530262bd452734090db827b68ff88d09c43',
        rect:'8d4286ec5619cf2dcbe63e3811ffb69a1256ad299a0d52569e365e3b21649976',
        ring:'70bc070fc157dfdebe2cc07e7c0ccf3fd9b0980144760e9e00d602e23c95cd45',
        utility:'0d5c287ede8decd8b69c8f94bfe72231758e607c02b64650951fcb5be269c861'}
    assert all(sha(p)==h for p,h in expected.items())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    inputs={str(p):sha(p) for p in list(expected)+[proof,Path(__file__)]}
    result=dict(status='running source conversion controls',inputs=inputs,
        prospective_numerical_bound='absolute current error <= 1e-15 A + 1e-12*abs(V/R); zero-voltage current <=1e-18 A',
        scope='One actual rectangle and one actual uniform ring polygon, each under two arithmetic conventions. No shape/R qualification or model-card edit.',
        physical_R_qualification='not run',power_sequencing_ESD='not run')
    def save():(a.output/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    save()
    try:
        rows=[]
        for name,ending,classification,symbol in [('rectangle','LEVELUPINV','rectangle',rect),
                ('ring','SECONDARYPROTECTION','uniform rectangular ring',ring)]:
            entry,=[r for r in j['changed_records'] if r['cell'].endswith(ending)]
            polygon=entry['owned_geometry']['polygons'][0]
            assert polygon['classification']==classification
            hull=polygon['hull_and_holes'][0]
            w=Decimal(max(p[0] for p in hull)-min(p[0] for p in hull))/1000
            l=Decimal(max(p[1] for p in hull)-min(p[1] for p in hull))/1000
            area=Decimal(polygon['area_um2']);perimeter=Decimal(polygon['perimeter_um'])
            params={'w':float(w)*1e-6,'l':float(l)*1e-6}
            if name=='rectangle':assert area==w*l and perimeter==2*(w+l)
            else:
                widths=polygon['rectangular_ring_widths_dbu'];assert len(set(widths))==1
                rw=Decimal(widths[0])/1000;params['rw']=float(rw)*1e-6
                assert area==2*rw*(w+l-2*rw) and perimeter==4*(w+l-2*rw)
            formatline,=[line for line in symbol.read_text().splitlines() if line.startswith('format=')]
            lvsline,=[line for line in symbol.read_text().splitlines() if line.startswith('lvs_format=')]
            symbol_R=expression(formatline,'R',params)
            symbol_A=expression(lvsline,'A',params)*1e12;symbol_P=expression(lvsline,'P',params)*1e6
            assert abs(symbol_A-float(area))<=64*math.ulp(float(area))
            assert abs(symbol_P-float(perimeter))<=64*math.ulp(float(perimeter))
            values={k:float(Decimal(980)/(area+k*perimeter)) for k in (1,2)}
            published_k=1 if name=='rectangle' else 2
            assert abs(symbol_R-values[published_k])<=64*math.ulp(values[published_k])
            rows.append(dict(case=name,source_cell=entry['cell'],source_instance=entry['instance'],
                polygon_index=0,polygon=polygon,W_um=str(w),L_um=str(l),A_um2=str(area),P_um=str(perimeter),
                symbol_parameters_SI=params,symbol_R_ohm=symbol_R,symbol_perimeter_factor=published_k,
                R_ohm={str(k):v for k,v in values.items()},symbol_AP_vs_native='passed',symbol_R_vs_declared_formula='passed'))
        # Exact function body, not a rewritten numerical implementation.
        func,=[n for n in ast.parse(utility.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='CbTapCalc']
        namespace={'Numeric':float,'techparams':{'ptap1_raspec':9.8e-10,'ptap1_rpspec':9.8e-4}}
        exec(compile(ast.Module(body=[func],type_ignores=[]),str(utility),'exec'),namespace)
        rectangle=rows[0];params=rectangle['symbol_parameters_SI']
        pcell=namespace['CbTapCalc']('R',0,params['l'],params['w'],'ptap1')
        assert abs(pcell-rectangle['R_ohm']['1'])<=64*math.ulp(pcell)
        result.update(cases=rows,rectangle_CbTapCalc_with_literal_symbol_coefficients=pcell,
            coefficient_scope='Literal pinned symbol coefficients supplied to unchanged CbTapCalc body; no technology-file/default applicability inferred')
        deck=['* Two source-conversion controls, not physical tap qualification',
            '.include "'+str(models)+'"','.options numdgt=17','Vtest drive 0 0']
        vectors=[];expected_R=[]
        for index,row in enumerate(rows):
            for k in (1,2):
                name='c%d%d'%(index,k);value=row['R_ohm'][str(k)]
                deck+=['E'+name+' pre'+name+' 0 drive 0 1','V'+name+' pre'+name+' n'+name+' 0',
                    'X'+name+' n'+name+' 0 ptap1 R='+format(value,'.17g')]
                vectors.append('i(V'+name+')');expected_R.append(value)
        deck+=['.control','set wr_singlescale','set wr_vecnames','set numdgt=17','dc Vtest -0.01 0.01 0.005',
            'wrdata '+str(a.output/'iv.dat')+' v(drive) '+' '.join(vectors),'quit','.endc','.end']
        path=a.output/'controls.cir';path.write_text('\n'.join(deck)+'\n')
        result.update(deck_sha256=sha(path),ngspice_version=subprocess.check_output(['ngspice','--version'],text=True))
        assert 'ngspice-46' in result['ngspice_version'];save()
        with (a.output/'console.log').open('x') as log:
            run=run_bounded(['ngspice','-b',str(path)],log,a.output/'run.json',20,cwd=ROOT,interval_s=1)
        result['run']=run;save()
        assert run['status']=='completed' and run['returncode']==0
        log=(a.output/'console.log').read_text()
        assert not re.search(r'(?im)^\s*(?:error|fatal)|unknown parameter|singular matrix',log)
        values=np.loadtxt(a.output/'iv.dat',skiprows=1);assert values.shape==(5,6) and np.isfinite(values).all()
        assert np.array_equal(values[:,0],values[:,1])
        checks=[]
        for i,resistance in enumerate(expected_R):
            predicted=values[:,1]/resistance;observed=values[:,i+2]
            bound=1e-15+1e-12*np.abs(predicted);error=np.abs(observed-predicted)
            passed=bool(np.all(error<=bound) and np.all(np.abs(observed[values[:,1]==0])<=1e-18))
            checks.append(dict(vector=vectors[i],R_ohm=resistance,max_absolute_error_A=float(error.max()),passed=passed))
        assert all(r['passed'] for r in checks)
        assert all(sha(Path(p))==h for p,h in inputs.items()) and sha(path)==result['deck_sha256']
        result.update(status='passed two-case source/model execution controls; physical applicability not qualified',I_V_checks=checks,
            row_count=5,finite_full_vector_coverage=True,input_rule_model_parity='passed',
            negative_controls=dict(wrong_perimeter_formula_rejected=rows[1]['R_ohm']['1']!=rows[1]['symbol_R_ohm'],
                inverted_current_sign_rejected=bool(np.any(np.abs(values[:,2]+values[:,1]/expected_R[0])>1e-15))))
        assert all(result['negative_controls'].values())
    except BaseException as exc:
        result.update(status='failed source/model execution control',error=repr(exc));raise
    finally:save()


if __name__=='__main__':main()
