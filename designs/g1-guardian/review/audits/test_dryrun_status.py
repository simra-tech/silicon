#!/usr/bin/env python3
"""Exercise actual dry-run shell with bounded tool fixtures and disposable files."""
from pathlib import Path
import os,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[4]
class DryRunStatus(unittest.TestCase):
    def test_continue_evidence_and_preserve_failure(self):
        for failing in ['first','resume','cdl','none']:
            with self.subTest(failing=failing),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);flow=root/'flow';flow.mkdir()
                for name in ['run_dryrun.sh','update_pdn_metrics.py']:shutil.copyfile(ROOT/'flow'/name,flow/name)
                mock=flow/'run.sh'
                mock.write_text('''#!/usr/bin/env bash
set -eu
case "$*" in
  *--to\ OpenROAD.GeneratePDN*) stage=first;;
  *--from\ Odb.RemovePDNObstructions*) stage=resume;;
  python3*) stage=cdl;;
  *) stage=straps;;
esac
printf '%s\\n' "$stage" >> "$TRACE"
if [ "$stage" = "$FAIL_STAGE" ]; then exit 7; fi
''');mock.chmod(0o755)
                run=root/'designs/g1-guardian/blocks/g1_padring/flow/runs/fixture';step=run/'22-openroad-generatepdn';step.mkdir(parents=True)
                (step/'g1_chip_top.odb').write_text('fixture')
                (step/'state_out.json').write_text('{"metrics":{}}')
                (step/'analog_straps.log').write_text('[INFO] analog_straps: check_power_grid -net VDD\n[INFO PSM-0040] All shapes on net VDD are connected.\n')
                for directory in ['pnl','nl']:
                    final=run/'final'/directory;final.mkdir(parents=True)
                    (final/f'g1_chip_top.{directory}.v').write_text('module g1_chip_top(); endmodule\n')
                trace=root/'trace.txt';env=os.environ|{'G1_RUN_TAG':'fixture','FAIL_STAGE':failing,'TRACE':str(trace)}
                proc=subprocess.run(['bash',str(flow/'run_dryrun.sh')],env=env,cwd=root,capture_output=True,text=True)
                self.assertEqual(proc.returncode,0 if failing=='none' else 1,proc.stderr)
                self.assertEqual(trace.read_text().splitlines(),['first','straps','resume','cdl'])
                self.assertTrue((root/'designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top.pnl.v').exists())
if __name__=='__main__':unittest.main()
