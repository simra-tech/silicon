#!/usr/bin/env python3
"""Compare failure families and unchanged stock-cell geometry, not golden netlists."""
import gzip,hashlib,json,re
from pathlib import Path
import pya
R=Path(__file__).resolve().parents[4];A=R/'designs/g1-guardian/review/audits';P=Path('/foss/pdks/ihp-sg13g2')
current=A/'p01-full-io-normalized-20260921';baseline=R/'designs/g1-guardian/blocks/g1_padring/reports/run-1200/lvs_klayout_deep/xref_summary.txt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def statuses(path):
    rows={}
    for line in path.read_text().splitlines():
        m=re.match(r'^(NOMATCH|MISMATCH|Skipped|Match)\s+(\S+) \|',line)
        if m:rows.setdefault(m[1],[]).append(m[2])
    return rows
old=statuses(baseline);new=statuses(current/'xref.txt');stock=pya.Layout();stock.read(str(P/'libs.ref/sg13g2_io/gds/sg13g2_io.gds'))
candidate=pya.Layout();candidate.read(str(R/'build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds'))
cdl=(P/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl').read_text();cells=[]
for name in sorted(new['NOMATCH']+new['MISMATCH']):
    left,right=stock.cell(name),candidate.cell(name);changes=[]
    for layer,datatype in sorted({(i.layer,i.datatype) for layout in (stock,candidate) for i in layout.layer_infos()}):
        info=pya.LayerInfo(layer,datatype)
        a=pya.Region(left.begin_shapes_rec(stock.layer(info))).merged();b=pya.Region(right.begin_shapes_rec(candidate.layer(info))).merged()
        if not (a^b).is_empty():changes.append(str(info))
    cells.append({'name':name,'unchanged_merged_polygon_geometry':not changes,'changed_layers':changes,'stock_cdl_subckt_present':bool(re.search(r'^\.SUBCKT\s+'+re.escape(name)+r'\b',cdl,re.M|re.I))})
manifest=json.loads((current/'manifest.json').read_text());archive=current/manifest['lvsdb_archive']['gzip'];h=hashlib.sha256()
with gzip.open(archive,'rb') as source:
    while chunk:=source.read(1024*1024):h.update(chunk)
assert h.hexdigest()==manifest['lvsdb_archive']['raw_sha256']
result={'scope':'Stock failure-family comparison and raw geometry identity, not a top-level LVS pass','source_baseline':str(baseline.relative_to(R)),'baseline_sha256':sha(baseline),'candidate_xref_sha256':sha(current/'xref.txt'),'pdk_commit':(P/'COMMIT').read_text().strip(),'script_sha256':sha(Path(__file__)),'counts':{k:len(v) for k,v in new.items()},'prior_io_NOMATCH':old['NOMATCH'],'current_io_NOMATCH':new['NOMATCH'],'new_NOMATCH_names':sorted(set(new['NOMATCH'])-set(old['NOMATCH'])),'prior_missing_reference_cells':old['MISMATCH'],'current_missing_reference_cells':new['MISMATCH'],'stock_cell_geometry':cells,'lvsdb_gzip_identity':'passed','decompressed_sha256':h.hexdigest(),'added_dummy_lvs_status':'not verified: input-pad and top comparisons skipped; stock unconditional purge removes electrically shorted MOS devices','whole_chip_lvs':'failed'}
(current/'baseline_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'counts':result['counts'],'new_NOMATCH_names':result['new_NOMATCH_names'],'unchanged_stock_cells':sum(c['unchanged_merged_polygon_geometry'] for c in cells),'archive_identity':result['lvsdb_gzip_identity']},indent=2))
