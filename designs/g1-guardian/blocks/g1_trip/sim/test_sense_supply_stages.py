import unittest
import numpy as np
from prepare_sense_supply_stages import TARGETS, instrument, transform
from run_sense_supply_stages import account


class SupplyStageTests(unittest.TestCase):
    def fixture(self):
        return ''.join('.subckt '+subckt+' inp inn bias out vdd vss\n'+''.join(name+' d g '+rail+' '+rail+' '+('sg13_hv_pmos' if rail == 'vdd' else 'sg13_hv_nmos')+' w='+('2u' if subckt == 'g1_ota_main_candidate' else '1u')+' l=1u\n' for name, rail in devices.items())+'.ends\n' for subckt, devices in TARGETS.items())

    def test_exact_restoration_and_inventory(self):
        original = self.fixture()
        changed, records, instances = instrument(original)
        self.assertEqual(len(records), 9)
        self.assertEqual(len(instances), 11)
        self.assertEqual(sum(r['rail'] == 'vdd' for r in instances), 8)
        self.assertEqual(changed.count('VSTAGE_'), 9)

    def test_accounted_shunts(self):
        _, _, instances = instrument(self.fixture())
        volts = np.array([3.3 if r['rail'] == 'vdd' else 0 for r in instances])
        measured = np.array([.0001 if r['rail'] == 'vdd' else -.0001 for r in instances])
        stage = np.array([[0]+measured.tolist()+volts.tolist()])
        currents = np.array([[0, .0013000000033, .0005, .0004, .0004]])
        monitors = np.array([[0, 3.3, 3.3, 3.3, 3.3]])
        result = account(currents, monitors, stage, instances)
        self.assertEqual(result['raw_kcl_1pA_status'], 'failed')
        self.assertEqual(result['accounted_kcl_1pA_status'], 'passed')
        self.assertAlmostEqual(result['all_added_vdd_node_shunt_current_range_A'][0], 39.6e-12, places=20)
        self.assertEqual(set(result['remaining_buffer_vdd_upper_bar_windows']), {'xbuf', 'xref'})

    def test_monitor_wrong_rail_rejected(self):
        _, _, instances = instrument(self.fixture())
        with self.assertRaises(AssertionError):
            account(np.array([[0, .001, .0004, .0003, .0003]]), np.array([[0, 3.3, 3.3, 3.3, 3.3]]), np.zeros((1, 23)), instances)

    def test_output_only_deck_transform(self):
        _, _, instances = instrument(self.fixture())
        text = '.save v(a)\n.control\nop\necho POPULATION_OP_END\n.endc\n'
        result = transform(text, 'old', 'new', instances)
        self.assertEqual(result.count('\nop\n'), 1)
        self.assertIn('wrdata qualification/new/stages.dat ', result)


if __name__ == '__main__':
    unittest.main()
