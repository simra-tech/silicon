import unittest
from run_73133_soft_instrumentation import SIM,PARENT,NAME,NODES,transform


class Controls(unittest.TestCase):
    def test_only_outputs_change(self):
        for case in ['c08','heldout-p27']:
            old=(SIM/'qualification'/PARENT/case/'probe.cir').read_text();new=transform(old,case)
            self.assertEqual(new.replace(' '+' '.join(NODES)+'\n','\n').replace(NAME,PARENT),old)
            self.assertEqual(new.count(' '.join(NODES)),2)

    def test_wrong_seed_step_and_repeated_output(self):
        old=(SIM/'qualification'/PARENT/'c08/probe.cir').read_text()
        for changed in [old.replace('setseed 73133','setseed 73134'),old.replace('0 0.2n\n','0 1n\n'),old+'\n'+NODES[0]]:
            with self.assertRaises(AssertionError):transform(changed,'c08')


if __name__=='__main__':unittest.main()
