#!/usr/bin/env python3
"""Exact native one-MIM A/B geometry and Magic type import; never extract."""
import argparse,copy,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
import pya

ROOT=Path('/work')
HELP=ROOT/'designs/g1-guardian/review/audits/sense_power_interface'
sys.path.insert(0,str(HELP))
from screen_sense_dual_gate_proposal import GM4,graph,regions,sha,inside_point
from build_sense_dual_gate import snapshot
SOURCE='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
GDS='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
BUFFER='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500'

def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def box(b):return [b.left,b.bottom,b.right,b.top]
def material(cell,pair):
    r=pya.Region()
    for q in pya.Region(cell.begin_shapes_rec(cell.layout().layer(*pair))).each():r.insert(pya.Polygon(q))
    return r.merged()
def records(r):
    return [dict(hull_dbu=[[q.x,q.y]for q in p.each_point_hull()],
                 holes_dbu=[[[q.x,q.y]for q in p.each_point_hole(i)]for i in range(p.holes())])for p in r.each()]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={1}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running native/type preparation only',source_sha256=SOURCE,GDS_sha256=GDS,
        buffer_sha256=BUFFER,script_sha256=sha(Path(__file__)),views=[],
        not_run=['Field extraction','AC','Backend adoption','Model composition','MOS/BN reference plane'])
    start=time.monotonic()
    try:
        source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
        gds=GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
        ref=GM4/'ring-r8-evidence-20260922-r1/sense-ring-reference-20260922-r8a/manifest.json'
        buf=GM4/'source-faithful-buffer-20260922-r2/g1_ota_source_faithful.gds'
        assert sha(source)==SOURCE and sha(gds)==GDS and sha(buf)==BUFFER
        assert source.read_text().count('XCC cz out cap_cmim w=23u l=23u m=1 mm_ok=1')==1
        result['reference_sha256']=sha(ref)
        ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_sense_physical');full=snapshot(top)
        native=regions(top);hold=graph(native,copy.deepcopy(json.loads(ref.read_text())['terminal_audit']['probes']))
        net,layers,expected,audit=hold[1:];assert audit['status']=='passed' and audit['source_net_count']==134
        result['source_graph']=audit;names={next(iter(v)):k for k,v in expected.items()}
        bl=pya.Layout();bl.read(str(buf));candidates=[]
        for cell in bl.each_cell():
            plate=material(cell,(36,0))
            if plate.count()!=1 or plate.area()!=529000000:continue
            if any(not material(cell,(l,0)).is_empty() for l in (1,5,128)):continue
            if cell.bbox().width()>35000 or cell.bbox().height()>35000:continue
            candidates.append(cell)
        result['native_candidates']=[dict(name=c.name,bbox=box(c.bbox()))for c in candidates]
        assert len(candidates)==1,'Native primitive hierarchy is ambiguous'
        cap=candidates[0];primitive=snapshot(cap);plate=primitive[36,0];b=plate.bbox()
        trans=pya.Trans(43910-b.left,198200-b.bottom)
        moved={k:r.transformed(trans)for k,r in primitive.items()}
        assert box(moved[36,0].bbox())==[43910,198200,66910,221200]
        drawing={k:r for k,r in moved.items() if k[1]==0 and not r.is_empty()}
        assert set(drawing)<={(36,0),(129,0),(67,0),(126,0)},set(drawing)
        result['native_subset']={str(k):dict(area_dbu2=r.area(),outside_source_dbu2=(r-full.get(k,pya.Region())).area())for k,r in drawing.items()}
        assert all((r-full.get(k,pya.Region())).is_empty() for k,r in drawing.items())
        cuts=drawing[129,0];assert cuts.count()==324
        assert all(p.bbox().width()==420 and p.bbox().height()==420 for p in cuts.each())
        assert (cuts-drawing[126,0]).is_empty() and (drawing[36,0]-drawing[67,0]).is_empty()
        for layer,label in [(126,'XBUF/cz'),(67,'vped')]:
            for q in drawing[layer,0].each():
                found=net.probe_net(layers[layer],inside_point(q));assert found is not None and names[found.cluster_id]==label
        # Explicit support/type coverage: native cap1 not shielded by its TOP TM1.
        exposed=(drawing[36,0]-drawing[126,0]).merged()
        result.update(native_cell=cap.name,translation_dbu=[trans.disp.x,trans.disp.y],Vmim_count=cuts.count(),
            intrinsic_area_um2=529,intrinsic_perimeter_um=92,native_plate_uncovered_by_TM1_dbu2=exposed.area(),
            native_plate_uncovered_by_TM1=records(exposed))
        env=pya.Region()
        for r in drawing.values():env+=r
        nativebox=env.bbox();result['native_bbox_dbu']=box(nativebox)
        # A holds the exact native drawing. B adds only passive routing/witnesses.
        additions={};ledger=[]
        def add(layer,name,bb,role):
            r=pya.Region(pya.Box(*bb));additions.setdefault((layer,0),pya.Region()).insert(r)
            ledger.append(dict(layer=layer,net=name,bbox_dbu=bb,role=role))
        m5=drawing[67,0].bbox();tm1=drawing[126,0].bbox()
        farx=nativebox.right+12000;endx=farx+12000
        # Same-P/N external pair has 12um×2um overlap outside primitive.
        y=(tm1.bottom+tm1.top)//2
        add(126,'P',[tm1.right-1000,y-1000,endx,y+1000],'TOP access and same-pair routing witness')
        add(67,'N',[m5.right-1000,y-1000,endx,y+1000],'BOTTOM access and same-pair routing witness')
        # Two foreign conductors witness actual native plate/access fields.
        cx=(b.left+b.right)//2+trans.disp.x;cy=(b.bottom+b.top)//2+trans.disp.y
        pb=drawing[36,0].bbox()
        add(134,'F_TOP',[pb.left-1000,pb.bottom-1000,pb.right+1000,pb.top+1000],
            'Single connected TM2 witness above entire native TOP including exposed rim; native shielding audited')
        add(10,'F_BOTTOM',[m5.left+1000,m5.bottom+1000,m5.left+9000,m5.bottom+9000],'M2 below native BOTTOM')
        result['additions']=ledger
        result['inverse_B_minus_declared_additions_scope']='Native A union exact declared additions; inverse uses pre-addition snapshot, not naive subtraction of overlapping landing area'
        dump(a.output/'native_shapes.json',{str(k):records(r)for k,r in drawing.items()})
        dump(a.output/'additions.json',ledger)
        pdk=Path('/foss/pdks/ihp-sg13g2');tech=pdk/'libs.tech/magic/ihp-sg13g2-extract.tech'
        assert sha(tech)=='e4c2aca0bd66eadfd31bc95885be46bdc16109fe471fa5953e27afd62763fe09'
        rules=tech.read_text().splitlines()
        result['cap1_rules']=[dict(line=i+1,text=s)for i,s in enumerate(rules)if any(t in s for t in ['mimcap','mimcc','cap1'])]
        result['required_exposed_cap1_TM2_rule_found']=any('default' in s and ('mimcap' in s or 'cap1' in s)and('allm7' in s or 'metal7' in s)for s in rules)
        # Import/type preparation only. There is deliberately no extract command.
        for name in ('A','B'):
            folder=a.output/name;folder.mkdir();out=pya.Layout();out.dbu=.001;cell=out.create_cell('sense_mim_control')
            wanted={k:r.dup()for k,r in drawing.items()}
            if name=='B':
                for k,r in additions.items():wanted[k]=wanted.get(k,pya.Region())+r
            for k,r in wanted.items():cell.shapes(out.layer(*k)).insert(r)
            for layer,label,reg in [(126,'P',drawing[126,0]),(67,'N',drawing[67,0])]:
                pt=inside_point(next(reg.each()));cell.shapes(out.layer(layer,25)).insert(pya.Text(label,pya.Trans(pt)))
            if name=='B':
                for layer,label in [(134,'F_TOP'),(10,'F_BOTTOM')]:
                    pt=inside_point(next(additions[layer,0].each()));cell.shapes(out.layer(layer,25)).insert(pya.Text(label,pya.Trans(pt)))
            path=folder/'native.gds';out.write(str(path));check=pya.Layout();check.read(str(path));saved=check.cell('sense_mim_control')
            for k,r in wanted.items():assert (material(saved,k)^r).is_empty()
            for k,r in drawing.items():assert (r-material(saved,k)).is_empty()
            row=dict(name=name,GDS_sha256=sha(path),native_held=True,drawing_layers={str(k):r.area()for k,r in wanted.items()})
            result['views'].append(row);dump(a.output/'summary.json',result)
            tcl=folder/'import.tcl'
            tcl.write_text('gds read native.gds\nload sense_mim_control\nsave sense_mim_control\nputs "MIM_IMPORT_COMPLETE=1"\nquit -noprompt\n')
            command=['magic','-dnull','-noconsole','-rcfile',str(pdk/'libs.tech/magic/ihp-sg13g2.magicrc'),str(tcl.resolve())]
            proc=subprocess.run(command,cwd=str(folder),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15)
            log=proc.stdout.decode(errors='replace');(folder/'import.log').write_text(log)
            row['import_returncode']=proc.returncode;row['import_log_sha256']=sha(folder/'import.log')
            row['error_lines']=[s for s in log.splitlines()if re.search(r'(?i)\b(error|fatal|invalid command|unknown command)\b',s)]
            assert proc.returncode==0 and not row['error_lines'] and 'MIM_IMPORT_COMPLETE=1' in log
            mag=folder/'sense_mim_control.mag';assert mag.exists();text=mag.read_text()
            row['mag_sha256']=sha(mag);row['imported_types']=re.findall(r'^<< (.*?) >>$',text,re.M)
            assert 'mimcap' in row['imported_types'] or 'mimcapc' in row['imported_types'] or 'mimcc' in row['imported_types']
        assert sha(gds)==GDS and sha(source)==SOURCE and sha(buf)==BUFFER
        result['status']='prepared exact A/B native geometry; field coverage review pending'
        if exposed.area()>0 and not result['required_exposed_cap1_TM2_rule_found']:
            result['status']='failed required exposed TOP-plate field rule coverage; extraction not run'
    except Exception as exc:
        result.update(status='failed native/type preparation',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(a.output/'summary.json',result)
        print(json.dumps({k:v for k,v in result.items()if k not in ('native_plate_uncovered_by_TM1','cap1_rules')},indent=2))

if __name__=='__main__':main()
