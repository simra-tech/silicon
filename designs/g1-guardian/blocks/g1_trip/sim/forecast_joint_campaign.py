#!/usr/bin/env python3
"""Forecast a declared same-source campaign from complete, preserved joint pilots."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from analyze_joint_calibration import summarize

SIM=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaigns',nargs='+',required=True)
    p.add_argument('--sample-count',type=int,default=300)
    p.add_argument('--allow-incomplete',action='store_true',help='Preliminary private planning only; never pilot qualification')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    paths=[SIM/'qualification'/name for name in a.campaigns]
    audit=summarize(paths)
    complete=(audit['sample_completion_counts']=={'completed checks':len(paths)} and
              audit['selected_probe_count']==len(paths)*28 and audit['combine_status']=='passed unique seeds')
    assert complete or a.allow_incomplete,'Wait for all pilot checks; do not relaunch running work'
    leaves=[];parents=[];identities=[]
    for path in paths:
        parents.append(sum(f.stat().st_size for f in path.iterdir() if f.is_file()))
        for sample in json.loads((path/'summary.json').read_text()):
            for probe in sample['probes']:
                leaf=SIM/'qualification'/probe.get('evidence_run',probe['run'])
                raw=json.loads((leaf/'summary.json').read_text())[0]
                assert raw['solver_status']=='passed' and len(raw['fingerprints'])==27
                receipts=list(leaf.glob('*.dat.archive.json'))
                assert len(receipts)==1 and not list(leaf.glob('*.dat'))
                receipt=json.loads(receipts[0].read_text())
                assert receipt['status']=='passed' and sha(leaf/receipt['gzip_name'])==receipt['gzip_sha256']
                prov=json.loads((leaf/'provenance.json').read_text())
                identity={k:prov[k] for k in ['image_id_observed_by_host','pdk_commit','ngspice_version','model_sha256']}
                identity['consumed_sources']={n:sha(leaf/n) for n in ['sense.spice','trip.spice','bgr.spice']}
                identities.append(identity)
                sizes={f.name:f.stat().st_size for f in leaf.iterdir() if f.is_file()}
                export_size=sum(size for name,size in sizes.items() if name in ['summary.json','provenance.json','runner.py'] or name.endswith('.archive.json'))+4096
                leaves.append({'run':leaf.name,'seed':sample['seed'],'wall_s':raw['wall_s'],
                    'retained_bytes':sum(sizes.values()),'gzip_bytes':receipt['gzip_bytes'],'original_wave_bytes':receipt['original_bytes'],
                    'portable_export_estimate_bytes':export_size,'summary_sha256':sha(leaf/'summary.json')})
    assert identities and all(i==identities[0] for i in identities)
    assert audit['explicit_frozen27_audit_failures']==0 and audit['missing_or_short_fingerprint_probes']==0
    times=[x['wall_s'] for x in leaves];sizes=[x['retained_bytes'] for x in leaves]
    exports=[x['portable_export_estimate_bytes'] for x in leaves]
    prospective=(a.sample_count-len(paths))*28
    assert prospective>0
    forecasts={}
    for name,fn in [('mean_observed',statistics.mean),('maximum_observed',max)]:
        core_h=fn(times)*prospective/3600
        forecasts[name]={'remaining_samples':a.sample_count-len(paths),'remaining_leaves':prospective,
            'remaining_core_hours':core_h,'ideal_elapsed_hours_by_concurrent_single_thread_leaves':{str(n):core_h/n for n in [12,16]},
            'remaining_retained_GiB':fn(sizes)*prospective/1024**3,
            'remaining_portable_exports_GiB':fn(exports)*prospective/1024**3,
            'parent_metadata_GiB':max(parents)*(a.sample_count-len(paths))/1024**3,
            'sixteen_live_plain_wave_overlap_GiB':max(x['original_wave_bytes'] for x in leaves)*16/1024**3}
    report={'status':'completed-pilot forecast' if complete else 'PRELIMINARY incomplete-pilot forecast',
        'pilot_counts':{k:audit[k] for k in ['sample_completion_counts','selected_probe_count','guards_status_counts','residual_status_counts','clipped_count','solver_failures','incomplete_probes','explicit_frozen27_audit_failures']},
        'scope':'Same frozen gm4comp3 actual-BGR loaded joint circuit, calibrated soft30mV/hard40mV targets. Three pilot samples do not prove yield or a statistical runtime/storage upper bound. No broad campaign is launched by this report; source/fit disposition and fresh resource/storage gates remain required.',
        'campaigns':a.campaigns,'declared_total_samples':a.sample_count,'identity':identities[0],
        'observed':{'complete_leaf_count':len(leaves),'total_core_seconds':sum(times),'mean_leaf_seconds':statistics.mean(times),
                    'maximum_leaf_seconds':max(times),'mean_retained_leaf_bytes':statistics.mean(sizes),'maximum_retained_leaf_bytes':max(sizes)},
        'forecasts':forecasts,'leaves':leaves,
        'limits':['Maximum-observed multiplication is a planning stress case, not a statistical upper bound.',
                  'Fresh failed leaves, larger candidate waveforms, command/orchestration overhead and other-worker growth need explicit reserve.',
                  'External allocation is nearly reserved by comparator600leaves; evaluate new joint bulk on home storage with8GiBreserve.',
                  'Existing pilot external artifacts remain untouched; new home runs must not inherit G1_RESULTS_ROOT.',
                  'Original calibratedbaseline20 and410xxSENSE100 are distinct circuit/sample scopes, not extra jointcandidate samples.']}
    with a.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['identity','leaves']},indent=2))


if __name__=='__main__':main()
