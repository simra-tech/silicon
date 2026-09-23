import unittest
from pathlib import Path
import tempfile
import json
from unittest.mock import patch
from audit_586_calibration_samples import audit_sample, rounded_measurement_consistency, primitive_distinctness, REFERENCE, sha


class AuditTests(unittest.TestCase):
    def test_missing_receipt_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            result = audit_sample(Path(directory)/'missing', 74101)
            self.assertEqual(result['status'], 'not run')
            self.assertFalse(result['complete'])

    def test_actual_ngspice_print_precision(self):
        text = 't_a = 5.86477e-06\nt_b = 1.63108e-05\nfreq = 1.531687943088603e+06\n'
        self.assertTrue(rounded_measurement_consistency(text)['status'].startswith('passed'))
        with self.assertRaises(AssertionError):
            rounded_measurement_consistency(text.replace('1.531687943088603e+06', '1.631687943088603e+06'))

    def test_all_primitive_draws_not_only_whole_vector(self):
        inventory = {'primitives': [{'instance': 'x1', 'group': 'BGR', 'queries': ['a']},
                                     {'instance': 'x2', 'group': 'T2F', 'queries': ['b']}]}
        a = {'BGR': [('a', '1')], 'T2F': [('b', '2')]}
        b = {'BGR': [('a', '1.0')], 'T2F': [('b', '3')]}
        self.assertEqual(primitive_distinctness(inventory, [a, b])['status'], 'failed')
        b['BGR'] = [('a', '2')]
        self.assertEqual(primitive_distinctness(inventory, [a, b])['status'], 'passed')

    def test_archived_control_reader_roundtrip(self):
        # Exercise real log/wave/query serialization, NOT a new sample claim.
        # Only the independent seed-transform check is mocked; it has separate
        # exhaustive transform tests. Existing archived artifacts stay readonly.
        old, = json.loads((REFERENCE/'summary.json').read_text())
        phase, = old['phases']
        prep = json.loads((REFERENCE/'preparation.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)/'reader-only-test'
            leaf = run/'p00'
            leaf.mkdir(parents=True)
            for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'population_inventory.json', 'runner.py']:
                (run/name).symlink_to(REFERENCE/name)
            for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'probe.cir', 'run.log', 'run.json', 'phase0.dat.gz', 'phase0.dat.archive.json']:
                (leaf/name).symlink_to(REFERENCE/name)
            row = dict(phase, status='passed', full3180_status='passed', runtime=old['runtime'], errors=[],
                       deck_sha256=sha(REFERENCE/'probe.cir'))
            (leaf/'summary.json').write_text(json.dumps([row]))
            entry = dict(index=0, temperature_C=25, status='passed', summary_sha256=sha(leaf/'summary.json'),
                         deck_sha256=row['deck_sha256'])
            parent = dict(seed=74101, status='running', leaves=[entry], parameters_first_completed_leaf=phase['parameters_before'])
            (run/'summary.json').write_text(json.dumps([parent]))
            provenance = dict(seed=74101, runtime_identity=prep['runtime'], reference_deck_sha256=prep['deck_sha256'],
                reference_preparation_sha256=sha(REFERENCE/'preparation.json'), runner_sha256=sha(run/'runner.py'),
                source_hashes=prep['source_hashes'], inventory_sha256=prep['inventory_sha256'])
            (run/'provenance.json').write_text(json.dumps(provenance))
            with patch('audit_586_calibration_samples.sample_deck', return_value=(REFERENCE/'probe.cir').read_text()):
                result = audit_sample(run, 74101)
            self.assertEqual(result['evidence_status'], 'passed')
            self.assertFalse(result['complete'])
            self.assertEqual(result['leaves'][0]['full_reaudit'], 'passed')


if __name__ == '__main__':
    unittest.main()
