#!/usr/bin/env python3
"""Assign original decap domains using three independently specified metal anchors."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical,identity,sha,DESIGN,HERE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--placement',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    baseline=DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    assert sha(baseline)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    placement=json.loads((args.placement/'analysis.json').read_text())
    assert placement['baseline_sha256']==sha(baseline) and len(placement['decaps'])==4662
    mesh=HERE/'supply-mesh-20260921-r3/mesh.json'
    anchors=json.loads(mesh.read_text())['source_interfaces']
    assert anchors=={'VDDA':['TopMetal1',946.02,389.34],'VDD':['TopMetal2',395.0,354.66],'VSS':['TopMetal2',507.0,334.66]}
    layout=pya.Layout();layout.read(str(baseline))
    net,layers=physical(layout,layout.cell('g1_chip_top'))
    names={}
    checks=[]
    for name,(layer,x,y) in anchors.items():
        found=identity(net,layers[126 if layer=='TopMetal1' else 134],[round(x/layout.dbu),round(y/layout.dbu)])
        assert found is not None and found not in names
        names[found]=name
        checks.append(dict(name=name,layer=layer,point_um=[x,y],physical_net=found))
    assignments=[];errors=[]
    for row in placement['decaps']:
        pins={label:names.get(identity(net,layers[8],probe['original_dbu']),'unmapped') for label,probe in row['pins'].items()}
        if pins!={'VDD':'VDD','VSS':'VSS'}:
            errors.append(dict(index=row['index'],pins=pins))
        assignments.append(dict(index=row['index'],pins=pins))
    counts=collections.Counter((r['pins']['VDD'],r['pins']['VSS']) for r in assignments)
    result=dict(status='passed original decap VDD/VSS assignment' if not errors else 'failed original decap VDD/VSS assignment',
                baseline_sha256=sha(baseline),placement_manifest_sha256=sha(args.placement/'analysis.json'),
                mesh_sha256=sha(mesh),script_sha256=sha(Path(__file__)),KLayout=pya.__version__,
                anchors=checks,counts=[dict(supply=k[0],ground=k[1],decaps=v) for k,v in counts.items()],errors=errors,
                method='All anchor and decap probes share one physical extraction; incidental cluster numbers are never compared across extractions. Mesh source labels identify intended rails, not imposed physical joins.',
                not_run=['reconnected placed decap feeds','physical voltage/current limits','fullchip LVS/PEX/signoff'])
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(errors))


if __name__=='__main__':
    main()
