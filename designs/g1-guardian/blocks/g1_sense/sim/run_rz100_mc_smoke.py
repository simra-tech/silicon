#!/usr/bin/env python3
"""One qualified R100 standalone sample; screen extension requires smoke proof."""
import argparse,json,os,subprocess
from pathlib import Path
from run_rz100_mc_control import SIM,sha,parse,electrical,errors,warning_inventory,run_bounded
from prepare_rz100_dc_grid import SOURCE

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--packet',type=Path,required=True)
    ap.add_argument('--method',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--cpu',type=int,choices=[1,6,7],required=True)
    ap.add_argument('--phase',choices=['smoke20','screen80'],default='smoke20')
    ap.add_argument('--smoke-audit',type=Path)
    a=ap.parse_args()
    assert os.sched_getaffinity(0)=={a.cpu}
    if a.phase=='smoke20':
        assert 41001<=a.seed<=41020
    else:
        assert 41021<=a.seed<=41100 and a.smoke_audit
        assert sha(a.smoke_audit)=='5c9330764380f8d27dd7f5bd8fd70497a1779d769f302aa2837c7425f7f18efe'
        smoke=json.loads(a.smoke_audit.read_text())
        assert smoke['controls']=={'passed':20} and smoke['electrical_failed']==0
    assert not a.output.exists()
    assert sha(a.method/'summary.json')=='f42e73611f99353d6cd401eeceadcb55c75213203b3c55fdc7017243a7efdc0a'
    assert sha(a.method/'independent_audit_r2.json')=='c40073ae572618cbe0c442b81956e72b77b7c0a1333b31f1dc9430173217eeea'
    pc=json.loads((a.packet/'contract.json').read_text())
    assert sha(a.packet/'contract.json')=='e014fa892b04904419ec5fc7614281a96580283088f8514289170434966a6741'
    assert sha(a.packet/'candidate.spice')==SOURCE
    baseline=a.packet/'candidate.cir'
    assert sha(baseline)==pc['artifacts']['candidate']['deck_sha256']
    text=baseline.read_text();old='setseed 41039\n';new=f'setseed {a.seed}\n'
    assert text.count(old)==1
    deck=text.replace(old,new)
    assert deck.replace(new,old)==text
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_hashes={str(p.relative_to(pd)):sha(p) for p in (pd/'libs.tech/ngspice/models').rglob('*') if p.is_file()})
    assert sha(a.method/'provenance.json')=='18bf99c9c9cb611cc1decba72b596348fc1a26d86696821783de2ee1e3163d12'
    assert runtime==json.loads((a.method/'provenance.json').read_text())
    historical=list((SIM/'qualification').glob(f'mc-gm4-comp3-{a.phase}-b*-20260922-a/seed{a.seed}.log'))
    assert len(historical)==1
    reference=parse(historical[0].read_text(),[])
    a.output.mkdir(parents=True)
    (a.output/'probe.cir').write_text(deck)
    (a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'contract.json').write_text(json.dumps(dict(seed=a.seed,source_sha256=SOURCE,phase=a.phase,
        deck_sha256=sha(a.output/'probe.cir'),cpu=a.cpu,timeout_s=120,seed_only_inverse_exact=True,
        original_log_sha256=sha(historical[0]),method_sha256=sha(a.method/'summary.json'),
        runtime=runtime,scope=pc['scope']),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:
        state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',120,cwd=SIM,interval_s=.2)
    log=(a.output/'run.log').read_text()
    result=dict(seed=a.seed,status='failed',runtime=state,errors=errors(log),warnings=warning_inventory(log),
        source_sha256=SOURCE,full_PEX='not run',hardware='not applicable')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors'] and 'QUALIFICATION_END' in log
        assert sha(a.packet/'candidate.spice')==SOURCE
        result.update(parse(log,pc['queries']))
        assert result['legacy']==reference['legacy']
        result['electrical']=electrical(result['rows'])
        result['status']='passed sample controls; electrical separate'
    except (AssertionError,ValueError,KeyError,OSError) as exc:
        result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(seed=a.seed,status=result['status'],wall_s=state['wall_s'],
        electrical={k:v for k,v in result.get('electrical',{}).items() if k!='points'})))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__':main()
