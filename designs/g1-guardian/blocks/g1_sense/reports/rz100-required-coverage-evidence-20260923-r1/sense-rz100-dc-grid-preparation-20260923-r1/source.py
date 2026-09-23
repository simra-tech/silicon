#!/usr/bin/env python3
"""Original standalone V06 fixture, source-only R100 replacement and observers."""
import argparse,collections,hashlib,itertools,json,re
from pathlib import Path
from expose_comp45_internal_nodes import parse,flatten

SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
HISTORICAL='8880157bd2a88c92a248c4865fc79b9242954d1920ce6e3834b776cae6eee57f'
SIM=Path(__file__).resolve().parent
REFERENCE=SIM/'qualification/corners-20260921-a'
PREPARATION=SIM.parents[1]/'g1_trip/sim/qualification/joint586-mm-tranqual-20260922-a-enabled/preparation.json'
VECTORS=['v(isense)','v(vped)','v(vref_buf)','v(xdut.vp)','v(xdut.vn)','v(xdut.vped_ref)','i(vdd)','v(shp)','v(cm)']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def cases():
    return [(f'{m}_{r}_{v}V_{t}C',(m,r,v,t)) for m,r,v,t in itertools.product(['tt','ss','ff'],['typ','bcs','wcs'],[3.0,3.3,3.6],[-40,27,85,125])]
def queries():
    q=json.loads(PREPARATION.read_text())['groups']['NON_BGR']
    answer=[s.replace('.xs.','.xdut.') for s in q if '.xs.' in s]
    assert len(answer)==len(set(answer))==529
    return answer
def source_inventory(source):
    assert hashlib.sha256(source.encode()).hexdigest()==SOURCE
    cells=parse(source);rows=flatten(cells)
    assert collections.Counter(r['model'] for r in rows)=={'rppd':98,'cap_cmim':3,'sg13_hv_nmos':25,'sg13_hv_pmos':33}
    assert len(cells['g1_sense']['ports'])==9 and len({n for r in rows for n in r['nodes']})==134
    return rows
def observe(q,when):
    return 'echo SENSE_'+when+'_BEGIN\n'+''.join('print '+x+'\n' for x in q)+'echo SENSE_'+when+'_END\n'
def make_deck(original,source_path,q,reverse=False):
    old='.include qualification/corners-20260921-a/sense_substrate_tied.spice'
    new='.include '+str(source_path);assert original.count(old)==1
    text=original.replace(old,new)
    pattern=r'alter Vcm dc=([^\n]+)\nalter Vsh dc=([^\n]+)\nop\necho ROW ([^\n]+)\n'
    matches=list(re.finditer(pattern,text));assert len(matches)==9
    points=[];blocks=[]
    for match in matches:
        cm,sh=float(match[1]),float(match[2]);label=match[3].split()[0]
        true_cm=cm+sh/2
        assert min(abs(true_cm-t) for t in [-.1,0,.3])<1e-15 and sh in [0,.025,.05]
        points.append(dict(label=label,true_cm_V=true_cm,shunt_V=sh,negative_V=cm,positive_V=cm+sh));blocks.append(match[0])
    assert len({(round(x['true_cm_V'],8),x['shunt_V']) for x in points})==9
    assert all(matches[i].end()==matches[i+1].start() for i in range(8))
    prefix=text[:matches[0].start()];suffix=text[matches[-1].end():]
    order=list(range(9));order=order[::-1] if reverse else order;order+=[order[0]]
    made=[]
    for position,index in enumerate(order):
        block=blocks[index]
        extra='set numdgt=17\necho DC_ROW_'+str(position)+'_BEGIN\nprint '+' '.join(VECTORS)+'\necho DC_ROW_'+str(position)+'_END\n'
        if position==0:extra+=observe(q,'BEFORE')
        if position==9:extra+=observe(q,'AFTER')
        made.append(block+extra)
    # Stripping observations and the declared return OP recovers exactly the
    # original nine blocks (after reversing when requested), with only include.
    recovered=''.join(blocks[i] for i in sorted(order[:-1]))
    assert (prefix+recovered+suffix).replace(new,old)==original
    return prefix+''.join(made)+suffix,dict(points=points,order=order,include_inverse_exact=True,original_blocks_exact=True,added_return_OP=True,queries=q,vectors=VECTORS)
def controls():
    text=(REFERENCE/'tt_typ_3.3V_27C.cir').read_text();q=queries()
    for reverse in [False,True]:
        made,proof=make_deck(text,Path('/control/candidate.spice'),q,reverse)
        assert len(proof['order'])==10 and proof['order'][0]==proof['order'][-1]
    broken=text.replace('alter Vcm dc=-0.1125','alter Vcm dc=-0.1')
    try:make_deck(broken,Path('/control/candidate.spice'),q)
    except AssertionError:pass
    else:raise AssertionError('wrong true common mode accepted')
    try:make_deck(text.replace('alter Vsh dc=0.025','alter Vsh dc=0.024'),Path('/control/candidate.spice'),q)
    except AssertionError:pass
    else:raise AssertionError('wrong endpoint accepted')
    assert len(cases())==108
    return dict(status='passed',controls=['108 unique tuples','529 unique source queries','forward/reverse/return inverse','wrong CM rejected','wrong shunt rejected'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    tested=controls();assert sha(REFERENCE/'sense_substrate_tied.spice')==HISTORICAL
    inventory=source_inventory(a.candidate.read_text());q=queries();records=[]
    for name,values in cases():
        deck=REFERENCE/(name+'.cir');run=json.loads((REFERENCE/(name+'.json')).read_text());assert sha(deck)==run['deck_sha256'] and run['status']=='completed' and run['returncode']==0
        records.append(dict(case=name,corner=values,original_deck_sha256=sha(deck),original_run_sha256=sha(REFERENCE/(name+'.json'))))
    result=dict(status='prepared only; historical/source/return runtime controls not run',controls=tested,
        candidate_source_sha256=SOURCE,historical_source_sha256=HISTORICAL,source_inventory=inventory,queries=q,
        original_provenance_sha256=sha(REFERENCE/'provenance.json'),query_preparation_sha256=sha(PREPARATION),cases=records,
        scope='Original V06 standalone idealVREF/PTAT/passiveTRIP fixture. Not actualBGR/fullTRIP, no11512 claim, no population/PEX or source adoption.',
        criteria=dict(gain_min=19.9,gain_max=20.1,within_source_control_V=1e-6,within_source_control_A=1e-9,offset_acceptance='separate calibration requirement; report only here'),
        unrun=['historical nominal exact printed-row replay','candidate forward/repeat/reverse and 529-query stability','108 candidate tuples'],
        inherited_solver_options='All original .option/.nodeset/model libraries retained. Only source include, output observations and explicit return OP differ.')
    a.output.mkdir(parents=True);(a.output/'candidate.spice').write_bytes(a.candidate.read_bytes());(a.output/'source.py').write_bytes(Path(__file__).read_bytes());(a.output/'contract.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(records),source_primitives=len(inventory),queries=len(q))))
if __name__=='__main__':main()
