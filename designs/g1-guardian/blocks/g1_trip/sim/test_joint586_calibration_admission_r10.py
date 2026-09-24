"""Pure permit binding and original-runner preservation controls."""
import json
import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_joint586_calibration_admission_r10 as a


class Controls(unittest.TestCase):
    def test_original_runner_bytes_and_watchdog_function_held(self):
        self.assertEqual(a.sha(Path(a.original.__file__)),a.RUNNER_SHA)
        self.assertIs(a.original_run_bounded,a.original.run_bounded)

    def test_exact_gate_authority_and_freshness(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            authority=root/'authority.json'
            gate=root/'gate.json'
            request=root/'request.json'
            authority.write_text(json.dumps(dict(status='ROOT authorized r10 terminal successor and leaf admission',
                cpus=[70],activation_sha256='act',checker_sha256='checker',ledger_sha256='ledger',
                policy_version='20260923-owner-overnight10reserve-v5')))
            request.write_text(json.dumps(dict(seed=73197,leaf_index=0)))
            checks={key:True for key in a.REQUIRED_CHECKS}
            checks.update(overnight_window_active=True,overnight_ledger_activated=True)
            report=dict(status='passed',checks=checks,
                activation_sha256='act',checker_sha256='checker',ledger_sha256='ledger',
                policy_version='20260923-owner-overnight10reserve-v5',
                window_status='active overnight CPU loan window',
                window_start_utc=(datetime.datetime.utcnow()-datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                window_end_utc=(datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                project_cpu_budget=80,
                coordinated_allocation=dict(distinct_cpu_ceiling=80,cpus=[70]),utc=a.utc())
            gate.write_text(json.dumps(report))
            context=dict(seed=73197,cpu=70,lease=authority,lease_sha256=a.sha(authority))
            grant=dict(request_sha256=a.sha(request),lease_sha256=context['lease_sha256'],
                seed=73197,cpu=70,authority_path='authority.json',authority_sha256=a.sha(authority),
                gate_path='gate.json',gate_sha256=a.sha(gate),issued_utc=a.utc())
            with patch.object(a.original,'ROOT',root):
                self.assertTrue(a.permit_valid(grant,request,context))
                bad=dict(grant,cpu=71)
                with self.assertRaises(AssertionError):a.permit_valid(bad,request,context)
                report['window_status']='expired overnight CPU loan window';gate.write_text(json.dumps(report))
                grant['gate_sha256']=a.sha(gate)
                self.assertFalse(a.permit_valid(grant,request,context))
                report['window_status']='active overnight CPU loan window';report['checks']['ram_available']=False
                gate.write_text(json.dumps(report));grant['gate_sha256']=a.sha(gate)
                with self.assertRaises(AssertionError):a.permit_valid(grant,request,context)
                report['checks']['ram_available']=True;gate.write_text(json.dumps(report));grant['gate_sha256']=a.sha(gate)
                self.assertTrue(a.permit_valid(grant,request,context))
                report['window_end_utc']='2020-01-01T00:00:00Z';gate.write_text(json.dumps(report));grant['gate_sha256']=a.sha(gate)
                self.assertFalse(a.permit_valid(grant,request,context))
                report['window_end_utc']=(datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                report['status']='failed';gate.write_text(json.dumps(report));grant['gate_sha256']=a.sha(gate)
                self.assertFalse(a.permit_valid(grant,request,context))
                report['status']='passed';gate.write_text(json.dumps(report));grant['gate_sha256']=a.sha(gate)
                self.assertFalse(a.permit_valid(dict(grant,issued_utc='2020-01-01T00:00:00.000000Z'),request,context))

    def test_root_successor_authority_requires_exact_previous_sha(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prior=root/'prior.json';new=root/'new.json';gate=root/'gate.json';request=root/'request.json'
            prior.write_text(json.dumps(dict(status='ROOT authorized r10 terminal successor and leaf admission',cpus=[70])))
            new.write_text(json.dumps(dict(status='ROOT authorized r10 replacement leaf admission',
                previous_lease_sha256='wrong',cpus=[70],activation_sha256='a',checker_sha256='c',
                ledger_sha256='l',policy_version='replacement')))
            gate.write_text('{}');request.write_text('{}')
            context=dict(seed=1,cpu=70,lease=prior,lease_sha256=a.sha(prior))
            grant=dict(request_sha256=a.sha(request),lease_sha256=a.sha(prior),seed=1,cpu=70,
                authority_path='new.json',authority_sha256=a.sha(new),gate_path='gate.json',
                gate_sha256=a.sha(gate),issued_utc=a.utc())
            with patch.object(a.original,'ROOT',root):
                with self.assertRaises(AssertionError):a.permit_valid(grant,request,context)


if __name__=='__main__':unittest.main()
