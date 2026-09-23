import unittest
from pathlib import Path
from run_digital_postcts import initial_views


class InitialStateTests(unittest.TestCase):
    def test_no_stale_physical_evidence(self):
        old = dict(json_h='source.json', vh='source.vh', sdf={'corner': 'old.sdf'},
                   odb='old.odb', metrics={'timing__hold__ws': 1,
                   'design__lint_error__count': 0, 'design__instance__count': 4413,
                   'synthesis__check_error__count': 0})
        new = initial_views(old, Path('/candidate'))
        self.assertNotIn('sdf', new)
        self.assertEqual(new['odb'], '/candidate/g1_digital.odb')
        self.assertEqual(new['metrics'], {'design__lint_error__count': 0,
                                          'synthesis__check_error__count': 0})
        self.assertEqual(new['json_h'], old['json_h'])
        self.assertEqual(new['vh'], old['vh'])
        self.assertEqual(old['odb'], 'old.odb')


if __name__ == '__main__':
    unittest.main()
