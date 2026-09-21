#!/usr/bin/env python3
"""Full IO LVS after geometry-preserving std-cell alias normalization.

Optional global-substrate reference normalization preserves all device and
parameter statements; it is recorded as an explicit reference-view hypothesis.
No implicit physical connections, rule changes or ignored ports are used.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
import pya

ROOT=Path(__file__).resolve().parents[4];B=ROOT/'designs/g1-guardian/blocks/g1_padring';PDK=Path('/foss/pdks/ihp-sg13g2')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--global-substrate',action='store_true');p.add_argument('--work',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
if a.work.exists() or a.report.exists():raise FileExistsError('Preserve earlier runs')
a.work.mkdir(parents=True);a.report.mkdir(parents=True);work,report=a.work.resolve(),a.report.resolve()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
original=pya.Layout();original.read(str(a.candidate));layout=pya.Layout();layout.read(str(a.candidate))
def equal_cells(left,right):
    if left.bbox()!=right.bbox() or left.child_instances()!=right.child_instances():return False
    for li in layout.layer_indexes():
        if not (pya.Region(left.begin_shapes_rec(li))^pya.Region(right.begin_shapes_rec(li))).is_empty():return False
        def texts(cell):return {(s.text_string,s.text_trans.to_s()) for s in cell.shapes(li).each() if s.is_text()}
        if texts(left)!=texts(right):return False
    return True
folded=[];renamed=[];different=[]
for cell in list(layout.each_cell()):
    match=re.match(r'(sg13g2_\w+?)\$\d+$',cell.name)
    if not match:continue
    base=layout.cell(match[1])
    if base is None:
        renamed.append([cell.name,match[1]]);cell.name=match[1];continue
    if not equal_cells(cell,base):different.append(cell.name);continue
    name=cell.name;count=0
    for parent_index in list(cell.each_parent_cell()):
        parent=layout.cell(parent_index)
        for inst in list(parent.each_inst()):
            if inst.cell_index!=cell.cell_index():continue
            item=inst.cell_inst;item.cell_index=base.cell_index();parent.replace(inst,item);count+=1
    layout.delete_cell(cell.cell_index());folded.append({'alias':name,'base':base.name,'instances':count})
assert not different, different
normalized=work/'g1_chip_top_normalized.gds';layout.write(str(normalized))
changed=[]
for li in original.layer_indexes():
    info=original.get_info(li);left=pya.Region(original.cell('g1_chip_top').begin_shapes_rec(li)).merged()
    right=pya.Region(layout.cell('g1_chip_top').begin_shapes_rec(layout.layer(info))).merged()
    delta=left^right
    if not delta.is_empty():changed.append({'layer':str(info),'area_um2':delta.area()*layout.dbu**2})
assert not changed,changed
reference=work/'g1_chip_top_reference.cdl';txt=a.reference.read_text()
if a.global_substrate:txt='* Reference-view normalization: global substrate, unchanged device statements\n.GLOBAL sub!\n'+txt
reference.write_text(txt)
state={'scope':'Exact candidate geometry; normalized cell aliases; full IO-inclusive strict comparison',
       'candidate_sha256':sha(a.candidate),'normalized_gds_sha256':sha(normalized),'source_reference_sha256':sha(a.reference),'normalized_reference_sha256':sha(reference),
       'source_reference':str(a.reference),'global_substrate_declaration':a.global_substrate,'folded_aliases':folded,'renamed_aliases':renamed,
       'all_layer_polygon_xor':'passed','changed_polygon_layers':changed,'text_comparison':'Per-cell texts checked before folding; no text edits',
       'pdk_commit':(PDK/'COMMIT').read_text().strip(),'klayout_version':pya.__version__,'script_sha256':sha(Path(__file__)),
       'checks':[{'name':'full_io_lvs','status':'not run','reason':'In progress; comparison not complete'}]}
def save():(report/'manifest.json').write_text(json.dumps(state,indent=2)+'\n')
save();shutil.copyfile(Path(__file__),report/'runner.py')
cmd=['python3',str(PDK/'libs.tech/klayout/tech/lvs/run_lvs.py'),'--layout',str(normalized),'--netlist',str(reference),'--topcell','g1_chip_top','--run_mode','deep','--run_dir',str(report/'lvs'),'--top_lvl_pins','--spice_comments']
os.environ['KLAYOUT_PATH']=str(PDK/'libs.tech/klayout');start=time.monotonic();timed_out=False
with (report/'console.log').open('w') as output:
    proc=subprocess.Popen(cmd,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    try:code=proc.wait(timeout=3600)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
        try:code=proc.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
console=(report/'console.log').read_text()
state['checks']=[{'name':'full_io_lvs','status':'not run' if timed_out else ('passed' if code==0 and 'Comparison mode: PASS (netlists match).' in console else 'failed'),
                  'command':cmd,'exit_code':code,'timed_out':timed_out,'wall_seconds':time.monotonic()-start}];save()
for db in (report/'lvs').glob('*.lvsdb'):
    with (report/'xref.txt').open('w') as output:subprocess.run(['klayout','-b','-rd','db='+str(db),'-r',str(B/'flow/lvs/xref_summary.py')],stdout=output,stderr=subprocess.STDOUT,timeout=120)
    dest=db.with_suffix(db.suffix+'.gz')
    with db.open('rb') as source,gzip.open(dest,'wb') as output:shutil.copyfileobj(source,output)
    raw=work/db.name;shutil.move(db,raw)
    state['lvsdb_archive']={'raw':str(raw),'raw_sha256':sha(raw),'gzip':str(dest.relative_to(report)),'gzip_sha256':sha(dest)};save()
print(json.dumps(state['checks'],indent=2))
