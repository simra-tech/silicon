#!/usr/bin/env python3
"""Check collector continuation and acceptance checks using independent fixtures."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[4]
SPEC=importlib.util.spec_from_file_location('signoff_runner',ROOT/'designs/g1-guardian/blocks/g1_padring/flow/signoff/signoff_runner.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class CollectorAcceptance(unittest.TestCase):
    def test_continue_and_distinguish_results(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);names=['process_failure','markers','missing','timeout','later_pass']
            runner=M.CheckRunner(out,names)
            success=lambda log:('passed',{})
            runner.run('process_failure',[sys.executable,'-c','raise SystemExit(7)'],success)
            bad=out/'bad.lyrdb'
            bad.write_text("<report-database><items><item><category>'M1.b'</category></item></items></report-database>")
            runner.run('markers',[sys.executable,'-c','pass'],lambda log:M.markers(bad))
            runner.run('missing',[sys.executable,'-c','pass'],lambda log:M.markers(out/'missing.lyrdb'))
            runner.run('timeout',[sys.executable,'-c','import time;time.sleep(2)'],success,timeout=.02)
            runner.run('later_pass',[sys.executable,'-c',"print('explicit pass')"],lambda log:M.signature(log,'explicit pass'))
            values={r['name']:r['status'] for r in json.loads((out/'check_status.json').read_text())['checks']}
            self.assertEqual(values,{'process_failure':'failed','markers':'failed','missing':'failed','timeout':'not run','later_pass':'passed'})

    def test_empty_report_required(self):
        with tempfile.TemporaryDirectory() as temp:
            good=Path(temp)/'good.lyrdb';good.write_text('<report-database><items/></report-database>')
            self.assertEqual(M.markers(good)[0],'passed')
            for bad in ['<unrelated/>','<report-database/>','<report-database><items><item/></items></report-database>']:
                good.write_text(bad)
                with self.assertRaises(ValueError):M.markers(good)

    def test_portable_report_paths(self):
        self.assertEqual(M.portable({'file':str(ROOT/'designs/example')}),{'file':'designs/example'})

    def test_raw_supply_failure_overrides_zero_metric(self):
        with tempfile.TemporaryDirectory() as temp:
            log=Path(temp)/'analog_straps.log'
            self.assertEqual(M.supply_grid_status(log,0)[0],'not run')
            log.write_text('[ERROR PSM-0069] Check connectivity failed on VDDA.\n[WARNING] analog_straps: PSM-0069\n')
            status,details=M.supply_grid_status(log,0)
            self.assertEqual(status,'failed');self.assertEqual(details['failed_nets'],['VDDA'])
            self.assertEqual(details['aggregate_metric'],0)
            log.write_text('check_power_grid -net VDDA\n')
            self.assertEqual(M.supply_grid_status(log,0)[0],'not run')
            log.write_text('check_power_grid -net VDDA\nAll shapes on net VDDA are connected\n')
            self.assertEqual(M.supply_grid_status(log,0)[0],'passed')


if __name__=='__main__':unittest.main()
