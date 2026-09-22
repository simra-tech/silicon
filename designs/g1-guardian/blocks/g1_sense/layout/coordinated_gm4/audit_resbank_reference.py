#!/usr/bin/env python3
"""Saved95R dimensions/head graph and complete source-derived reference."""
import argparse,copy,json,os,re
from pathlib import Path
from build_native_prototypes import pya,snapshot,sha
from build_source_faithful_buffer import full_nets
from spice2cdl import convert

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    m=json.loads((a.candidate/'manifest.json').read_text());gds=a.candidate/'g1_sense_resistor_bank.gds';assert sha(gds)==m['GDS_sha256']
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)==m['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    block=re.search(r'(?ms)^\.subckt g1_sense .*?^\.ends',source.read_text()).group(0);specs={line.split()[0]:line for line in block.splitlines()if ' rppd 'in line};assert len(specs)==95 and specs=={r['device']:r['source_line']for r in m['devices']}
    ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_sense_resistor_bank');r=snapshot(cell,128);assert r.count()==95
    assert all(p.bbox().width()==2000 and p.bbox().height()==76700 and p.area()==153400000 for p in r.each())
    for row in m['devices']:
        x,y=row['head_points_um'][0];middle=pya.DPoint(x,11.43+row['row']*83.92+38.35).to_itype(.001)
        assert sum(poly.inside(middle)for poly in r.each())==1
    graph=full_nets(cell,copy.deepcopy(m['terminal_audit']['probes']));assert graph['status']=='passed'
    assert(snapshot(cell,1)&snapshot(cell,5)).is_empty()
    for li in ly.layer_indexes():
        for poly in pya.Region(cell.begin_shapes_rec(li)).each():
            for pt in poly.each_point_hull():assert pt.x%5==pt.y%5==0
            for h in range(poly.holes()):
                for pt in poly.each_point_hole(h):assert pt.x%5==pt.y%5==0
    ports=list(m['ports']);assert len(ports)==9
    a.output.mkdir(parents=True);cdl=a.output/'g1_sense_resistor_bank.cdl';cdl.write_text('\n'.join(convert(['.subckt g1_sense_resistor_bank '+' '.join(ports)]+list(specs.values())+['.ends g1_sense_resistor_bank']))+'\n');assert sha(cdl)==m['CDL_sha256']
    result=dict(status='passed saved-polygon and exact source reference gate',source_sha256=sha(source),GDS_sha256=sha(gds),CDL_sha256=sha(cdl),manifest_sha256=sha(a.candidate/'manifest.json'),script_sha256=sha(Path(__file__)),devices=m['devices'],terminal_audit=graph,ports=ports,stock_checks='not run',PEX='not run')
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');(a.output/'audit_snapshot.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items()if k not in('devices','terminal_audit')},indent=2))
if __name__=='__main__':main()
