#!/usr/bin/env python3
"""Unchanged stock native LVS of the current digital/physical-tap candidate."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import traceback
import pya

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
PDK=Path('/foss/pdks/ihp-sg13g2')
TOP='placed_core_NOT_CONNECTED_FULLCHIP'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,j):p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--resource-gate',type=Path,required=True)
    ap.add_argument('--minimum-budget',type=int,required=True)
    a=ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_text(EFFECTIVE_CODE)
    (a.output/'binding_wrapper.py').write_bytes(WRAPPER.read_bytes())
    result=dict(status='running preflight',native_extraction='not run',strict_fullchip_LVS='not run')
    passed=False
    try:
        assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
        gate=json.loads(a.resource_gate.read_text())
        age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
        assert gate['status']=='passed' and 0<=age<1800 and gate['project_cpu_budget']>=a.minimum_budget
        assert gate['expected_growth_gib']>=.02 and gate['external_allocation']['expected_growth_gib']>=2
        assert gate['ram_available_bytes']>=16*2**30
        assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        bulk=Path(os.environ['G1_RESULTS_ROOT'])
        layout=bulk/'analog-pair-integration-20260923-r1/analog_pair_native.gds'
        candidate=layout.parent/'analysis.json'
        preparation=bulk/'analog-pair-reference-20260923-r1/summary.json'
        source=preparation.parent/'physical_taps_reader.cdl'
        source_original=preparation.parent/'physical_taps.cdl'
        parser=HERE.parents[1]/'fullchip_reference_closure/physical_lvs/inspect_stock_result_r4.py'
        expected={layout:'be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307',
            candidate:'80575bbd6a51044a287bb091c6888a02acdb4fb096d95dc201278dcc7e74fab3',
            source:'35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51',
            source_original:'ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e',
            parser:'e53c46f698af2825e8a3a127bfe8b04d5ed5e4783ba45ec49b5ef63f0f04c361'}
        assert all(sha(p)==h for p,h in expected.items())
        cj=json.loads(candidate.read_text());pj=json.loads(preparation.read_text())
        assert cj['status'].startswith('passed') and cj['GDS_sha256']==sha(layout)
        assert sha(preparation)=='0e6bb78e137b01c17d3b0ee4893d12aa1193342b3148be948ad22ed688ea2a1b'
        assert pj['status'].startswith('passed') and pj['GDS_sha256']==sha(layout)
        assert len(pj['arms'])==2
        for arm in pj['arms']:
            assert sha(preparation.parent/arm['file'])==arm['output_sha256']
            assert arm['all386tap_records_and_nodes_exact'] and arm['all_other_blocks_and_source_bytes_exact']
            assert arm['reverse_bytes_exact'] and arm['exact_standalone_SENSE_body_after_top_name_projection']
            assert len(arm['flattened_differences'])==2 and all(arm['negative_controls'].values())
            normalized=arm['new_region'].rstrip('\n')
            assert normalized.replace('l=62u','l=61u')!=normalized
            assert normalized.replace('w=45u','w=44u')!=normalized
        context=bulk/'analog-pair-context-20260923-r1/summary.json'
        assert sha(context)=='0d1ab6ca320eea357b027c11219c7e98f50cb9f674d0d8cf21e150f2e0fccd44'
        proof=json.loads(context.read_text())
        assert proof['status']=='passed full native context and scoped IO junction exact parity'
        assert proof['all_native_instances_preserved'] and all(proof['full_context_IO_junction_parity'].values())
        assert sha(layout) in proof['inputs'].values()
        expected[context]=sha(context)
        expected[WRAPPER]=sha(WRAPPER)

        header,=re.findall(r'^\.SUBCKT '+TOP+r' ([^\n]+)$',source.read_text(),re.M)
        pins=header.split();assert len(pins)==len(set(pins))==22
        dump(a.output/'expected_source_pins.json',pins)
        rules={str(p.relative_to(PDK)):sha(p) for p in (PDK/'libs.tech/klayout/tech/lvs').rglob('*') if p.is_file()}
        inputs={str(p):sha(p) for p in list(expected)+[preparation,Path(__file__),a.resource_gate]}
        (a.output/'parser.py').write_bytes(parser.read_bytes())
        command=['python3',str(PDK/'libs.tech/klayout/tech/lvs/run_lvs.py'),
            '--layout',str(layout),'--netlist',str(source),'--topcell',TOP,
            '--run_mode','deep','--top_lvl_pins','--spice_comments','--run_dir',str(a.output/'reports')]
        result.update(status='running native stock extraction/comparison',inputs=inputs,stock_rule_hashes=rules,
            command=command,source_pins=pins,watchdog_seconds=900,analysis_watchdog_seconds=60,
            memory_reservation_GiB=16,memory_enforced=False,output_bound_GiB=2,
            runtime=dict(klayout=pya.__version__,pdk_commit=(PDK/'COMMIT').read_text().strip(),
                image='ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'),
            scope='Current digital and two-passive SENSE source; owner-authorized explicit VSS and independently derived physical tap A/P. Reversible X-to-R tap reader syntax. All three all-VDD source dummies retained.',
            not_run=['electrical tap-R applicability','new SPI sequencing','PEX','adoption'],
            not_applicable=['random seed','device/model/rule tuning'])
        dump(a.output/'summary.json',result)
        with (a.output/'stock_console.log').open('x') as log:
            run=run_bounded(command,log,a.output/'run.json',900,cwd=ROOT,
                env=dict(os.environ,KLAYOUT_PATH=str(PDK/'libs.tech/klayout')),interval_s=5)
        result.update(run=run,native_extraction='attempted; actual report determines completion')
        dump(a.output/'summary.json',result)
        command=['python3',str(parser),'--reports',str(a.output/'reports'),'--returncode',str(run['returncode']),
            '--top',TOP,'--pins-json',str(a.output/'expected_source_pins.json'),'--mode','deep',
            '--output',str(a.output/'strict_analysis.json')]
        with (a.output/'analysis.log').open('x') as log:
            check=run_bounded(command,log,a.output/'analysis_run.json',60,cwd=ROOT,interval_s=5)
        parsed=json.loads((a.output/'strict_analysis.json').read_text()) if (a.output/'strict_analysis.json').exists() else None
        unchanged=all(sha(Path(p))==h for p,h in inputs.items()) and all(sha(PDK/p)==h for p,h in rules.items())
        growth=sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file())
        passed=run['status']=='completed' and run['returncode']==0 and check['status']=='completed' and parsed is not None and parsed['status'].startswith('passed') and unchanged and growth<2*2**30
        result.update(status='passed strict native fullchip LVS' if passed else 'failed strict native fullchip LVS',
            strict_fullchip_LVS='passed' if passed else 'failed',analysis_run=check,
            analysis_summary={k:v for k,v in parsed.items() if k!='database'} if parsed else None,
            input_rule_parity='passed' if unchanged else 'failed',output_bytes=growth,
            output_bound='passed' if growth<2*2**30 else 'failed')
    except BaseException as exc:
        result.update(status='failed preflight or harness',error=repr(exc),traceback=traceback.format_exc())
    finally:
        dump(a.output/'summary.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','stock_rule_hashes')},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
