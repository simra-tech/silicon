import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest
from run_joint586_adverse_staged import heldout_plan, collect_entries, adverse_deck, sha, SIM, REFERENCE, CONDITIONS
import run_joint586_adverse_calibration as serial


TREE = dict(corrected_codes=dict(soft=153, hard=204), fixed_residual_codes=dict(soft=135, hard=151))


class Staged(unittest.TestCase):
    def test_exact_original_sixty_order_codes_conditions(self):
        rows = heldout_plan(TREE, 10)
        expected = []
        for kind, key, values in [('guard','corrected_codes',[(.027,False,False),(.033,True,False),(.9*204*1.04/5300,True,False),(1.1*204*1.04/5300,True,True)]),
                                 ('residual','fixed_residual_codes',[(.0245,False,False),(.0255,True,True)])]:
            for condition in CONDITIONS:
                for shunt, soft, hard in values:
                    expected.append(dict(index=10+len(expected), codes=[TREE[key][k] for k in ['soft','hard']], shunt_V=shunt,
                        condition=list(condition), kind=kind, expected_decisions=dict(soft=soft,hard=hard)))
        self.assertEqual(rows, expected)
        self.assertEqual(len({r['index'] for r in rows}),60)

    def test_all_sixty_decks_each_corner_byte_identical_serial(self):
        original=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
        for corner,seed in [('slow',77101),('fast',78101)]:
            for r in heldout_plan(TREE,10):
                args=(original,REFERENCE,'staged-parity',seed,r['codes'],r['shunt_V'],r['condition'],corner)
                self.assertEqual(adverse_deck(*args),serial.adverse_deck(*args))

    def test_frozen_sampling_parameter_watchdog_bodies(self):
        old=ast.parse((SIM/'run_joint586_adverse_calibration.py').read_text())
        new=ast.parse((SIM/'run_joint586_adverse_staged.py').read_text())
        def calls(tree,name):
            return [ast.dump(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
        for name in ['run_bounded','phase_parameters','analyze_wave','archive_new_wave','read_group']:
            self.assertEqual(calls(old,name),calls(new,name),name)
        for name in ['calibration_deck','adverse_deck','qualification','check_pause']:
            a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name)
            b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(ast.dump(a),ast.dump(b),name)

    def fixture(self,out):
        rows=heldout_plan(TREE,10)
        # Deliberately complete backwards: assembler must use frozen ledger order.
        for row in reversed(rows):
            leaf=out/('p%02d'%row['index']);leaf.mkdir()
            (leaf/'probe.cir').write_text('deck'+str(row['index']))
            row['deck_sha256']=sha(leaf/'probe.cir')
            (leaf/'summary.json').write_text('{}')
            entry=dict(row,run=out.name+'/'+leaf.name,summary_sha256=sha(leaf/'summary.json'),status='failed' if row['index']==23 else 'passed')
            (leaf/'entry.json').write_text(json.dumps(entry))
        return dict(rows=rows)

    def test_out_of_order_completion_preserves_failed_leaf_and_fixed_order(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);plan=self.fixture(out);entries=collect_entries(out,plan)
            self.assertEqual([r['index'] for r in entries],list(range(10,70)))
            self.assertEqual([r['index'] for r in entries if r['status']=='failed'],[23])

    def test_missing_leaf_blocks_assembly(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);plan=self.fixture(out);(out/'p23/entry.json').unlink()
            with self.assertRaises(FileNotFoundError):collect_entries(out,plan)

    def test_mutated_input_blocks_assembly(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);plan=self.fixture(out);(out/'p23/probe.cir').write_text('changed')
            with self.assertRaises(AssertionError):collect_entries(out,plan)

    def test_atomic_directory_claim_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            leaf=Path(d)/'p10';leaf.mkdir()
            with self.assertRaises(FileExistsError):leaf.mkdir()

    def test_plan_does_not_mutate_calibration_tree(self):
        before=copy.deepcopy(TREE);rows=heldout_plan(TREE,10)
        rows[0]['codes'][0]=0
        self.assertEqual(TREE,before)


if __name__=='__main__':unittest.main()
