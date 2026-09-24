import re
import unittest
from run_regenpair4_roomcal import make_deck,wave_gate,SIM,PARENT,NAME,replay


class Controls(unittest.TestCase):
    def setUp(self):self.old=(SIM/'qualification'/PARENT/'p00/probe.cir').read_text()

    def test_codes_only_beyond_paths(self):
        new=make_deck(self.old,'c02',[132,145],1.2)
        strip=lambda t:re.sub(r'(?m)^(V[sh][0-7] [sh][0-7] 0 dc) .+$',r'\1 BIT',t)
        restored=new.replace(NAME,PARENT).replace('/c02/phase0.dat','/p00/phase0.dat')
        self.assertEqual(strip(restored),strip(self.old))
        for channel,code in [('s',132),('h',145)]:
            for bit in range(8):
                value=float(re.search(r'(?m)^V%s%d %s%d 0 dc (.+)$'%(channel,bit,channel,bit),new)[1])
                self.assertEqual(value,1.2 if code&(1<<bit) else 0)

    def test_seed_timestep_solver_and_code_rejected(self):
        for old in [self.old.replace('setseed 78101','setseed 78102'),self.old.replace('0 0.2n\n','0 1n\n'),self.old+'\n.options klu\n']:
            with self.assertRaises(AssertionError):make_deck(old,'c00',[0,0],1.2)
        for codes in [[-1,0],[0,256],[False,0]]:
            with self.assertRaises(AssertionError):make_deck(self.old,'c00',codes,1.2)

    def test_header_order_and_endpoint(self):
        ref={'wave_header':['time','v(a)','v(b)']}
        wave_gate(b'time v(a) v(b)\n0 1 2\n1.02e-6 1 2\n',ref)
        for blob in [b'time v(b) v(a)\n0 1 2\n1.02e-6 1 2\n',b'time v(a) v(b)\n0 1 2\n1e-6 1 2\n',b'time v(a) v(b)\n0 1 2\n1.02e-6 nan 2\n']:
            with self.assertRaises(AssertionError):wave_gate(blob,ref)

    def test_original_binary_and_failed_probe(self):
        records=[]
        for index in range(10):
            codes=[0,0] if index==0 else [255,255] if index==1 else replay(records)['next_required_codes']
            records.append(dict(run='c%d'%index,codes=codes,status='passed',decisions={k:code<threshold for k,code,threshold in zip(['soft','hard'],codes,[132,145])}))
        result=replay(records)
        self.assertEqual(result['bracket_status'],'passed selected probes')
        self.assertEqual(result['fixed_residual_codes'],{'soft':132,'hard':145})
        records[-1]['status']='failed'
        self.assertNotEqual(replay(records)['bracket_status'],'passed selected probes')


if __name__=='__main__':unittest.main()
