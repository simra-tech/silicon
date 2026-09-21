#!/usr/bin/env python3
"""Scratch-only pad-exit / VDD dummy-PMOS candidates; unmodified stock rule checks."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya

ROOT=Path(__file__).resolve().parents[4]
BLOCK=ROOT/'designs/g1-guardian/blocks/g1_padring'
BASE=BLOCK/'layout/g1_chip_top.gds'
PDK=Path('/foss/pdks/ihp-sg13g2')
DRC=PDK/'libs.tech/klayout/tech/drc'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['pad','pad_dummy','pad_outward','pad_outward_dummy','pad_outward_dummy_clean'],required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    if args.work.exists() or args.report.exists():raise FileExistsError('Use new output directories')
    args.work.mkdir(parents=True);args.report.mkdir(parents=True)
    work,report=args.work.resolve(),args.report.resolve()
    l=pya.Layout();l.read(str(BASE));top=l.cell('g1_chip_top')
    audit_path=ROOT/'designs/g1-guardian/review/audits/pad-markers-20260921.json'
    audit=json.loads(audit_path.read_text())
    assert sha(BASE)==audit['gds_sha256']
    added=collections.defaultdict(float)
    moved_pads=[]
    if args.mode.startswith('pad_outward'):
        for inst in list(top.each_inst()):
            if inst.cell.name!='bondpad_70x70_tm1':continue
            center=inst.dbbox().center();dx=dy=0
            if center.x<200:dx=-4
            elif center.x>1150:dx=4
            elif center.y<200:dy=-4
            elif center.y>1150:dy=4
            else:raise ValueError('Unexpected bondpad location')
            old=inst.cplx_trans;translation=pya.Trans(round(dx/l.dbu),round(dy/l.dbu))
            for layer in (126,134):
                region=pya.Region(inst.cell.begin_shapes_rec(l.layer(layer,0))).transformed(old)
                assert not region.is_empty()
                swept=region.bbox()+region.transformed(translation).bbox()
                top.shapes(l.layer(layer,0)).insert(swept)
                added[str(layer)]+=swept.area()*l.dbu**2
            inst.dcplx_trans=pya.DCplxTrans(1,0,False,dx,dy)*inst.dcplx_trans
            moved_pads.append({'original_center_um':[center.x,center.y],'shift_um':[dx,dy],
                               'new_center_um':[center.x+dx,center.y+dy]})
        assert len(moved_pads)==24
    else:
        for marker in audit['pad_items']:
            layer=126 if marker['rule'].endswith('TM1') else 134
            poly=pya.DPolygon([pya.DPoint(*v) for v in marker['polygon_um']]).to_itype(l.dbu)
            top.shapes(l.layer(layer,0)).insert(poly);added[str(layer)]+=poly.area()*l.dbu**2
    dummy=None
    if '_dummy' in args.mode:
        c=l.cell('sg13g2_IOPadIn')
        window=pya.Region(pya.DBox(40.9,161.2,42.65,166.8).to_itype(l.dbu))
        move=pya.Trans(round(-5/l.dbu),0)
        layers={}
        for layer in (1,5,6,14,44):
            region=pya.Region(c.begin_shapes_rec(l.layer(layer,0))).merged()&window
            layers[layer]=region.transformed(move)
        # Contact geometry was clipped below the existing top nwell-tap rail.
        # Only M1 extends to that existing VDD rail; no duplicate tap contacts.
        metal_window=pya.Region(pya.DBox(40.9,161.2,42.65,167.15).to_itype(l.dbu))
        layers[8]=(pya.Region(c.begin_shapes_rec(l.layer(8,0))).merged()&metal_window).transformed(move)
        layers[31]=pya.Region(pya.DBox(35.5,160.95,43.0,167.77).to_itype(l.dbu))
        for layer,region in layers.items():
            for polygon in region.each():c.shapes(l.layer(layer,0)).insert(polygon)
        extra_gate=layers[1]&layers[5]
        assert abs(extra_gate.area()*l.dbu**2-4.65*.45)<1e-8
        dummy={'cell':'sg13g2_IOPadIn','source_window_um':[40.9,161.2,42.65,166.8],
               'translation_um':[-5,0],'metal_window_um':[40.9,161.2,42.65,167.15],
               'nwell_extension_um':[35.5,160.95,43,167.77],
               'extra_gate_area_per_pad_um2':extra_gate.area()*l.dbu**2,
               'topology':'Duplicate existing all-VDD MP0 dummy; functional receiver devices unchanged.',
               'terminal_connectivity':'not run'}
        network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(l,c,[]));conductors={}
        sequence=[('poly',5),('cont',6),('m1',8),('v1',19),('m2',10),('v2',29),('m3',30),('v3',49),('m4',50),('v4',66),('m5',67),('tv1',125),('tm1',126),('tv2',133),('tm2',134)]
        for name,gl in sequence:
            conductors[name]=network.make_layer(l.layer(gl,0),name);network.connect(conductors[name])
            if name in ('m1','m2','m3','m4','m5','tm1','tm2'):
                texts=network.make_text_layer(l.layer(gl,25),name+'_txt');network.connect(conductors[name],texts)
        for a,b in zip(list(conductors),list(conductors)[1:]):network.connect(conductors[a],conductors[b])
        network.extract_netlist();nets={}
        for terminal,layer,x,y in [('gate','poly',36.765,164),('source','m1',36.35,164),('drain','m1',37.18,164),('well_tap_metal','m1',36.0,167.0)]:
            net=network.probe_net(conductors[layer],pya.Point(round(x/l.dbu),round(y/l.dbu)))
            nets[terminal]=net.name if net else None
        assert all(v=='vdd' for v in nets.values()),nets
        dummy['terminal_connectivity']={'status':'passed','method':'Cell-local metal/poly trace at gate/S/D and existing nwell-tap metal; extended nwell overlaps original nwell. Not transistor LVS.','nets':nets}
    fill_cleanup=[]
    if args.mode.endswith('_clean'):
        # Remove only existing datatype-22 dummy fill near the added transistor.
        # Split intersecting fill arrays into retained single instances; never
        # remove device/drawing geometry, and retain every remote fill element.
        local_keepout=pya.DBox(33.5,158.95,40,169.77).to_itype(l.dbu)
        keepouts=[local_keepout.transformed(i.cplx_trans) for i in top.each_inst()
                  if i.cell.name=='sg13g2_IOPadIn']
        assert len(keepouts)==3
        for inst in list(top.each_inst()):
            used=[l.get_info(li) for li in l.layer_indexes() if inst.cell.shapes(li).size()]
            if not used or not all(q.datatype==22 and q.layer in (1,5,8) for q in used):continue
            if not any(inst.bbox().overlaps(k) for k in keepouts):continue
            retained=[];removed=[]
            for transform in inst.cell_inst.each_cplx_trans():
                bbox=inst.cell.bbox().transformed(transform)
                (removed if any(bbox.overlaps(k) for k in keepouts) else retained).append(transform)
            if not removed:continue
            fill_cleanup.append({'cell':inst.cell.name,'layers':[str(q) for q in used],
                                 'removed_bboxes_um':[str(inst.cell.dbbox().transformed(pya.DCplxTrans(t,l.dbu))) for t in removed],
                                 'removed_elements':len(removed),'retained_elements':len(retained)})
            index=inst.cell_index
            inst.delete()
            for transform in retained:top.insert(pya.CellInstArray(index,transform))
        assert fill_cleanup
    candidate=work/'g1_chip_top.gds';l.write(str(candidate))
    manifest={'mode':args.mode,'scope':'NON-PRODUCTION DIAGNOSTIC; delivered GDS and PDK untouched',
              'command':'flow/run.sh python3 designs/g1-guardian/review/audits/geometry_candidates.py --mode '+args.mode+' --work '+str(args.work)+' --report '+str(args.report),
              'base_sha256':sha(BASE),'candidate_sha256':sha(candidate),'script_sha256':sha(Path(__file__)),
              'pdk_commit':(PDK/'COMMIT').read_text().strip(),'klayout_version':pya.__version__,
              'pad_marker_sha256':sha(audit_path),'pad_drawn_patch_area_um2_by_layer':dict(added),'moved_bondpads':moved_pads,'dummy':dummy,'fill_cleanup':fill_cleanup,'checks':[],
              'not_run':['Full IO-inclusive LVS','Core LVS','PEX and electrical startup',*([] if args.mode.endswith('_clean') else ['Density rerun']),'Production adoption']}
    (report/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (report/'generator.py').write_bytes(Path(__file__).read_bytes())
    # Sequential: at most two deck threads; each process has an explicit watchdog.
    for name,deck,options in [
        ('drc_recommended',DRC/'ihp-sg13g2.drc',['-rd','run_mode=deep']),
        ('antenna',DRC/'rule_decks/antenna.drc',[]),
        *([('density',DRC/'rule_decks/density.drc',[])] if args.mode.endswith('_clean') else []),
    ]:
        rpt=report/(name+'.lyrdb');log=report/(name+'.log')
        cmd=['klayout','-b','-zz','-r',str(deck),'-rd','input='+str(candidate),'-rd','topcell=g1_chip_top',
             '-rd','report='+str(rpt),'-rd','threads=2']+options
        start=time.monotonic();timed_out=False
        with log.open('w') as stream:
            try: proc=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=600);code=proc.returncode
            except subprocess.TimeoutExpired:code=None;timed_out=True
        record={'name':name,'command':cmd,'exit_code':code,'timed_out':timed_out,'wall_seconds':time.monotonic()-start,
                'deck_sha256':sha(deck),'status':'not run' if timed_out else 'failed'}
        if code==0 and rpt.exists():
            cats=collections.Counter(i.findtext('category').strip("'") for i in ET.parse(rpt).findall('.//items/item'))
            record.update(markers=sum(cats.values()),categories=dict(cats),status='failed' if cats else 'passed')
            if name=='drc_recommended':
                record['hard_rule_status']='failed' if any(not k.startswith('Pad.fR_') for k in cats) else 'passed'
                record['recommended_pad_status']='failed' if any(k.startswith('Pad.fR_') for k in cats) else 'passed'
        manifest['checks'].append(record)
        (report/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(record),flush=True)


if __name__=='__main__':main()
