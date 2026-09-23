#!/usr/bin/env python3
"""Read-only actual rising-event comparison; no solver acceptance substitution."""
import argparse
import gzip
import json
from pathlib import Path
from prepare_586_klu_controls import HERE, REFERENCES, sha
from run_586_klu_temperature import compare_wave


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args();assert not a.output.exists()
    audit=HERE/'t2f586-klu-matched-control-audit-20260923.json'
    existing=json.loads(audit.read_text());rows={}
    for corner, name in REFERENCES.items():
        assert existing['corners'][corner]['status']=='passed fullparameters and KLU exactrepeat'
        runs=[HERE/'runs'/name,HERE/'runs'/('t2f586-klu-'+corner+'-replay-20260923-a')]
        blobs=[]
        for run in runs:
            for n,h in existing['corners'][corner]['receipts_sha256'][run.name].items():
                assert sha(run/n)==h
            with gzip.open(run/'phase0.dat.gz','rb') as stream:blobs.append(stream.read())
        comparison=compare_wave(*blobs)
        events=comparison['actual_fout_rising_events']
        assert events['original_s'] and events['klu_s']
        comparison['index_paired_rising_event_max_abs_delta_s']=max(map(abs,events['index_paired_deltas_s']))
        f=existing['corners'][corner]['frequencies_Hz']
        comparison['frequency_delta_ppm']=(f[1]/f[0]-1)*1e6
        rows[corner]=comparison
    result=dict(status='completed descriptive event and accepted trajectory comparisons',corners=rows,
                matched_audit_sha256=sha(audit),analyzer_sha256=sha(Path(__file__)),
                comparison_helper_sha256=sha(HERE/'run_586_klu_temperature.py'),
                scope='Original exact wave/grid failures retained. Actual 0.6V rising events paired by index only when counts match; interpolation is descriptive, not solver internal/rejected-step evidence or an accuracy waiver. No population solver adoption.')
    with a.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({c:dict(frequency_delta_ppm=r['frequency_delta_ppm'],events=[len(r['actual_fout_rising_events'][k]) for k in ['original_s','klu_s']],max_delta_s=r['index_paired_rising_event_max_abs_delta_s']) for c,r in rows.items()},indent=2))


if __name__=='__main__':main()
