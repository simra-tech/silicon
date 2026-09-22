"""Synthetic before/after contracts; inventory size is separately source-audited."""
import unittest
from run_bgr_substitution_transient import parameter_audit


class SubstitutionContract(unittest.TestCase):
    def setUp(self):
        self.non = ['@n.xs.xm%d[w]' % i for i in range(24)]
        self.bgr = ['@n.xbgr.xm%d[delvto]' % i for i in range(3)]
        self.baseline = [[key, '1.0'] for key in self.non]
        self.prep = {'candidate2842_queries': self.bgr,
                     'candidate2842_nominal_expected': ['0.0'] * 3,
                     'original27_observations': self.baseline + [[key, '.01'] for key in self.bgr],
                     'non_bgr24_expected': dict(self.baseline)}
        self.inventory = {'queries': self.non}
        self.log = ''
        for when in ['BEFORE', 'AFTER']:
            for group, keys, value in [('NON_BGR', self.non, '1.0'), ('BGR', self.bgr, '0.0')]:
                tag = group + '_' + when
                self.log += tag + '_BEGIN\n' + ''.join(key + ' = ' + value + '\n' for key in keys) + tag + '_END\n'
        self.log += ''.join(key + ' = 1.0\n' for key in self.non)
        self.log += ''.join(key + ' = 0.0\n' for key in self.bgr)

    def audit(self, log):
        return parameter_audit(log, self.prep, self.inventory, self.baseline)

    def test_all_nonBGR_exact_and_BGR_change_distinct(self):
        result = self.audit(self.log)
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(len(result['original_three_BGR_changes']), 3)
        self.assertTrue(all(not row['unchanged'] for row in result['original_three_BGR_changes']))

    def test_post_transient_change_rejected(self):
        log = self.log.replace('NON_BGR_AFTER_BEGIN\n@n.xs.xm0[w] = 1.0',
                               'NON_BGR_AFTER_BEGIN\n@n.xs.xm0[w] = 1.1')
        self.assertFalse(self.audit(log)['checks']['nonBGR_after_equals_temperature_matched8670baseline'])

    def test_non_nominal_BGR_rejected(self):
        log = self.log.replace('BGR_BEFORE_BEGIN\n@n.xbgr.xm0[delvto] = 0.0',
                               'BGR_BEFORE_BEGIN\n@n.xbgr.xm0[delvto] = .001')
        self.assertFalse(self.audit(log)['checks']['newBGR_before_all2842nominal_exact'])

    def test_missing_after_group_rejected(self):
        with self.assertRaises(AssertionError):
            self.audit(self.log.replace('NON_BGR_AFTER_BEGIN', 'MISSING_BEGIN'))


if __name__ == '__main__':
    unittest.main()
