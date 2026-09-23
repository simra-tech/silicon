#!/usr/bin/env python3
"""Pinned formula/shape accounting only; do not select a new electrical R."""
import argparse
import collections
from decimal import Decimal,localcontext
import hashlib
import json
import os
from pathlib import Path
import re


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    pdk=Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    source=Path(os.environ['G1_RESULTS_ROOT'])/'io-physical-ap-source-20260923-r2/summary.json'
    j=json.loads(source.read_text());assert j['source_sha256']=='796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf'
    assert j['status'].startswith('passed') and j['reachable_taps']==386
    paths=[pdk/'libs.tech/xschem/sg13g2_pr'/n for n in ('ptap1.sym','ptap1_ring.sym','ntap1.sym')]
    found=[]
    for root,pattern in [(pdk/'libs.tech/ngspice','*'),(pdk/'libs.tech/klayout/python','*.py')]:
        for p in sorted(root.rglob(pattern)):
            if not p.is_file() or p.stat().st_size>5*2**20:continue
            try:text=p.read_text()
            except UnicodeError:continue
            if re.search(r'(?im)^\s*\.subckt\s+ptap1\b|^def CbTapCalc\(',text):
                paths.append(p);found.append(str(p.relative_to(pdk)))
    assert any('ngspice' in x for x in found) and any('klayout' in x for x in found),found
    a.output.mkdir(parents=True);artifacts=[]
    for p in paths:
        rel=p.relative_to(pdk);dest=a.output/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(p.read_bytes());artifacts.append(dict(path=str(rel),sha256=sha(p)))
    classes=collections.Counter();rows=[]
    for row in j['changed_records']:
        classification=tuple(sorted({p['classification'] for p in row['owned_geometry']['polygons']}))
        classes['; '.join(classification)]+=1
        # Exact counts by parameter pair are not unique identifiers. Keep the
        # local record ledger; expanded total is separately source-qualified.
        with localcontext() as ctx:
            ctx.prec=50
            area=Decimal(row['A_um2']);perimeter=Decimal(row['P_um'])
            r1=Decimal(980)/(area+perimeter);r2=Decimal(980)/(area+2*perimeter)
            assert str(r1)==row['conditional_single_perimeter_R_ohm']
            assert str(r2)==row['conditional_double_perimeter_R_ohm']
        rows.append(dict(cell=row['cell'],instance=row['instance'],classification=classification,
            original_SPI_R=row['original_SPI_R'],A_um2=str(area),P_um=str(perimeter),
            conditional_single_perimeter_R_ohm=str(r1),conditional_double_perimeter_R_ohm=str(r2),
            selected_R='not run'))
    assert sum(classes.values())==42
    report=dict(status='passed pinned expression capture and arithmetic; electrical applicability unresolved',
        inputs={str(source):sha(source),str(Path(__file__)):sha(Path(__file__))},
        pinned_artifacts=artifacts,shape_classes=dict(classes),local_records=42,expanded_source_taps=386,rows=rows,
        failed=['A unique generally applicable electrical perimeter convention has not been established.'],
        not_run=['New R source selection','Power sequencing with new R','ESD qualification','substrate spreading validation'],
        not_applicable=['Model card edits','Rule edits','Resistance selection from LVS pass/fail'])
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
