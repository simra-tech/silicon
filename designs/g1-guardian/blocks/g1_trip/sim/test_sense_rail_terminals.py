import unittest
from pathlib import Path
import numpy as np
from prepare_sense_rail_terminals import instrument, transform
from run_sense_rail_terminals import account


class RailTerminalTests(unittest.TestCase):
    def records(self):
        source = Path(__file__).resolve().parents[2]/'g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
        return instrument(source.read_text())

    def fixture(self):
        _, _, rows = self.records()
        volts = np.array([3.3 if r['rail'] == 'vdd' else 0 for r in rows])
        values = np.array([1e-5 if r['rail'] == 'vdd' else -1e-5 for r in rows])
        branches = [sum(values[i] for i, r in enumerate(rows) if r['macro'] == macro and r['rail'] == 'vdd')+3.3e-12 for macro in ['xota', 'xbuf', 'xref']]
        currents = np.array([[0, sum(branches)+3.3e-12]+branches])
        mon = np.array([[0, 3.3, 3.3, 3.3, 3.3]])
        data = np.array([[0]+values.tolist()+volts.tolist()])
        return currents, mon, data, rows

    def test_inventory_and_restoration(self):
        changed, sections, rows = self.records()
        self.assertEqual(len(rows), 102)
        self.assertEqual(sum(r['rail'] == 'vdd' for r in rows), 54)
        self.assertEqual(sum(r['terminal'] == 'B' for r in rows), 58)
        for macro in ['xota', 'xbuf', 'xref']:
            entries = [r for r in rows if r['macro'] == macro and r['device'] == 'XM11']
            self.assertEqual({r['terminal'] for r in entries}, {'S', 'B'})
            self.assertNotEqual(entries[0]['monitor'], entries[1]['monitor'])
        bank, = [r for r in rows if r['device'] == 'RBANK']
        self.assertEqual(len(bank['member_ports']), 96)
        self.assertIn({'device': 'XRD250', 'terminal': '2', 'original_node': 'vss'}, bank['member_ports'])
        restored = changed
        for section in sections:
            restored = restored.replace(section['instrumented'], section['original'])
        self.assertNotIn('VPORT_', restored)

    def test_measured_shunts_and_independent_macro_kcl(self):
        result = account(*self.fixture())
        self.assertEqual(result['raw_top_kcl_1pA_status'], 'failed')
        self.assertEqual(result['accounted_top_kcl_1pA_status'], 'passed')
        self.assertTrue(all(r['status'] == 'passed' for r in result['macro_vdd_rail_kcl'].values()))
        self.assertAlmostEqual(result['added_vdd_monitor_shunt_range_A'][0], 58*3.3e-12, places=20)
        self.assertEqual(len(result['buffer_signed_groups']), 6)

    def test_macro_kcl_error_not_waived(self):
        currents, mon, data, rows = self.fixture()
        data[0, 1+next(i for i, r in enumerate(rows) if r['macro'] == 'xota' and r['rail'] == 'vdd')] += 1e-9
        result = account(currents, mon, data, rows)
        self.assertEqual(result['macro_vdd_rail_kcl']['xota']['status'], 'failed')

    def test_wrong_monitor_voltage_rejected(self):
        currents, mon, data, rows = self.fixture()
        data[0, 1+len(rows)] = 1e-3
        with self.assertRaises(AssertionError):
            account(currents, mon, data, rows)

    def test_signed_source_body_cancellation_not_hidden(self):
        currents, mon, data, rows = self.fixture()
        indices = [i for i, r in enumerate(rows) if r['macro'] == 'xota' and r['device'] == 'XM11']
        data[0, 1+indices[0]] = 1e-3
        data[0, 1+indices[1]] = -1e-3
        result = account(currents, mon, data, rows)
        selected = [r for r in result['terminals'] if r['macro'] == 'xota' and r['device'] == 'XM11']
        self.assertTrue(all(r['shunt_subtracted_entering_terminal_windows']['complete']['sampled_abs_peak_A'] > .00099 for r in selected))

    def test_output_transform_no_analysis_change(self):
        _, _, rows = self.records()
        original = '.save v(a)\n.control\nop\necho POPULATION_OP_END\n.endc\n'
        changed = transform(original, 'old', 'new', rows)
        self.assertEqual(changed.count('\nop\n'), 1)
        self.assertIn('wrdata qualification/new/rail_terminals.dat ', changed)


if __name__ == '__main__':
    unittest.main()
