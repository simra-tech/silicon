#!/usr/bin/env python3
"""Bind source-owned native TIE polygons to independently derived local bodies."""
import argparse
import copy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit_ownership import polygon


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def canonical(name):
    if name.startswith('g1_io_secondary_polyres_r1'):
        return 'sg13g2_secondaryprotection'
    return re.sub(r'\$\d+$','',name.removeprefix('retained_fullchip_')).lower()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    original=bulk/'io-direct-ownership-20260923-r1/analysis.json'
    junction=bulk/'io-deep-junction-20260923-r1/summary.json'
    masks=bulk/'io-deep-junction-20260923-r1/derived_tap_masks.gds'
    labels=bulk/'io-text-control-20260923-r2/raw_control.json'
    base=json.loads(original.read_text());proof=json.loads(junction.read_text())
    assert base['status']=='passed per-tap local native ownership' and not base['failures']
    assert proof['status']=='passed scoped140-IO raw hierarchical Boolean derivation; source ownership pending'
    assert sha(masks)==proof['geometry_sha256'] and all(v>0 for v in proof['coverage'].values())
    assert all(row['exact'] for row in json.loads(labels.read_text())['masters'])
    assert all(sha(Path(p))==h for p,h in proof['inputs'].items())
    source=HERE/'audit_dimensions_r2.py'
    assert sha(source)=='835beb602aa89fd75e0316b473047586336b58f6b6b594cd30bc84758c6d8965'
    scope={'__file__':str(source),'__name__':'analytical_arithmetic'}
    text=source.read_text();exec(compile(text[:text.index('\noriginal = Path')],str(source),'exec'),scope)
    measure=scope['polygon_record']
    ly=pya.Layout();ly.read(str(masks));assert ly.dbu==.001
    variants={}
    for row in proof['local_junctions']:
        cell=ly.cell(row['cell']);assert cell
        tie=pya.Region(cell.shapes(ly.layer(301,0))).merged()
        body=pya.Region(cell.shapes(ly.layer(303,0))).merged()
        assert tie.area()==row['tie_area_dbu2'] and (tie&body).area()==row['junction_area_dbu2']
        variants.setdefault(canonical(cell.name),[]).append((cell.name,tie,body))
    inputs={str(p):sha(p) for p in (original,junction,masks,labels,source,HERE/'audit_ownership.py',Path(__file__).resolve())}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running source-owned physical junction preparation',inputs=inputs,cells=[],failures=[])
    changed=[];controls=[]
    try:
        for old in base['cells']:
            row=copy.deepcopy(old);local_variants=variants.get(row['cell'].lower(),[])
            combined=pya.Region()
            for tap in row['taps']:
                for p in tap['polygons']:combined.insert(polygon(p))
            combined.merge()
            for name,tie,body in local_variants:
                assert (tie^combined).is_empty(),(row['cell'],name,'raw TIE/source polygon mismatch')
            for tap in row['taps']:
                original_geometry=pya.Region()
                for p in tap['polygons']:original_geometry.insert(polygon(p))
                original_geometry.merge()
                actual=original_geometry
                if local_variants:
                    projections=[(original_geometry&body).merged() for _,_,body in local_variants]
                    assert all((p^projections[0]).is_empty() for p in projections)
                    actual=projections[0]
                assert not actual.is_empty(),(row['cell'],tap['source']['instance'],'empty physical junction')
                polys=[measure(p) for p in actual.each()]
                area=sum(p['klayout_area_dbu2'] for p in polys)
                perimeter=sum(p['klayout_perimeter_dbu'] for p in polys)
                assert all(abs(Decimal(p['area_API_difference_dbu2']))<=Decimal('.5') for p in polys)
                assert all(abs(Decimal(p['perimeter_API_difference_dbu']))<=Decimal('.5') for p in polys)
                tap['original_direct_active_polygons']=tap['polygons']
                tap.update(polygons=polys,owned_polygon_count=len(polys),
                    area_um2=str(Decimal(area)/Decimal(1000000)),perimeter_um=str(Decimal(perimeter)/Decimal(1000)),
                    analytical_area_um2=str(sum((Decimal(p['area_um2']) for p in polys),Decimal(0))),
                    analytical_perimeter_um=str(sum((Decimal(p['perimeter_um']) for p in polys),Decimal(0))),
                    dimension_reporting='Pinned integer-DBU polygon area/perimeter; analytical rounding error independently bounded, not fitted.',
                    body_context=('actual current140-IO local-body variants; exact identical projections' if local_variants else
                        'native source-cell isolated junction; global Boolean hierarchy omits this locally covered child'),
                    local_body_variants=[n for n,_,_ in local_variants])
                if not (actual^original_geometry).is_empty():
                    changed.append(dict(cell=row['cell'],instance=tap['source']['instance'],
                        raw_direct_area_dbu2=original_geometry.area(),junction_area_dbu2=actual.area(),
                        removed_area_dbu2=(original_geometry-actual).area(),body_variants=tap['local_body_variants']))
                    moved=(original_geometry&local_variants[0][2].moved(1,0)).merged()
                    controls.append(dict(cell=row['cell'],instance=tap['source']['instance'],
                        moved_body_rejected=not (moved^actual).is_empty(),
                        omitted_body_rejected=actual.area()>0,
                        original_unclipped_rejected=not (original_geometry^actual).is_empty()))
            result['cells'].append(row)
        assert changed and all(all(v for k,v in r.items() if k.endswith('_rejected')) for r in controls)
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed per-tap physical junction ownership; stock/electrical validation pending',
            changes=changed,negative_controls=controls,source_taps=63,
            parameter_targets_read='not applicable; no extracted device database or parameters were inputs',
            hierarchy_note='Individual source-cell primitives retained; source hierarchy can contain overlapping drawing. This is not a globally exclusive substrate-resistance partition.',
            fullchip_nonIO_context='not run; bounded140-IO plus actual top mask context',
            electrical_R='not run; rectangle/ring coefficient convention remains unresolved',strict_LVS='not run',adoption='not run')
    except Exception as exc:
        result.update(status='failed junction ownership preparation',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
