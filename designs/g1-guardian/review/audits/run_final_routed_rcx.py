#!/usr/bin/env python3
"""Stock OpenRCX on the exact final signal-routing database; no full-GDS claim."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from check_closed_macro_odb import sha, quote
from check_fullchip_def_odb import observation, OPENROAD, PDK


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--route-metadata',type=Path,help='Explicit checked successor route metadata; original default identity is held')
    p.add_argument('--route-metadata-sha256')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert bool(a.route_metadata)==bool(a.route_metadata_sha256)
    if a.route_metadata:
        assert sha(a.route_metadata)==a.route_metadata_sha256
        route=json.loads(a.route_metadata.read_text())
        if route['status']=='passed exact three-segment g_shared_bare spacing repair; stock checks not run':
            from repair_gshared_route_spacing import validate_patch
            validate_patch(a.route_metadata.parent)
        else:
            assert route['status']=='passed isolated detailed-route candidate with zero router markers'
        assert a.source.name=='detailed.odb' and a.source.parent==a.route_metadata.parent
        assert sha(a.source)==route['detailed.odb_sha256']
        assert sha(a.source.with_suffix('.def'))==route['detailed.def_sha256']
    else:
        assert sha(a.source)=='88143d849e5c599423c04e4824c14463b53a08d997aa50d9ea6e6441c811e8d7'
    rules=PDK/'libs.tech/librelane/openrcx/IHP_rcx_patterns.rules'
    assert rules.is_file()
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    inputs={str(path):sha(path)for path in (a.source,rules,OPENROAD)}
    if a.route_metadata:
        inputs.update({str(path):sha(path) for path in [a.route_metadata,a.source.with_suffix('.def')]})
    script=a.output/'extract.tcl'
    lines=['set_thread_count 1','read_db '+quote(a.source)]
    lines+=observation(a.output/'before.tsv')
    lines+=['define_process_corner -ext_model_index 0 CURRENT_CORNER',
            'extract_parasitics -ext_model_file '+quote(rules)+' -lef_res',
            'write_spef '+quote(a.output/'final_signal.nom.spef'),
            'write_verilog '+quote(a.output/'final_signal.nl.v')]
    lines+=observation(a.output/'after.tsv')
    lines+=['puts "FINAL_ROUTED_RCX_COMPLETE"']
    script.write_text('\n'.join(lines)+'\n')
    command=['timeout','--kill-after=5','300',str(OPENROAD),'-exit',str(script)]
    result=dict(status='running',inputs=inputs,script_sha256=sha(Path(__file__)),
                command=command,stock_options='Default via/wire merging and -lef_res, as pinned LibreLane RCX script',
                scope='Detailed signal routing DB only; no full filled native GDS or macro-internal extraction',
                not_run=['Independent SPEF connectivity/completeness audit','Final expanded-macro STA',
                         'Native supplemental supply/terminal metal and fill parasitics',
                         'Actual-source electrical, current and power acceptance'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    started=time.monotonic()
    with (a.output/'extract.log').open('x')as log:
        child=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=child.returncode,wall_s=time.monotonic()-started)
    try:
        assert child.returncode==0
        text=(a.output/'extract.log').read_text()
        assert 'FINAL_ROUTED_RCX_COMPLETE' in text and '[ERROR' not in text
        assert sorted((a.output/'before.tsv').read_text().splitlines())==sorted((a.output/'after.tsv').read_text().splitlines())
        assert all(sha(Path(path))==value for path,value in inputs.items())
        result['functional_instance_and_net_connectivity_unchanged']='passed'
        outputs=[]
        for name in ('final_signal.nom.spef','final_signal.nl.v'):
            path=a.output/name
            assert path.stat().st_size>0
            outputs.append(dict(name=name,bytes=path.stat().st_size,sha256=sha(path)))
        result.update(status='passed stock RCX tool completion and unchanged functional DB connectivity; independent audit pending',outputs=outputs)
    except Exception as exc:
        result.update(status='failed routed RCX tool or source checks',error=repr(exc))
        raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
