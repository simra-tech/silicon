#!/usr/bin/env python3
"""Only ten collector Via1 array/landing rotations; r1 immutable."""
import collections
import json
from pathlib import Path
import argparse
import pya
import build_pilot as old

PARENT=old.ROOT/'build/scratch/bgr-hbt-worstrows-20260922-r1'
class Revision(old.Build):
    def __init__(self,out):
        super().__init__(out);self.rotations=[]
    def via(self,kind,net,x,y):
        if kind!='Via1' or net!='c2':return super().via(kind,net,x,y)
        self.rotations.append(dict(net=net,center_um=[x,y],expected_emitter_side_gap_um=.30))
        for layer in ('M1','M2'):
            self.rect(layer,net,x-.15,y-.36,x+.15,y+.36,'two_cut_landing')
        for dy in (-.21,.21):
            b=old.box(x-.095,y+dy-.095,x+.095,y+dy+.095)
            self.top.shapes(self.layers[kind]).insert(b)
            self.vias.append(dict(layer=kind,net=net,bbox_dbu=[b.left,b.bottom,b.right,b.top]))
    def run(self):
        assert old.sha(Path(old.__file__))=='f4c802ca0cae066d86c12d78f499f42ebce29dfa54e56588c4bbad37a9b78e7a'
        assert old.sha(PARENT/'pilot.gds')=='20990b281b617df935f9fc31071a2369ebdafdc953e5da22a325ddd805ebfc00'
        status=super().run()
        assert len(self.rotations)==10
        previous=json.loads((PARENT/'route_ledger.json').read_text());current=json.loads((self.out/'route_ledger.json').read_text())
        audit=dict(status='failed',rotations=self.rotations,revision_script_sha256=old.sha(Path(__file__)),
                   parent_builder_sha256=old.sha(Path(old.__file__)),parent_GDS_sha256=old.sha(PARENT/'pilot.gds'),
                   candidate_GDS_sha256=old.sha(self.out/'pilot.gds'))
        def difference(key):
            a=collections.Counter(json.dumps(r,sort_keys=True) for r in previous[key])
            b=collections.Counter(json.dumps(r,sort_keys=True) for r in current[key])
            return dict(removed=[json.loads(s) for s,n in (a-b).items() for _ in range(n)],
                        added=[json.loads(s) for s,n in (b-a).items() for _ in range(n)])
        audit['route_delta']=difference('routes');audit['via_delta']=difference('vias')
        assert all(len(audit[k][side])==20 for k in ('route_delta','via_delta') for side in ('removed','added'))
        for side in ('removed','added'):
            assert all(r['net']=='c2' and r['role']=='two_cut_landing' and r['layer'] in ('M1','M2') for r in audit['route_delta'][side])
            assert all(r['net']=='c2' and r['layer']=='Via1' for r in audit['via_delta'][side])
        assert previous['terminals']==current['terminals'] and previous['ports']==current['ports']
        assert (PARENT/'subset.json').read_bytes()==(self.out/'subset.json').read_bytes()
        assert (PARENT/'pilot.cdl').read_bytes()==(self.out/'pilot.cdl').read_bytes()
        layouts=[]
        for path in (PARENT/'pilot.gds',self.out/'pilot.gds'):
            ly=pya.Layout();ly.read(str(path));layouts.append(ly)
        allowed=pya.Region()
        for r in self.rotations:
            x,y=r['center_um'];allowed.insert(old.box(x-.36,y-.36,x+.36,y+.36))
        layerinfos={(ly.get_info(i).layer,ly.get_info(i).datatype) for ly in layouts for i in ly.layer_indices()}
        xors=[];textdiff=[]
        for pair in sorted(layerinfos):
            rr=[];texts=[]
            for ly in layouts:
                li=ly.layer(*pair);cell=ly.top_cell();rr.append(old.materialized(cell,li))
                it=cell.begin_shapes_rec(li);tt=[]
                while not it.at_end():
                    if it.shape().is_text():tt.append(str(it.shape().text.transformed(it.trans())))
                    it.next()
                texts.append(sorted(tt))
            xor=rr[0]^rr[1]
            if not xor.is_empty():
                assert pair in [(8,0),(10,0),(19,0)]
                assert (xor-allowed).is_empty()
                xors.append(dict(layer=list(pair),xor_area_um2=xor.area()*1e-6,polygons=xor.count()))
            if texts[0]!=texts[1]:textdiff.append(list(pair))
        assert not textdiff
        assert {tuple(x['layer']) for x in xors}=={(8,0),(10,0),(19,0)}
        audit.update(status='passed' if status==0 else 'failed',serialized_layer_XOR=xors,text_differences=textdiff,
                     subset_byte_identical=True,CDL_byte_identical=True,all_other_geometry_unchanged=True)
        old.dump(self.out/'revision_audit.json',audit)
        prep=json.loads((self.out/'preparation.json').read_text())
        prep['revision_script_sha256']=old.sha(Path(__file__))
        prep['revision_audit_sha256']=old.sha(self.out/'revision_audit.json')
        prep['revision_scope']='Only10collectorVia1array/landing rotations; serialized GDS XOR confined to exact windows'
        old.dump(self.out/'preparation.json',prep)
        print(json.dumps(audit,indent=2));return status
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert a.output.is_dir() and not (a.output/'pilot.gds').exists()
    try:return Revision(a.output).run()
    except Exception as e:
        old.dump(a.output/'preparation_exception.json',dict(status='failed',type=type(e).__name__,message=str(e)));raise
if __name__=='__main__':raise SystemExit(main())
