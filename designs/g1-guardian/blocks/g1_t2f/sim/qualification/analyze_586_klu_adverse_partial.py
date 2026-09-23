#!/usr/bin/env python3
"""Conditional original linear-fit diagnostics from completed75201 leaves only."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    audit_path=HERE/'t2f586-klu-fast-s75201-firstsample-audit-20260923.json'
    audit=json.loads(audit_path.read_text())
    assert audit['status']=='passed independent evidence audit' and audit['seed']==75201
    parent=HERE/'runs/t2f586-klu-adverse-calibration-s75201-20260923-a'
    assert all(sha(parent/n)==v for n,v in audit['parent_receipts_sha256'].items())
    result,=json.loads((parent/'summary.json').read_text());leaves=result['leaves']
    assert result['status']=='failed; complete attempted six-condition coverage' and len(leaves)==6
    by_label={r['label']:r for r in leaves};assert by_label['cal25']['status']==by_label['cal100']['status']=='passed'
    slope=(by_label['cal100']['measurements']['freq']-by_label['cal25']['measurements']['freq'])/75
    intercept=by_label['cal25']['measurements']['freq']-slope*25;assert slope>0
    rows=[]
    for leaf in leaves:
        record=dict(label=leaf['label'],original_status=leaf['status'],temperature_C=leaf['temperature_C'],
            VDDA_V=leaf['VDDA_V'],VDD_V=leaf['VDD_V'],conditional_original_criterion_status='not run')
        if leaf['status']=='passed':
            frequency=leaf['measurements']['freq'];estimated=(frequency-intercept)/slope;error=estimated-leaf['temperature_C']
            record.update(frequency_Hz=frequency,conditional_temperature_C=estimated,error_C=error,
                conditional_original_criterion_status='passed' if abs(error)<=2 else 'failed')
        else:record['original_errors']=leaf['errors']
        rows.append(record)
    output=dict(status='completed conditional original-fit decomposition; original sample remains failed',seed=75201,
        slope_Hz_per_C=slope,intercept_Hz=intercept,records=rows,independent_audit_sha256=sha(audit_path),
        parent_summary_sha256=sha(parent/'summary.json'),analyzer_sha256=sha(Path(__file__)),
        scope='Same original25/100 linear formula; no refit/alternate point/removal of failed condition. Lowcold has no valid frequency and staysNOTRUN. This partial diagnostic does not replace parent calibration_status=notrun or qualify fast30/solver adoption.')
    a.output.write_text(json.dumps(output,indent=2)+'\n');print(a.output.name,sha(a.output))


if __name__=='__main__':main()
