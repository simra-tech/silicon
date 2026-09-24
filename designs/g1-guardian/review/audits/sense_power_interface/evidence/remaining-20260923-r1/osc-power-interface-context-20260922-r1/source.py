#!/usr/bin/env python3
"""Screen an isolated new feed against frozen signals and the SENSE feed."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import region,sha
from build_interface import METALS,CUTS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--signals',type=Path,required=True)
    p.add_argument('--sense',type=Path,required=True)
    p.add_argument('--bgr',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert pya.__version__=='0.30.9'and len(os.sched_getaffinity(0))==1
    pm=json.loads((a.candidate/'analysis.json').read_text());source=a.candidate/'power_overlay.gds'
    assert pm['status'].startswith('passed')and sha(source)==pm['overlay_sha256']
    pl=pya.Layout();pl.read(str(source));pt=pl.top_cell()
    power={l:region(pl,pt,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
    contexts=[('signals',a.signals,'03473e0dd19b9d69be9faa5e7b9edb4254c7aabab354b8899d18b0bba586703b'),
              ('sense_feed',a.sense,'a16aa0d622329a4d5de51b658a3d57f0e7cf1d1be1cdd4228dfead0856f56ca0')]
    if a.bgr:contexts.append(('bgr_feed',a.bgr,'a164d870d685b91877f23ddcf5d9d7aeb725c60b7f54c330d4c3b0e04d1c269b'))
    rows=[]
    for name,path,digest in contexts:
        assert sha(path)==digest
        sl=pya.Layout();sl.read(str(path));st=sl.top_cell()
        foreign={l:region(sl,st,pya.LayerInfo(l,0))for l in power}
        for l in power:
            margin=(.4 if l<100 else 2 if l==126 else 5)if l in METALS else(.29 if l<100 else .42 if l==125 else 1.06)
            overlap=power[l]&foreign[l];near=power[l]&foreign[l].sized(round(margin*1000))
            rows.append(dict(context=name,layer=l,margin_um=margin,overlap_um2=overlap.area()*1e-6,
                             proximity_um2=near.area()*1e-6))
        for l,(lo,hi)in CUTS.items():
            old_capture=(power[lo]+power[hi])&foreign[l]
            new_capture=power[l]&(foreign[lo]+foreign[hi])
            rows.append(dict(context=name,cut_layer=l,old_cut_capture_um2=old_capture.area()*1e-6,
                             new_cut_capture_um2=new_capture.area()*1e-6))
    failures=[r for r in rows if any(v!=0 for k,v in r.items()if k.endswith('_um2'))]
    result=dict(status='passed frozen signal and SENSE feed context'if not failures else'failed frozen feed context',
                overlay_sha256=sha(source),script_sha256=sha(Path(__file__)),
                contexts=[dict(name=n,sha256=h)for n,q,h in contexts],checks=rows,failures=failures,
                scope='Exact physical overlay polygons/cuts; conservative same-layer spacing and cross-layer via capture. Historical route source binding remains separate.',
                not_run=['future changed root assembly','combined stock DRC','coupling/IR/EM/LVS','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='checks'},indent=2))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
