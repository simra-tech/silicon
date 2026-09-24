import json
import unittest
from run_regenpair4_r100_roomcal import base,sense_r100,OLD_CANDIDATE,OLD_REPLAY,serialized_replay


class Controls(unittest.TestCase):
    def test_only_main_R100_beyond_frozen_R62(self):
        original=(base.SIM/'qualification'/base.PARENT/'sense.spice').read_text()
        new=sense_r100(original);old=OLD_CANDIDATE(original)
        self.assertEqual(new.replace('XRZ out1 cz vss rppd w=1u l=100u m=1 b=0 mm_ok=1','XRZ out1 cz vss rppd w=1u l=62u m=1 b=0 mm_ok=1'),old)
        with self.assertRaises(AssertionError):sense_r100(new)
        with self.assertRaises(AssertionError):sense_r100(original.replace('w=69u l=23u','w=68u l=23u'))

    def test_fresh_original_binary_no_old_code_inheritance(self):
        rows=[]
        for i in range(10):
            codes=[0,0] if i==0 else [255,255] if i==1 else serialized_replay(rows)['next_required_codes']
            rows.append(dict(run='c%d'%i,codes=codes,status='passed',decisions={k:c<n for k,c,n in zip(['soft','hard'],codes,[133,149])}))
        actual=serialized_replay(rows)
        self.assertEqual(actual,json.loads(json.dumps(OLD_REPLAY(rows))))
        self.assertEqual(actual['fixed_residual_codes'],{'soft':133,'hard':149})
        rows[-1]['status']='failed'
        self.assertNotEqual(serialized_replay(rows)['bracket_status'],'passed selected probes')


if __name__=='__main__':unittest.main()
