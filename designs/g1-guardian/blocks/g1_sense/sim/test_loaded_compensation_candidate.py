#!/usr/bin/env python3
"""Source and model-law controls for the isolated compensation candidate."""
import math
import unittest
from run_loaded_compensation_candidate import candidate_source,scale_interval,OLD,NEW,RZ_OLD


class Controls(unittest.TestCase):
    def test_main_rz_only_inverse(self):
        prefix='.subckt buffer a b\n'+RZ_OLD+'\n.ends\n'
        main='.subckt g1_ota_main_candidate a b\n'+RZ_OLD+'\n'+OLD+'\n.ends\n'
        for length in ['24.8','37.2','62']:
            updated=candidate_source(prefix+main,length)
            self.assertTrue(updated.startswith(prefix))
            self.assertEqual(updated.count('l='+length+'u'),1)
            self.assertEqual(updated.replace('l='+length+'u','l=6.2u').replace(NEW,OLD),prefix+main)
        with self.assertRaises(AssertionError):candidate_source(prefix+main,'12')

    def test_coupled_candidate_main_only_inverse(self):
        prefix='.subckt buffer a b\n'+RZ_OLD+'\nXCC cz out cap_cmim w=23u l=23u m=1 mm_ok=1\n.ends\n'
        main='.subckt g1_ota_main_candidate a b\n'+RZ_OLD+'\n'+OLD+'\n.ends\n'
        updated=candidate_source(prefix+main,'62','45')
        self.assertTrue(updated.startswith(prefix))
        self.assertEqual(updated.count('w=45u'),1)
        self.assertEqual(updated.count('l=62u'),1)
        self.assertEqual(updated.replace('w=45u','w=69u').replace('l=62u','l=6.2u'),prefix+main)
    def test_exact_single_source_inverse(self):
        original='.subckt held a b\n'+OLD+'\n.ends\n'
        changed=candidate_source(original)
        self.assertEqual(changed.replace(NEW,OLD),original)
        for bad in [original.replace(OLD,NEW),original+OLD,original.replace('w=69u','w=70u')]:
            with self.assertRaises(AssertionError):candidate_source(bad)

    def test_native_area_law_and_wrong_draw(self):
        for old in ['1.000471200817121e+00','9.999060906637424e-01']:
            new=format(1+(float(old)-1)*math.sqrt(69/50),'.15e')
            self.assertEqual(scale_interval(old,new)['status'],'passed')
            self.assertEqual(scale_interval(old,old)['status'],'failed')
            self.assertEqual(scale_interval(old,format(float(new)+1e-6,'.15e'))['status'],'failed')

    def test_actual_decimal_only_counterexample(self):
        result=scale_interval('9.999060906637424e-01','9.998896815086120e-01')
        self.assertEqual(result['status'],'passed')
        self.assertFalse(result['numerical_options_changed'])

    def test_binary64_native_expression_controls(self):
        # Independent forward source evaluation, both signs and several draws.
        for delta in [-.05,-.01,-.001,0.,.001,.01,.05]:
            mm=1.+delta
            for target in ['50','45']:
                scales=[]
                for width in [69.,float(target)]:
                    area=(23.*1e-6)*(width*1e-6)*1e12
                    scales.append(format(1+(mm-1)/math.sqrt(area),'.15e'))
                self.assertEqual(scale_interval(*scales,cap_width_um=target)['status'],'passed')
                self.assertEqual(scale_interval(scales[0],format(float(scales[1])+1e-6,'.15e'),target)['status'],'failed')


if __name__=='__main__':unittest.main()
