#!/usr/bin/env python3
"""Candidate-only stock-LVS text scope normalization, with instance-local clones."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

SHA='5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684'
TOP='placed_core_NOT_CONNECTED_FULLCHIP'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--gds',type=Path,required=True)
    ap.add_argument('--proof',type=Path,required=True)
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--paths',type=Path,required=True)
    ap.add_argument('--ports',type=Path,required=True)
    ap.add_argument('--reach',type=Path,required=True)
    ap.add_argument('--input-record-proof',type=Path);a=ap.parse_args()
    input_sha=sha(a.input)
    if input_sha!=SHA:
        assert a.input_record_proof is not None
        record=json.loads(a.input_record_proof.read_text())
        assert record['status']=='passed exact GDS record identity except timestamp payloads'
        assert record['reference_gds_sha256']==SHA and record['reproduced_gds_sha256']==input_sha
        assert record['all_nondate_records_byte_exact'] and record['other_record_differences']==0
    assert not a.gds.exists() and not a.proof.exists()
    mapped=json.loads(a.paths.read_text());rows=mapped['rows']
    assert len(rows)==86 and len({n for r in rows for n in r['pins']})==81
    ext=json.loads(a.ports.read_text());external=sorted(json.loads(a.reach.read_text())['expected_external'])
    assert len(external)==22 and ext['all_external_label_sites_on_conductor']
    centers={}
    for r in ext['rows']:
        if r['label'] not in external:continue
        assert r['on_stock_TM2_conductor'] and r['raw_layer_overlaps']['(134, 2)']
        centers.setdefault(r['label'],r['xy'])
    ly=pya.Layout();ly.read(str(a.input));assert abs(ly.dbu-.001)<1e-12
    top=ly.cell(TOP);assert top
    trie={'children':{},'texts':[]}
    for r in rows:
        node=trie
        for e in r['path']:
            node=node['children'].setdefault(e['inst_index'],{'children':{},'texts':[],'expected':e})
            assert node['expected']==e
        node['texts'].append(r)
    clone_log=[];erase_log=[]
    def clone(src,node):
        dst=ly.create_cell(f'__rz_port_text_{len(clone_log):03d}_{src.name}')
        assert dst and dst.cell_index()!=src.cell_index()
        dst.copy_shapes(src);dst.copy_instances(src)
        if src.properties():dst.set_properties(src.properties())
        orig_inst=list(src.each_inst());new_inst=list(dst.each_inst())
        assert len(orig_inst)==len(new_inst)
        for idx,ch in sorted(node['children'].items()):
            oi=orig_inst[idx];ni=new_inst[idx];exp=ch['expected']
            assert src.name==exp['parent'] and oi.cell.name==exp['child']
            assert exp['ia']==-1 and exp['ib']==-1
            child=clone(oi.cell,ch)
            cia=ni.cell_inst.dup();cia.cell_index=child.cell_index();ni.cell_inst=cia
        for r in node['texts']:
            layer=ly.layer(pya.LayerInfo(*r['key'][1]));target=r['local_xy'];found=[]
            for s in dst.shapes(layer).each():
                if s.is_text() and s.text.string==r['local_text']:
                    p=s.text.trans.disp
                    if [p.x,p.y]==target:found.append(s)
            assert len(found)==1,(src.name,r['key'],len(found))
            dst.shapes(layer).erase(found[0]);erase_log.append(dict(cell=dst.name,source=src.name,
                         text=r['local_text'],local_xy=target,layer=r['key'][1],global_xy=r['key'][2],pins=r['pins']))
        clone_log.append(dict(source=src.name,clone=dst.name,original_instances=len(orig_inst),
                              child_redirects=len(node['children']),text_deletions=len(node['texts'])))
        return dst
    top_inst=list(top.each_inst())
    for idx,node in sorted(trie['children'].items()):
        oi=top_inst[idx];assert oi.cell.name==node['expected']['child']
        child=clone(oi.cell,node)
        cia=oi.cell_inst.dup();cia.cell_index=child.cell_index();oi.cell_inst=cia
    assert len(erase_log)==86
    li=ly.layer(pya.LayerInfo(134,25))
    for name,xy in sorted(centers.items()):
        top.shapes(li).insert(pya.Text(name,pya.Trans(pya.Point(*xy))))
    clean=pya.Layout();clean.dbu=ly.dbu;clean_top=clean.create_cell(TOP);clean_top.copy_tree(top)
    assert [c.name for c in clean.top_cells()]==[TOP]
    a.gds.parent.mkdir(parents=True,exist_ok=True);clean.write(str(a.gds))
    proof=dict(status='candidate text-only transformation; stock LVS not yet run',
               input_gds_sha256=input_sha,output_gds_sha256=sha(a.gds),paths_sha256=sha(a.paths),
               port_overlap_sha256=sha(a.ports),root_external_labels=centers,
               target_synthetic_pins=81,text_occurrences_removed=erase_log,
               clones=clone_log,nontext_operation_count=0,
               note='Original cells remain byte-for-byte unedited; clones copy all shapes and instances, delete only mapped text, and redirect selected instances.')
    a.proof.parent.mkdir(parents=True,exist_ok=True);a.proof.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(output_gds_sha256=proof['output_gds_sha256'],clones=len(clone_log),
                          text_deleted=len(erase_log),root_labels=len(centers))))
if __name__=='__main__':main()
