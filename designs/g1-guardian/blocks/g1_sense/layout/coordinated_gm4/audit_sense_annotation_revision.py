#!/usr/bin/env python3
"""Prove the nine-port revision changes pin annotations only, no native layers."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('before','after','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    layouts=[]
    for f in(a.before,a.after):
        ly=pya.Layout();ly.read(str(f));assert ly.dbu==.001;layouts.append(ly)
    cells=[ly.cell('g1_sense_physical')for ly in layouts];infos={(ly.get_info(i).layer,ly.get_info(i).datatype)for ly in layouts for i in ly.layer_indexes()};rows=[]
    for layer,dt in sorted(infos):
        rs=[pya.Region(c.begin_shapes_rec(ly.layer(layer,dt))).merged()for ly,c in zip(layouts,cells)];area=(rs[0]^rs[1]).area()*1e-6
        assert area==0 or dt in(2,25),(layer,dt,area)
        if dt in(2,25):assert(rs[1]-rs[0]).is_empty()
        rows.append(dict(layer=layer,datatype=dt,XOR_um2=area))
    labels=[]
    for ly,c in zip(layouts,cells):labels.append([s.text.string for li in ly.layer_indexes()if ly.get_info(li).datatype==25 for s in c.shapes(li).each()if s.is_text()])
    assert set(labels[0])-set(labels[1])=={'vn','vp','vped_ref'} and len(set(labels[1]))==9
    result=dict(status='passed annotation-only nine-port revision',before_sha256=sha(a.before),after_sha256=sha(a.after),script_sha256=sha(Path(__file__)),layers=rows,top_labels_before=labels[0],top_labels_after=labels[1],scope='All non-pin-annotation polygon layers XOR0, including every native/conductive/mask layer. Only redundant top resistor-bank diagnostic pin annotations removed; child pin annotations unchanged. No source/card/deck change.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='layers'},indent=2))
if __name__=='__main__':main()
