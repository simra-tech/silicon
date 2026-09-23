#!/usr/bin/env python3
"""Probe actual routed metal at all declared LEF terminal windows, no label joins."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import pya
from add_fullchip_native_instances import transform
from audit_placed_decap_domains import physical, identity
from place_closed_analog import region, sha

LAYERS=dict(Metal1=8,Metal2=10,Metal3=30,Metal4=50,Metal5=67,TopMetal1=126,TopMetal2=134,
            Via1=19,Via2=29,Via3=49,Via4=66,TopVia1=125,TopVia2=133)
CUTS={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
SUPPLIES={'VDD','VSS','VDDA','IOVDD','IOVSS'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--gds-name',required=True)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--odb-check',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--flat-physical',action='store_true')
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=a.candidate/a.gds_name;metadata=json.loads((a.candidate/'analysis.json').read_text())
    assert metadata['status'].startswith('passed') and sha(source)==metadata['GDS_sha256']
    prepared=json.loads((a.prepared/'analysis.json').read_text());odb=json.loads((a.odb_check/'analysis.json').read_text())
    assert prepared['DEF_sha256']==odb['source_DEF_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    masters={}
    for entry in odb['LEFs']:
        path=Path(entry['path']);assert sha(path)==entry['sha256']
        for name,body in re.findall(r'^MACRO (\S+)\n(.*?)^END \1$',path.read_text(),re.M|re.S):
            size=re.search(r'\bSIZE ([\d.]+) BY ([\d.]+) ;',body)
            assert size and name not in masters
            pins={}
            for pin,block in re.findall(r'^\s*PIN (\S+)\s*\n(.*?)^\s*END \1\s*$',body,re.M|re.S):
                assert not re.search(r'\b(?:POLYGON|PATH)\b',block),(name,pin,'nonrectangular unsupported LEF geometry')
                rects=[];layer=None
                for match in re.finditer(r'\bLAYER (\S+)\s*;|\bRECT\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*;',block):
                    if match[1]:layer=LAYERS[match[1]]
                    else:
                        assert layer is not None
                        rects.append((layer,[round(float(v)*1000)for v in match.groups()[1:]]))
                assert rects,(name,pin)
                pins[pin]=rects
            masters[name]=dict(size=[round(float(v)*1000)for v in size.groups()],pins=pins)
    components={r['instance']:dict(master=r['master'],xy=r['new'][:2],orient=r['new'][2])for r in prepared['changes']}
    components.update({r['instance']:r for r in prepared['added_native_IO_fillers']})
    assert len(components)==4904
    logical=collections.defaultdict(set)
    for line in (a.odb_check/'roundtrip.tsv').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='CONN':logical[fields[1]].add(tuple(fields[2:]))
    layout=pya.Layout();layout.read(str(source));top=layout.top_cell()
    if a.flat_physical:
        from flat_metal_connectivity import flat_physical
        net,metal,flat_layout_held=flat_physical(layout,top)
    else:
        net,metal=physical(layout,top)
    actual={layer:region(layout,top,pya.LayerInfo(layer,0))for layer in LAYERS.values()}
    observations=[];errors=[];by_logical=collections.defaultdict(set);by_physical=collections.defaultdict(set)
    external=[]
    for name,terminals in sorted(logical.items()):
        for instance,pin in sorted(terminals):
            if instance=='PIN':external.append(dict(net=name,pin=pin));continue
            comp=components[instance];master=masters[comp['master']]
            tr=transform(comp['xy'],comp['orient'],master['size'])
            clusters=set();windows=[]
            for layer,rect in master['pins'][pin]:
                box=tr*pya.Box(*rect);overlap=actual[layer]&pya.Region(box)
                found=set()
                for polygon in overlap.each():
                    # First vertex lies on real drawn metal. A non-null probe
                    # is required; no nearest-conductor or label substitution.
                    point=next(polygon.each_point_hull())
                    for probe_layer in CUTS.get(layer,(layer,)):
                        key=identity(net,metal[probe_layer],[point.x,point.y])
                        if key is None:
                            errors.append(dict(net=name,instance=instance,pin=pin,layer=layer,probe_layer=probe_layer,error='off-metal polygon probe',point=str(point)))
                        else:found.add(key)
                clusters.update(found)
                windows.append(dict(layer=layer,bbox=[box.left,box.bottom,box.right,box.top],
                                    native_area_um2=overlap.area()*1e-6,clusters=[list(v)for v in sorted(found)]))
            if not clusters:errors.append(dict(net=name,instance=instance,pin=pin,error='no actual conductor in any LEF window'))
            observations.append(dict(net=name,instance=instance,pin=pin,clusters=[list(v)for v in sorted(clusters)],windows=windows))
            by_logical[name].update(clusters)
            for key in clusters:by_physical[key].add(name)
    shorts=[dict(component=list(k),logical_nets=sorted(v))for k,v in by_physical.items()if len(v)>1]
    splits={name:len(parts)for name,parts in by_logical.items()if len(parts)!=1}
    signal_splits={k:v for k,v in splits.items()if k not in SUPPLIES}
    passed=not errors and not shorts and not signal_splits
    result=dict(status='passed scoped signal terminal connectivity'if passed else'failed scoped signal terminal connectivity',
                GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),LEF_binding_sha256=sha(a.odb_check/'analysis.json'),
                extraction_scope='flat instance-resolved geometry'if a.flat_physical else'hierarchical; repeated unconnected local-cell identities may alias',
                flat_helper_sha256=sha(Path(__file__).with_name('flat_metal_connectivity.py'))if a.flat_physical else None,
                logical_nets=len(logical),terminal_observations=len(observations),errors=errors,unexpected_net_merges=shorts,
                split_components=splits,signal_splits=signal_splits,external_BTerms_not_probed=external,observations=observations,
                not_run=['external BTerm physical binding','device-aware full LVS','complete PDN supply connectivity',
                         'electrical/currentIR/EM qualification'],not_applicable=['label-based virtual net joining'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='observations'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
