#!/usr/bin/env python3
"""Keep all original macro ports; conservatively block new native interior."""
import argparse
import json
import os
from pathlib import Path
import re
import pya
from export_closed_macro_lef import METALS, subtract_rectangle
from place_closed_analog import region, sha


def ports(source):
    result={}
    for name,body in re.findall(r'^  PIN (\S+)\n(.*?)^  END \1$',source,re.M|re.S):
        assert name not in result
        shapes=[]
        for layer,block in re.findall(r'      LAYER (\w+) ;\n(.*?)(?=      LAYER|    END)',body,re.S):
            number,=[k for k,v in METALS.items() if v==layer]
            for coords in re.findall(r'RECT ([\d. -]+) ;',block):
                bounds=[round(float(v)*1000) for v in coords.split()];assert len(bounds)==4
                shapes.append((number,bounds))
        assert shapes;result[name]=shapes
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('gds','reference-lef','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--sha256',required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and sha(a.gds)==a.sha256
    source=a.reference_lef.read_text();pins=ports(source);assert len(pins)==46
    assert source.count('\n  OBS\n')==1 and source.rstrip().endswith('END LIBRARY')
    ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_digital');assert ly.dbu==.001 and top
    native={layer:region(ly,top,pya.LayerInfo(layer,0)) for layer in METALS}
    windows={layer:[] for layer in METALS}
    for name,shapes in pins.items():
        for layer,bounds in shapes:
            assert (pya.Region(pya.Box(*bounds))-native[layer]).is_empty(),name
            windows[layer].append(bounds)
    lines=[];coverage=[]
    for layer,name in METALS.items():
        boxes=[[0,0,360000,360000]] if layer<=67 else [[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in native[layer].each()]
        for cut in windows[layer]:boxes=[part for box in boxes for part in subtract_rectangle(box,cut)]
        obs=pya.Region();opening=pya.Region()
        for box in boxes:obs.insert(pya.Box(*box))
        for box in windows[layer]:opening.insert(pya.Box(*box))
        assert (native[layer]-(obs+opening)).is_empty(),layer
        assert (obs&opening).is_empty()
        lines.append('    LAYER '+name+' ;')
        lines.extend('      RECT '+' '.join('%.3f'%(v*.001) for v in box)+' ;' for box in boxes)
        coverage.append(dict(layer=layer,rectangles=len(boxes),all_nonport_native_covered=True,port_obstruction_overlap_dbu2=0))
    prefix=source.split('\n  OBS\n',1)[0]
    output=prefix+'\n  OBS\n'+'\n'.join(lines)+'\n  END\nEND g1_digital\nEND LIBRARY\n'
    assert ports(output)==pins and output.split('\n  OBS\n',1)[0]==prefix
    a.output.mkdir(parents=True);dest=a.output/'g1_digital.lef';dest.write_text(output)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed conservative digital egress LEF with exact original ports',GDS_sha256=sha(a.gds),
        reference_LEF_sha256=sha(a.reference_lef),LEF_sha256=sha(dest),pins=pins,coverage=coverage,
        not_run=['OpenDB roundtrip','Routing','Native geometry DRC connectivity antenna and density','Timing extraction','Adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],ports=len(pins),LEF_sha256=sha(dest))))


if __name__=='__main__':main()
