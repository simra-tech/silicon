import unittest
from run_final_expanded_sta import spef_commands


class SpefImportTests(unittest.TestCase):
    def test_original_failure_control_preserved(self):
        self.assertEqual(spef_commands('top.spef','macro.spef'),[
            'read_spef -corner CURRENT {top.spef}',
            'read_spef -corner CURRENT -path i_core.u_digital {macro.spef}'])

    def test_order_control_only_reverses(self):
        self.assertEqual(spef_commands('t','m',macro_first=True),spef_commands('t','m')[::-1])

    def test_shared_set_changes_only_second_selector(self):
        original=spef_commands('t','m');new=spef_commands('t','m',shared=True)
        self.assertEqual(new[0],original[0])
        self.assertEqual(new[1],original[1].replace('-corner CURRENT','-name CURRENT'))

    def test_retained_couplings_preserve_both_inputs(self):
        base=spef_commands('t','m',shared=True)
        new=spef_commands('t','m',shared=True,keep=True)
        self.assertEqual([line.replace('-keep_capacitive_coupling ','')for line in new],base)

    def test_reversed_shared_set_rejected(self):
        with self.assertRaises(AssertionError):spef_commands('t','m',macro_first=True,shared=True)

    def test_keep_without_shared_set_rejected(self):
        with self.assertRaises(AssertionError):spef_commands('t','m',keep=True)

    def test_unsafe_tcl_path_rejected(self):
        with self.assertRaises(AssertionError):spef_commands('bad}path','m')


if __name__=='__main__':unittest.main()
