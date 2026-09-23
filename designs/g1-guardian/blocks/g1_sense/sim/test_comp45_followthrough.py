import unittest
from pathlib import Path
from run_comp45_followthrough import prepare,SOURCE
from run_loaded_compensation_candidate import candidate_source
from run_loaded_followthrough import get_reference,TARGETS
from run_loaded_noise_audit import sha


class FollowthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference_run,cls.ref,cls.prep,_,_=get_reference('settling','rise')
        cls.deck=(cls.ref/'population_transient.cir').read_text()
        cls.out=Path('/qualified-results/c45-followthrough')

    def test_source_main_only(self):
        import hashlib
        text=candidate_source((self.ref/'sense.spice').read_text(),'62','45')
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),SOURCE)

    def test_noise_basis_and_observations(self):
        text=prepare(self.deck,self.out,'noise','nominal',self.prep['groups'],self.reference_run)
        self.assertIn('noise v(isense) Vsh dec 100 1 10meg',text)
        self.assertIn('Vsh shp 0 dc 0.025000000000000001 ac 1',text)
        self.assertEqual(text.count('echo AC_DC_OBS_BEGIN'),1)
        self.assertEqual(text.count('.include '+str(self.out/'candidate.spice')),1)
        self.assertNotIn('Vcm_measure',text)

    def test_step_and_dc(self):
        for case,target in TARGETS.items():
            for mode in ['step','dc']:
                text=prepare(self.deck,self.out,mode,case,self.prep['groups'],self.reference_run)
                self.assertEqual(text.count('echo AC_DC_OBS_BEGIN'),1)
                self.assertEqual('tran 0.2n 1.02u 0 0.2n' in text,mode=='step')
                if mode=='step':self.assertIn('201n '+format(target,'.17g'),text)
                else:self.assertIn('Vsh shp 0 dc '+format(target,'.17g')+'\n',text)

    def test_missing_source_rejected(self):
        with self.assertRaises(AssertionError):
            prepare(self.deck.replace('/sense.spice','/wrong.spice'),self.out,'noise','nominal',self.prep['groups'],self.reference_run)


if __name__=='__main__':unittest.main()
