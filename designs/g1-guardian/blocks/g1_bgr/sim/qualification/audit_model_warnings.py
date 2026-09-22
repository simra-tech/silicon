#!/usr/bin/env python3
"""Inventory retained solver/model warnings without changing completion status."""
import hashlib,json,re
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNS=['bgr_mc20_20260921_01','bgr_mc100_20260921_01','bgr_corners81_20260921_01',
      'bgr_startup6_20260921_01','bgr_stress3_20260921_01','bgr_capload9_20260921_01']
PATTERNS={'temperature_limiter_NaN':r'The temperature limiting function received NaN',
          'singular_matrix':r'Warning: singular matrix',
          'resistor_vmax':r'voltage is greater than specified by vmax',
          'timestep_failure':r'Timestep too small',
          'analysis_aborted':r'analysis aborted'}


def main():
    results=[]
    for run in RUNS:
        folder=HERE/'runs'/run
        manifest=json.loads((folder/'manifest.json').read_text())
        cases=[]
        for case in manifest['cases']:
            paths=[p for p in [folder/(case['name']+'.log'),folder/(case['name']+'.stderr.log')] if p.exists()]
            text='\n'.join(p.read_text(errors='replace') for p in paths)
            counts={kind:len(re.findall(pattern,text,re.I)) for kind,pattern in PATTERNS.items()}
            cases.append({'name':case['name'],'recorded_completion':case['status'],'warning_counts':counts,
                          'log_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
        results.append({'run_id':run,'cases':cases,'cases_with_category':{kind:sum(r['warning_counts'][kind]>0 for r in cases) for kind in PATTERNS},
                        'message_occurrences':{kind:sum(r['warning_counts'][kind] for r in cases) for kind in PATTERNS}})
    result={'runs':results,'interpretation':'These warning flags do not rewrite retained numerical completion or TC outcomes. Finite final vectors do not establish model validity. Original merged stdout/stderr sometimes interleave device names, so message counts are not an exact per-device census. Logs do not establish whether every warning belongs to converged operating points or solver trial states; separate terminal exports are required.',
            'scope':'Baseline100 MC,81 corner/rail sweeps,6 startup,3 stress,9 cap-load cases. Model cards and warnings unchanged.',
            'resistor_warning_source':{'source': 'libs.tech/verilog-a/r3_cmc/r3_cmc-patched.va', 'source_sha256': '8a2c7a9049a1c4a47617bfd0a444bc76169b39e1399337ec580ff588b5924417', 'default_vmax_V': 9900000000.0, 'default_parameter_line': 144, 'warning_lines': [689, 695], 'resistor_model_card_vmax_override': 'none in installed resistor model cards', 'interpretation': 'Warnings cannot be interpreted as a low-voltage operating rating. They concern internal resistor/control-node voltage and may arise during solver trial states; saved external-node audit is separate. Realized OSDI parameter/introspection and timing attribution not yet run.'}}
    (HERE/'model_warning_audit_20260922.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='cases'} for r in results],indent=2))


if __name__=='__main__':main()
