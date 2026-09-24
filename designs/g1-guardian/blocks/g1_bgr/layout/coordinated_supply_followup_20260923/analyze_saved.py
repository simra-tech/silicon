#!/usr/bin/env python3
"""Saved-only complete comparison to both the collector parent and original native."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    run=bulk/'bgr-supply-kpex-20260923-r1'
    prep=bulk/'bgr-supply-fixture-20260923-r1'
    out=bulk/'bgr-supply-comparison-20260923-r1'
    assert not out.exists();out.mkdir()
    analyze=HERE.parent/'coordinated_model_boundary/analyze_external_pin.py'
    compare=HERE.parent/'coordinated_dvbe_remedy_20260923/compare_dvbe.py'
    source=HERE.parents[1]/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    inputs={str(p):sha(p) for p in (analyze,compare,source,Path(__file__))}
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    commands=[[sys.executable,str(analyze),'--run',str(run),'--prepared',str(prep)]]
    for bprep,brun,name in [('bgr-dvbe-collector-fixture-20260923-r1','bgr-dvbe-collector-kpex-20260923-r1','vs_collector_parent.json'),
                            ('bgr-external-pin-source-20260923-r1','bgr-external-pin-kpex-20260923-r1','vs_original.json')]:
        commands.append([sys.executable,str(compare),'--baseline-prepared',str(bulk/bprep),
                         '--candidate-prepared',str(prep),'--baseline-run',str(bulk/brun),
                         '--candidate-run',str(run),'--source',str(source),'--output',str(out/name)])
    for i,cmd in enumerate(commands):
        with (out/('stage%d.log'%i)).open('x') as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        assert result.returncode==0,(i,result.returncode)
    assert all(sha(Path(p))==h for p,h in inputs.items())
    print(json.dumps({n:{k:json.loads((out/n).read_text())[k] for k in ('delta_VREF_V','remaining_VREF_error_V','nonzero_runtime_s')}
                      for n in ('vs_collector_parent.json','vs_original.json')},indent=2))


if __name__=='__main__':main()
