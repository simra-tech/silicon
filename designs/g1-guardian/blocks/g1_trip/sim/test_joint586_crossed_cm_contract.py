import json,unittest
from prepare_joint586_crossed_cm_contract import rows,SIM


class Coverage(unittest.TestCase):
    def test_exact144_no_population_credit_or_missing_combinations(self):
        contract=json.loads((SIM/'qualification/joint586-adverse30-contract-20260923-b/contract.json').read_text())
        result=rows(contract['required_crossed_CM_conditions'])
        self.assertEqual(len(result),144)
        for corner,seed in [('slow',77101),('fast',78101)]:
            cohort=[r for r in result if r['corner']==corner]
            self.assertEqual(len(cohort),72);self.assertEqual({r['seed'] for r in cohort},{seed})
            self.assertEqual(sum(r['kind']=='guard' for r in cohort),48)
            self.assertEqual(sum(r['kind']=='residual' for r in cohort),24)
            actual={tuple(r['condition'][1:]) for r in cohort}
            expected={(t,a,d,c) for t in [-40,125] for a,d in [(3.,1.08),(3.3,1.2),(3.6,1.32)] for c in [-.1,.3]}
            self.assertEqual(actual,expected)


if __name__=='__main__':unittest.main()
