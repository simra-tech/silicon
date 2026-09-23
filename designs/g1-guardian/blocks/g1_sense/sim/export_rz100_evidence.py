#!/usr/bin/env python3
"""Compact reversible R100/partial-field evidence, including original failures."""
import argparse,getpass,gzip,hashlib,io,json
from pathlib import Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bulk-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--actual-cases',nargs='+',choices=['fast','nominal','slow'],required=True);a=p.parse_args();assert not a.output.exists()
    sim=Path(__file__).resolve().parent;root=sim.parents[4];layout=sim.parent/'layout';rows=[];omitted=[]
    folders=['sense-comp45-private-nodes-preparation-20260923-r1','sense-comp45-zero-c-noise-20260923-r1','sense-comp45-zero-c-step-20260923-r1',
        'sense-comp45-field-preparation-20260923-r1','sense-comp45-field-cc-before-20260923-r1','sense-comp45-field-cc-after-20260923-r1',
        'sense-comp45-field-comparison-20260923-r2','sense-comp45-partial-c-source-20260923-r1','sense-comp45-partial-c-fast-20260923-r1']
    folders += ['sense-comp45-rz'+str(n)+'-borrowed-source-20260923-r1' for n in [80,100]]
    folders += ['sense-comp45-rz80-borrowed-fast-20260923-r1']
    folders += ['sense-comp45-rz100-borrowed-'+c+'-20260923-r1' for c in ['fast','nominal','slow']]
    folders += ['sense-comp45-rz100-native-'+c+'-20260923-r1' for c in ['build','reference','stock']]
    folders += ['sense-comp45-rz100-native-'+c+'-20260923-r1-rz100-adapter' for c in ['build','reference','stock']]
    folders += ['sense-comp45-rz100-native-'+c+'-20260923-r1-preparation' for c in ['reference','stock']]
    folders += ['sense-comp45-rz100-field-'+c+'-20260923-r1'+suffix for c in ['prepare','extract'] for suffix in ['', '-adapter']]
    folders += ['sense-comp45-rz100-field-comparison-20260923-r1','sense-rz100-followthrough-20260923-r1']
    folders += ['sense-rz100-zero-c-'+mode+'-20260923-r1'+suffix for mode in ['noise','step'] for suffix in ['', '-adapter']]
    folders += ['sense-comp45-rz100-actual-source-20260923-r1']
    folders += ['sense-comp45-rz100-actual-'+c+'-20260923-r1' for c in a.actual_cases]
    for case in a.actual_cases:
        result=json.loads((a.bulk_root/('sense-comp45-rz100-actual-'+case+'-20260923-r1')/'analysis/summary.json').read_text())
        assert result['status']=='completed conditional partial-C analysis; completefield NOT qualified'
    a.output.mkdir(parents=True)
    for folder in folders:
        sourcebase=a.bulk_root/folder;assert sourcebase.is_dir(),sourcebase
        for source in sorted(sourcebase.rglob('*')):
            if not source.is_file():continue
            assert not source.is_symlink();raw=source.read_bytes();relative=str(source.relative_to(a.bulk_root))
            # Exact cap tables, commands, reports, source snapshots and final
            # geometry are portable. Large native databases/report overlays
            # remain hash-bound omissions, never claimed to be exported.
            if source.suffix in ['.lvsdb','.rdb'] or source.name.endswith('.rdb.gz') or ('engine' in source.relative_to(sourcebase).parts and source.suffix in ['.gds','.lyt','.lef']):
                omitted.append(dict(path=relative,sha256=sha(raw),bytes=len(raw),reason='Large engine database/report retained by original hash; exact caps and reports exported'));continue
            portable=raw
            if source.suffix!='.gds':
                pairs=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(str(root).encode(),b'${REPOSITORY_ROOT}'),(b'/work/',b'${CONTAINER_REPOSITORY_ROOT}/')]
                for old,new in pairs:portable=portable.replace(old,new)
                restored=portable
                for old,new in reversed(pairs):restored=restored.replace(new,old)
                assert restored==raw
            assert str(Path.home()).encode() not in portable and getpass.getuser().encode() not in portable
            zipped=source.suffix in ['.json','.jsonl','.dat','.log','.cir','.lyrdb'];data=portable
            if zipped:
                memory=io.BytesIO()
                with gzip.GzipFile(fileobj=memory,mode='wb',filename='',mtime=0) as stream:stream.write(portable)
                data=memory.getvalue()
            target=a.output/relative
            if zipped:target=target.with_name(target.name+'.gz')
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            rows.append(dict(path=str(target.relative_to(a.output)),sha256=sha(data),bytes=len(data),original_sha256=sha(raw),decoded_sha256=sha(portable),inverse_exact=True))
    (a.output/'artifact_manifest.json').write_text(json.dumps(dict(status='exported completed scoped evidence; failures and omissions explicit',records=rows,omitted=omitted,
        actual_field_cases=a.actual_cases,not_run_actual_cases=sorted(set(['fast','nominal','slow'])-set(a.actual_cases)),full_field_qualification='failed/unresolved',adoption='not run',no_new_simulation=True),indent=2)+'\n')
    helpers=['expose_comp45_internal_nodes.py','test_expose_comp45_internal_nodes.py','run_comp45_private_zero_c.py','prepare_comp45_partial_c.py','test_comp45_partial_c.py',
        'run_comp45_partial_c_ac.py','qualify_comp45_partial_c_baseline.py','analyze_comp45_partial_c_ac.py','prepare_comp45_rz_remedy.py','test_comp45_rz_remedy.py',
        'COMP45_RZ_REMEDY_CONTRACT.md','expose_rz100_internal_nodes.py','adapt_rz100_followthrough.py','analyze_rz100_settling.py',
        'prepare_rz100_actual_partial_c.py','test_rz100_actual_partial_c.py','export_rz100_evidence.py']
    paths=sorted(q for q in a.output.rglob('*') if q.is_file())+[sim/q for q in helpers]
    paths += [layout/'coordinated_comp45_rz62'/q for q in ['prepare_affected_field_views.py','extract_affected_field_cc.py','analyze_affected_field_cc.py']]
    paths += [layout/'coordinated_comp45_rz100'/q for q in ['adapt_native.py','adapt_field.py']]
    paths += [sim.parent/'reports/RZ100_PARTIAL_FIELD_20260923.md']
    inventory=[dict(path=str(q.resolve().relative_to(root)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size) for q in paths]
    target=a.output/'commit_inventory.json';target.write_text(json.dumps(dict(status='frozen listed files only',files=inventory,total_bytes=sum(r['bytes'] for r in inventory),self_excluded=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(inventory),bytes=sum(r['bytes'] for r in inventory),inventory_sha256=sha(target.read_bytes()))))
if __name__=='__main__':main()
