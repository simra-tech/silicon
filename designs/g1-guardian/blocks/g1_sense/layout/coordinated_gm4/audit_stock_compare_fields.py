#!/usr/bin/env python3
"""Inspect the actual saved stock MOS classes; do not modify any compare settings."""
import argparse,hashlib,json,os
from pathlib import Path
import pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    summary=json.loads((a.stock/'summary.json').read_text());pdk=Path('/foss/pdks/ihp-sg13g2');rows=[]
    for path in sorted(a.stock.rglob('*.lvsdb')):
        db=pya.LayoutVsSchematic();db.read(str(path));classes=[];unused=[]
        used_kind='sg13_hv_nmos' if path.parent.name=='bias_n2-lvs' else 'sg13_hv_pmos'
        for cls in db.netlist().each_device_class():
            if cls.name not in ('sg13_hv_nmos','sg13_hv_pmos'):continue
            defs=[dict(name=q.name,primary=q.is_primary) for q in cls.parameter_definitions()]
            fields={q['name']:q['primary'] for q in defs}
            if cls.name!=used_kind:
                unused.append(dict(name=cls.name,parameters=defs,scope='Registered but unused primitive class; rfmode may not be added'))
                continue
            assert fields=={'L':True,'W':True,'AS':False,'AD':False,'PS':False,'PD':False,'rfmode':True}
            classes.append(dict(name=cls.name,parameters=defs,ng_present=False))
        assert classes;rows.append(dict(database=str(path.relative_to(a.stock)),sha256=sha(path),classes=classes,unused_registered_classes=unused))
    excerpts=[]
    for name,lo,hi in [('rule_decks/mos_extraction.lvs',35,74),('rule_decks/custom_reader.lvs',375,382),('rule_decks/custom_writer.lvs',101,121),('sg13g2.lvs',447,457)]:
        path=pdk/'libs.tech/klayout/tech/lvs'/name;rel=str(path.relative_to(pdk));assert sha(path)==summary['stock_hashes'][rel]
        lines=path.read_text().splitlines();excerpts.append(dict(path=rel,sha256=sha(path),first_line=lo,last_line=hi,text='\n'.join(lines[lo-1:hi])))
    result={'status':'passed actual class-field inspection; junction/ng not certified by strict stock Match','script_sha256':sha(Path(__file__)),
            'stock_summary_sha256':sha(a.stock/'summary.json'),'databases':rows,'stock_deck_excerpts':excerpts,
            'primary_comparison_fields':['L','W','rfmode'],'nonprimary_fields':['AS','AD','PS','PD'],'absent_field':'ng',
            'scope':'Inspection only, no comparator/card/deck mutation. Stock mos4 extraction and standard simplify flow precede the writer, which prints stored parameter values. Observed A/P symmetrization already exists in saved database/text; this inspection does not isolate the internal extraction-versus-combination step causing it.'}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'databases':len(rows)},indent=2))
if __name__=='__main__':main()
