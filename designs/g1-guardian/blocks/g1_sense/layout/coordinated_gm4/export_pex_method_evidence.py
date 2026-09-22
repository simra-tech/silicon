#!/usr/bin/env python3
"""Export compact PEX-method evidence with explicit portable-summary provenance."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve();assert not output.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve();here=Path(__file__).resolve().parent
    exact={
        'exact_capacitances.json':'sense-api-recovery-20260922-r1/data/exact_capacitances.json',
        'raw_recovery_summary.json':'sense-api-recovery-20260922-r1/data/summary.json',
        'mapped_incomplete_capacitances.json':'sense-api-recovery-20260922-r1/mapped_incomplete_capacitances.json',
        'coverage_existing132_r1.json':'sense-kpex-coverage-20260922-r1/summary.json',
        'coverage_existing132_r2.json':'sense-kpex-coverage-20260922-r2/summary.json',
        'coverage_complete134_r5.json':'sense-kpex-coverage-20260922-r5/summary.json',
        'computed_partition_audit.json':'sense-computed-partition-20260922-r1/summary.json',
        'mim_saved_solver_audit.json':'sense-mim-fastercap-20260922-r2/saved_solver_audit.json',
        'mim_coupon_manifest.json':'sense-mim-method-coupon-20260922-r1/manifest.json',
        'sense_mim_method_control.gds':'sense-mim-method-coupon-20260922-r1/sense_mim_method_control.gds',
        'sense_mim_method_control.cdl':'sense-mim-method-coupon-20260922-r1/sense_mim_method_control.cdl',
    }
    portable={
        'original_blackbox_writer_failure.json':'sense-fullassembly-cc-20260922-r1/summary.json',
        'api_recovery_supervisor.json':'sense-api-recovery-20260922-r1/supervisor.json',
        'mim_cli_setup_failure_r1.json':'sense-mim-fastercap-20260922-r1/summary.json',
        'mim_cli_postprocessor_failure_r2.json':'sense-mim-fastercap-20260922-r2/summary.json',
    }
    output.mkdir(parents=True);records=[]
    def check_text(data):
        text=data.decode()
        assert getpass.getuser() not in text
        assert not re.search(r'/(?:home|Users|opt/sim)/[^\s"<>]+',text)
    for destination,relative in exact.items():
        source=bulk/relative;assert source.is_file() and not source.is_symlink()
        data=source.read_bytes()
        if source.suffix!='.gds':check_text(data)
        target=output/destination;target.write_bytes(data);assert sha(source)==sha(target)
        records.append(dict(path=destination,sha256=sha(target),bytes=target.stat().st_size,
                            source_relative=relative,source_sha256=sha(source),transformation='byte-exact'))
    def make_portable(value):
        if isinstance(value,str):return value.replace(str(bulk),'${RESULTS_ROOT}')
        if isinstance(value,list):return [make_portable(item)for item in value]
        if isinstance(value,dict):return {key:make_portable(item)for key,item in value.items()}
        return value
    for destination,relative in portable.items():
        source=bulk/relative;data=json.loads(source.read_text())
        data=make_portable(data);data['_export_provenance']=dict(original_sha256=sha(source),
            transformation='Dedicated runtime results prefix replaced with ${RESULTS_ROOT}; original retained externally')
        encoded=(json.dumps(data,indent=2)+'\n').encode();check_text(encoded)
        target=output/destination;target.write_bytes(encoded)
        records.append(dict(path=destination,sha256=sha(target),bytes=len(encoded),source_relative=relative,
                            source_sha256=sha(source),transformation='explicit portable JSON derivative'))
    manifest=dict(status='passed compact method export',exporter_sha256=sha(Path(__file__)),files=records,
                  all_original_artifacts_retained=True,qualified_CPEX=False,canonical_geometry_source_modified=False)
    (output/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    sources=['SENSE_PEX_CONTRACT_20260922.md','prepare_sense_pex_view.py','audit_pex_view_roundtrip.py','run_sense_kpex.py',
             'export_sense_kpex_api.py','run_sense_api_recovery.py','audit_sense_kpex_coverage.py',
             'MIM_METHOD_CONTROL_20260922.md','build_mim_method_control.py','run_mim_method_control.py',
             'audit_mim_method_matrix.py','audit_kpex_computed_partition.py','map_sense_raw_capacitances.py',
             'PEX_COMPLETENESS_REVIEW_20260922.md','export_pex_method_evidence.py']
    inventory=[]
    for path in [here/name for name in sources]+sorted(output.iterdir()):
        assert path.is_file() and not path.is_symlink()
        if path.suffix!='.gds':check_text(path.read_bytes())
        inventory.append(dict(path=str(path.relative_to(here)),sha256=sha(path),bytes=path.stat().st_size))
    receipt=dict(status='passed frozen source/evidence inventory',files=inventory,count=len(inventory),
                 total_bytes=sum(row['bytes']for row in inventory),scope='New method diagnostics only; no unchanged committed assembly re-export')
    (output/'commit_inventory.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({key:value for key,value in receipt.items()if key!='files'},indent=2))
    print('Inventory SHA256 '+sha(output/'commit_inventory.json'))


if __name__=='__main__':main()
