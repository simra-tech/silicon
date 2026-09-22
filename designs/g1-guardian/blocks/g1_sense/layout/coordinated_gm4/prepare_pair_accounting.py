#!/usr/bin/env python3
"""Prospective split-chain ABBA accounting only; no saved geometry or electrical pass."""
import argparse,hashlib,json
from pathlib import Path
from audit_junction_defaults import default

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--pack',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();inv=json.loads(a.inventory.read_text());pack=json.loads(a.pack.read_text())
    rows={r['device']:r for r in inv['devices']};result=[]
    for view in ('g1_ota','g1_ota_main_candidate'):
        q=rows['XM1']['source_comparisons'][view]['source']['params'];ng=int(q['ng']);w=float(q['w'].rstrip('u'));l=float(q['l'].rstrip('u'));f=w/ng
        assert ng in (16,64) and f==6 and l==2
        active_width=ng*(l+.38)+.30
        if view=='g1_ota':
            # 2.4um Activ gap permits one L2 dummy with0.2um clearance on both sides.
            origins=[(0,0),(active_width+2.4,0)]
        else:
            # Reuse exact r4 native bbox reservations; PCell Activ origin is bbox+.62.
            bbox=[next(r['bbox_um'] for r in pack['main_OTA_devices'] if r['name']==name) for name in ('XM1','XM2')]
            origins=[(b[0]+.62,b[1]+.62) for b in bbox]
        gates=[];strips=[];allocated={n:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for n in ('A','B')}
        for chain,(x,y) in enumerate(origins):
            groups=('ABBA' if chain==0 else 'BAAB')*(ng//8)
            owners=[groups[k//2] for k in range(ng)]
            for k,owner in enumerate(owners):gates.append(dict(chain=chain,finger=k,owner=owner,center_um=[x+.34+l/2+k*(l+.38),y+f/2]))
            for k in range(ng+1):
                width=.34 if k in (0,ng) else .38
                area=f*width;perimeter=2*(f+width)
                if k%2:
                    assert owners[k-1]==owners[k]
                    weights={owners[k]:1.};kind='drain'
                else:
                    adjacent=owners[max(0,k-1):min(ng,k+1)]
                    weights={n:adjacent.count(n)/len(adjacent) for n in ('A','B') if n in adjacent};kind='source'
                for name,weight in weights.items():
                    allocated[name]['as_um2' if kind=='source' else 'ad_um2']+=area*weight
                    allocated[name]['ps_um' if kind=='source' else 'pd_um']+=perimeter*weight
                strips.append(dict(chain=chain,strip=k,kind=kind,physical_area_um2=area,physical_perimeter_um=perimeter,adjacent_gate_allocation=weights))
        centroids={name:[sum(g['center_um'][i] for g in gates if g['owner']==name)/ng for i in (0,1)] for name in ('A','B')}
        expected=default(w,ng)
        assert all(sum(g['owner']==name for g in gates)==ng for name in ('A','B'))
        assert all(abs(centroids['A'][i]-centroids['B'][i])<1e-9 for i in (0,1))
        assert all(abs(allocated[n][key]-expected[key])<1e-8 for n in ('A','B') for key in expected)
        assert all(abs(sum(r['adjacent_gate_allocation'].values())-1)<1e-12 for r in strips)
        result.append(dict(view=view,chains=2,native_chain_parameters=dict(w_um=w,l_um=l,ng=ng),Activ_origins_um=origins,
                           gates=gates,diffusion_strips=strips,logical_centroids_um=centroids,source_default_per_logical=expected,
                           adjacent_gate_allocated_junction_per_logical=allocated,status='passed prospective arithmetic only'))
    specs={name:rows[name]['source_comparisons']['g1_ota']['source']['params'] for name in rows}
    groups=[['XMB4','XMB2','XMB6','XM3','XM13','XM16','XM4','XM21'],['XM14','XM15','XM12','XM11'],['XMB7','XMB5','XMB3','XMT','XM20']]
    widths=[sum(int(specs[n]['ng'])*(float(specs[n]['l'].rstrip('u'))+.38)+.3 for n in group)+1.4*(len(group)-1) for group in groups]
    pairwidth=2*(16*2.38+.3)+2.4
    active=max(widths+[pairwidth]);oldactive=inv['generator_polygon_reproduction']['boundary_um'][2]-9.5-.6
    buffer_width=97.85+(active-oldactive)
    final={'status':'passed prospective centroid/adjacent-gate junction arithmetic; physical/model applicability not run',
           'script_sha256':sha(Path(__file__)),'inventory_sha256':sha(a.inventory),'pack_sha256':sha(a.pack),'source_sha256':inv['source_sha256'],
           'pair_options':result,'buffer_row_Activ_widths_um':widths,'buffer_pair_Activ_width_um':pairwidth,'prospective_buffer_width_um':buffer_width,
           'source_unchanged':True,'GDS_saved':False,
           'allocation_scope':'Each physical shared source strip is counted once globally and divided equally between adjacent channel owners. This is a prospective consistent model-assignment convention, not intrinsic ownership of shared diffusion or an extraction/PCell qualification. Each logical input retains exact W/L/ng; both gate centroids coincide. Nominal-node total A/P matches independently of allocation.',
           'not_run':['actual contact/dummy/well/guard geometry','stock DRC/LVS','independent physical source-model allocation applicability including mismatch','routed macro fit','electrical matching/extracted performance']}
    a.output.write_text(json.dumps(final,indent=2)+'\n');print(json.dumps({k:v for k,v in final.items() if k!='pair_options'},indent=2))
if __name__=='__main__':main()
