"""Independent reparse of two lowcarry diagnostics and exact same-method repeat."""
import argparse
import json
from pathlib import Path
from run_dac586_lowcarry_probe import ROOT,SIM,REFERENCE,chunk_deck,sha,analyze


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    execution=ROOT/a.execution;assert sha(execution)==a.execution_sha256;e=json.loads(execution.read_text())
    assert all(sha(ROOT/n)==v for n,v in e['bindings_sha256'].items())
    packet=ROOT/e['packet'];assert sha(packet)==e['packet_sha256'];d=json.loads(packet.read_text());records=[];outputs=[]
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items())
    for case in d['controls']:
        out=SIM/'qualification'/case['run'];record=dict(run_id=case['run'],status='not run');records.append(record)
        if not (out/'run.json').exists():continue
        try:
            assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
            assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
            assert (out/'dac_lowcarry.cir').read_text()==chunk_deck((REFERENCE/'dac_static.cir').read_text(),REFERENCE.name,out.name,prep['groups'])
            provenance=json.loads((out/'provenance.json').read_text());assert provenance['runtime_identity']==prep['expected_runtime_identity'] and provenance['execution_sha256']==a.execution_sha256
            result=analyze(out,prep,json.loads((out/'run.json').read_text()));assert result==json.loads((out/'summary.json').read_text())
            assert result['numerical_status']=='passed'
            record.update(status='passed independent reparse',result=result,receipts_sha256={n:sha(out/n) for n in ['preparation.json','provenance.json','run.json','run.log','summary.json','op0.dat','forward.dat','reverse.dat']});outputs.append(out)
        except (AssertionError,ValueError,KeyError,OSError) as error:record.update(status='failed evidence or numerical gate',error=repr(error))
    repeat=None
    if len(outputs)==2:repeat={n:(outputs[0]/n).read_bytes()==(outputs[1]/n).read_bytes() for n in ['op0.dat','forward.dat','reverse.dat']}
    result=dict(status='completed two lowcarry diagnostics; no scaling',execution_sha256=a.execution_sha256,auditor_sha256=sha(Path(__file__)),records=records,same_method_repeat_exact=repeat,
        scope='Strict repeat and original code0 comparisons remain distinct. No static reference for codes1..7, no universal epsilon or all-code/population/dynamic adoption.')
    output=ROOT/a.output;assert not output.exists();output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],repeat)
    raise SystemExit(0 if len(outputs)==2 and all(repeat.values()) else 1)


if __name__=='__main__':main()
