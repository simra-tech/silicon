import tempfile
import unittest
from pathlib import Path
from prepare_joint586_tmax_halfns import matched_transform,source_gate,OLD,NEW,sha


class Tests(unittest.TestCase):
    def test_exact_inverse(self):
        old='setseed 77101\n'+OLD+'wrdata qualification/original/phase0.dat v(a)\n'
        changed=matched_transform(old,'original','new',77101)
        self.assertEqual(changed.replace(NEW,OLD).replace('qualification/new/phase0.dat','qualification/original/phase0.dat'),old)
    def test_wrong_step_seed_solver_rejected(self):
        old='setseed 77101\n'+OLD+'wrdata qualification/original/phase0.dat v(a)\n'
        for bad in [old.replace(OLD,NEW),old.replace('77101','77102'),old+'.options klu\n',old+'.nodeset v(a)=1\n']:
            with self.assertRaises(AssertionError):matched_transform(bad,'original','new',77101)
    def test_wrong_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'new';out.mkdir();old=root/'original';old.mkdir();leaf=old/'p52';leaf.mkdir()
            for directory in [old,out]:
                (directory/'sense.spice').write_text('original');(directory/'population_inventory.json').write_text('{}')
            prep=dict(source_hashes={'sense.spice':sha(old/'sense.spice')},inventory_sha256=sha(old/'population_inventory.json'))
            source_gate(out,leaf,prep);(out/'sense.spice').write_text('changed')
            with self.assertRaises(AssertionError):source_gate(out,leaf,prep)


if __name__=='__main__':unittest.main()
