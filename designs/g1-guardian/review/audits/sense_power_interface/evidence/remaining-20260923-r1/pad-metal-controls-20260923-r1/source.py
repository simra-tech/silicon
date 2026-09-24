#!/usr/bin/env python3
"""Qualify top-metal extension of native metallic-R API; no device extraction."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import klayout.db as kdb
import klayout.pex as klp

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]/'blocks/g1_bgr/layout/coordinated_return_remedy/extract_metal_r.py'
spec=importlib.util.spec_from_file_location('isolated_native_metal_r',BASE)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
PAIRS=dict(base.PAIRS,TM1=(126,0),TM2=(134,0),TopVia1=(125,0),TopVia2=(133,0))
CUTS=dict(base.CUTS,TopVia1=('M5','TM1'),TopVia2=('TM1','TM2'))
IDS={name:i for i,name in enumerate(PAIRS)}
SIZE={name:(.42 if name=='TopVia1'else .9 if name=='TopVia2'else .19)for name in CUTS}
base.PAIRS=PAIRS;base.CUTS=CUTS;base.IDS=IDS


def technology(scenario):
    tech=klp.RExtractorTech();tech.skip_simplify=True
    for name,resistance in scenario['sheet_ohm'].items():
        conductor=klp.RExtractorTechConductor();conductor.layer=IDS[name]
        conductor.algorithm=klp.Algorithm.SquareCounting
        conductor.triangulation_min_b=.5;conductor.triangulation_max_area=50.
        conductor.resistance=resistance;tech.add_conductor(conductor)
    for name,resistance in scenario['cut_ohm'].items():
        via=klp.RExtractorTechVia();via.cut_layer=IDS[name]
        via.bottom_conductor=IDS[CUTS[name][0]];via.top_conductor=IDS[CUTS[name][1]]
        via.resistance=resistance*SIZE[name]**2;via.merge_distance=0.
        tech.add_via(via)
    return tech


base.technology=technology


def scenario():
    lef=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
    assert base.sha(lef)=='054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
    values={}
    names={'Metal'+str(i):'M'+str(i)for i in range(1,6)}
    names.update(TopMetal1='TM1',TopMetal2='TM2')
    for name,body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$',lef.read_text(),re.M|re.S):
        if name in names or name in CUTS:
            matches=re.findall(r'^\s*RESISTANCE\s+(?:RPERSQ\s+)?([0-9.]+)\s*;',body,re.M)
            assert len(matches)==1;values[name]=float(matches[0])
    return dict(sheet_ohm={short:values[name]for name,short in names.items()},
                cut_ohm={name:values[name]for name in CUTS},LEF_sha256=base.sha(lef),
                scope='Pinned LEF resistance scenario; .103ohm/square and20ohm Via1–4 are tabulated maxima, not nominal/hot bounds')


def controls(output):
    model=scenario();rows=[]
    for name,(lower,upper)in CUTS.items():
        size=round(SIZE[name]*1000)
        pitch=840 if name=='TopVia1' else 1960 if name=='TopVia2' else 420
        for count in(1,2):
            extent=size//2 if count==1 else pitch//2+size//2
            plate=kdb.Box(-extent,-size//2,extent,size//2)
            regions={IDS[lower]:kdb.Region(plate),IDS[upper]:kdb.Region(plate),IDS[name]:kdb.Region()}
            for x in([0]if count==1 else[-pitch//2,pitch//2]):
                regions[IDS[name]].insert(kdb.Box(x-size//2,-size//2,x+size//2,size//2))
            points=[dict(id=i,layer=layer,point_dbu=[0,0],injection_A=.001 if i==0 else-.001,
                         source_net='coupon',reference_ports=['a']if i==0 else[])
                    for i,layer in enumerate((lower,upper))]
            raw=base.extract(regions,points,model);solved,_=base.solve(raw,points,1)
            actual=abs(solved['points'][1]['delta_V'])/.001
            expected=model['cut_ohm'][name]/count
            if count==2:expected+=(pitch/2/size)*(model['sheet_ohm'][lower]+model['sheet_ohm'][upper])/2
            rows.append(dict(cut=name,count=count,size_um=SIZE[name],pitch_um=pitch*.001,
                actual_ohm=actual,expected_ohm=expected,passed=abs(actual-expected)<=1e-8,raw=raw,solution=solved))
            base.dump(output/(name+'_'+str(count)+'.json'),rows[-1])
    assert len(rows)==12 and all(r['passed']for r in rows)
    return rows,model


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and kdb.__version__=='0.30.9'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',script_sha256=base.sha(Path(__file__)),base_helper_sha256=base.sha(BASE),
                not_run=['native pad distribution','loaded full-chip IR/EM/current capacity','adoption'])
    try:
        rows,model=controls(a.output)
        result.update(status='passed twelve analytic native-metal via controls',scenario=model,
                      controls=[{k:v for k,v in r.items()if k not in('raw','solution')}for r in rows])
    except Exception as exc:
        result.update(status='failed native-metal API controls',error=repr(exc));raise
    finally:
        base.dump(a.output/'summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
