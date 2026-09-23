#!/usr/bin/env python3
"""One bounded original-fixture DC tuple/control, source-held R100."""
import argparse,json,math,os,re,subprocess
from pathlib import Path
from prepare_rz100_dc_grid import SOURCE,HISTORICAL,SIM,REFERENCE,VECTORS,sha,make_deck,source_inventory,controls
from run_loaded_followthrough import errors
from run_loaded_noise_audit import MANIFEST,IMAGE,run_bounded,read_group,warning_inventory

def detailed_rows(log):
    matches=re.findall(r'^DC_ROW_(\d+)_BEGIN\n(.*?)^DC_ROW_\1_END$',log,re.M|re.S)
    assert [int(n) for n,_ in matches]==list(range(10))
    answer=[]
    for _,text in matches:
        row={k:float(v) for k,v in re.findall(r'^([vi]\([^\n=]+\))\s*=\s*(\S+)',text,re.M)}
        assert set(row)==set(VECTORS) and all(math.isfinite(v) for v in row.values());answer.append(row)
    return answer
def compare(a,b):
    assert set(a)==set(b)==set(VECTORS)
    delta={k:abs(a[k]-b[k]) for k in a}
    assert all(d<=(1e-9 if k.startswith('i(') else 1e-6) for k,d in delta.items())
    return dict(status='passed original within-source voltage/current bounds',exact=a==b,absolute_delta=delta)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['packet','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--case',required=True);p.add_argument('--kind',choices=['historical','candidate','repeat','reverse'],required=True)
    p.add_argument('--baseline',type=Path);p.add_argument('--cpu',type=int,choices=[1,2],required=True);a=p.parse_args()
    assert os.sched_getaffinity(0)=={a.cpu} and not a.output.exists();tested=controls()
    pc=json.loads((a.packet/'contract.json').read_text());assert pc['candidate_source_sha256']==sha(a.packet/'candidate.spice')==SOURCE
    source_inventory((a.packet/'candidate.spice').read_text());record,=[x for x in pc['cases'] if x['case']==a.case]
    original=REFERENCE/(a.case+'.cir');assert sha(original)==record['original_deck_sha256']
    assert sha(REFERENCE/'sense_substrate_tied.spice')==HISTORICAL
    historical=json.loads((REFERENCE/'provenance.json').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2');models={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}
    runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),model_sha256=models,solver='sparse')
    assert runtime['pdk_commit']==historical['pdk_commit'] and runtime['ngspice_version']==historical['ngspice_version'] and models==historical['model_hashes']
    a.output.mkdir(parents=True);(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    proof=None
    if a.kind=='historical':deck=original.read_text()
    else:
        (a.output/'candidate.spice').write_bytes((a.packet/'candidate.spice').read_bytes())
        deck,proof=make_deck(original.read_text(),a.output/'candidate.spice',pc['queries'],a.kind=='reverse')
    (a.output/'probe.cir').write_text(deck)
    contract=dict(case=a.case,corner=record['corner'],kind=a.kind,cpu=a.cpu,packet_sha256=sha(a.packet/'contract.json'),source_sha256=HISTORICAL if a.kind=='historical' else SOURCE,
        original_deck_sha256=sha(original),deck_sha256=sha(a.output/'probe.cir'),observation_proof=proof,
        baseline_sha256=sha(a.baseline/'summary.json') if a.baseline else None,watchdog_s=120,
        scope=pc['scope'],criteria=pc['criteria'],controls=tested)
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');(a.output/'provenance.json').write_text(json.dumps(runtime,indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',120,cwd=SIM,interval_s=1)
    log=(a.output/'run.log').read_text();result=dict(status='failed',kind=a.kind,case=a.case,runtime=state,errors=errors(log),warnings=warning_inventory(log),source_sha256=contract['source_sha256'])
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors'] and 'QUALIFICATION_END' in log
        assert sha(original)==record['original_deck_sha256']
        if a.kind=='historical':
            old=re.findall(r'^ROW .+$',(REFERENCE/(a.case+'.log')).read_text(),re.M);new=re.findall(r'^ROW .+$',log,re.M)
            assert len(new)==9 and new==old;result.update(historical_printed_nine_rows_exact=True,rows=new)
        else:
            assert sha(a.output/'candidate.spice')==SOURCE
            before=read_group(log,'SENSE_BEFORE',pc['queries']);after=read_group(log,'SENSE_AFTER',pc['queries']);assert before==after and len(before)==529
            result.update(parameter_before=before,parameter_after=after,all529_before_after_exact=True)
            rows=detailed_rows(log);result['rows']=rows;result['return_control']=compare(rows[0],rows[-1])
            keyed={}
            for i,index in enumerate(proof['order']):
                point=proof['points'][index];row=rows[i]
                assert abs(row['v(shp)']-point['positive_V'])<=1e-12 and abs(row['v(cm)']-point['negative_V'])<=1e-12
                assert abs((row['v(shp)']+row['v(cm)'])/2-point['true_cm_V'])<=1e-12
                if i<9:keyed[point['label']]=row
            assert len(keyed)==9;result['point_rows']=keyed
            gains={str(cm):(keyed['t0_c'+str(cm)+'_s0.05']['v(isense)']-keyed['t0_c'+str(cm)+'_s0']['v(isense)'])/.05 for cm in [-.1,0,.3]}
            result.update(gains_V_per_V=gains,gain_status='passed' if all(19.9<=x<=20.1 for x in gains.values()) else 'failed',
                raw_input_error_V={label:(row['v(isense)']-51/53*1.04)/20-proof['points'][next(i for i,x in enumerate(proof['points']) if x['label']==label)]['shunt_V'] for label,row in keyed.items()},
                offset_acceptance='not assessed; not calibrated joint-chain evidence')
            if a.kind in ['repeat','reverse']:
                assert a.baseline
                base=json.loads((a.baseline/'summary.json').read_text());assert base['status']=='passed source/finite DC tuple' and base['kind']=='candidate' and base['case']==a.case and base['source_sha256']==SOURCE
                assert base['parameter_before']==before
                result['point_controls']={label:compare(row,base['point_rows'][label]) for label,row in keyed.items()}
        result['status']='passed source/finite DC tuple'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_before','parameter_after','rows','point_rows']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)
if __name__=='__main__':main()
