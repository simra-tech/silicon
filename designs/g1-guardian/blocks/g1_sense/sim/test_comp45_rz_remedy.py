#!/usr/bin/env python3
import unittest
from prepare_comp45_rz_remedy import change,OLD
from run_comp45_partial_c_ac import probe

class Controls(unittest.TestCase):
    def test_allowed_lengths_and_inverse(self):
        for n in [80,100]:
            text='* control\n'+OLD+'\nXRZ other cz vss rppd w=1u l=6.2u\n'
            out=change(text,n)
            self.assertEqual(out.replace(OLD.replace('l=62u',f'l={n}u'),OLD),text)
            self.assertIn('l=6.2u',out)
    def test_duplicate_reject(self):
        with self.assertRaises(AssertionError):change(OLD+'\n'+OLD,80)
    def test_wrong_parent_reject(self):
        with self.assertRaises(AssertionError):change(OLD.replace('l=62u','l=60u'),80)
    def test_unapproved_length_reject(self):
        with self.assertRaises(AssertionError):change(OLD,90)
    def test_probe_held_passive(self):
        line='XOTA vp vn iptat isense vdd vss '+' '.join('node'+str(i) for i in range(11))+' g1_ota_main_candidate'
        for n in [80,100]:
            source='.subckt g1_sense vp vn\n'+line+'\n'+change(OLD,n)+'\n.ends\n'
            out=probe(source)
            self.assertIn(change(OLD,n),out)
            self.assertIn('XOTA vp main_loop_e iptat isense vdd vss',out)
if __name__=='__main__':unittest.main()
