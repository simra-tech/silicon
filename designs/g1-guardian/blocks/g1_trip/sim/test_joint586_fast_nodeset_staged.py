import ast
import json
import unittest
from pathlib import Path
import run_joint586_adverse_staged as old
import run_joint586_fast_nodeset_staged as new


class FrozenMethod(unittest.TestCase):
    def test_all60_and_calibration_inputs_only_fixed_nodeset(self):
        original=(new.SIM/'qualification'/new.REFERENCE/'population_transient.cir').read_text()
        tree=dict(corrected_codes=dict(soft=153,hard=204),fixed_residual_codes=dict(soft=135,hard=151))
        rows=old.heldout_plan(tree,10)
        rows += [dict(condition=list(old.CONDITIONS[0]),codes=c,shunt_V=.025) for c in [[0,0],[255,255],[127,127]]]
        expected_line=None
        for row in rows:
            args=(original,new.REFERENCE,'nodeset-staged-test',78101,row['codes'],row['shunt_V'],row['condition'],'fast')
            before=old.adverse_deck(*args);after=new.adverse_deck(*args)
            lines=[line for line in after.splitlines(True) if line.startswith('.nodeset ')]
            self.assertEqual(len(lines),1)
            if expected_line is None:expected_line=lines[0]
            self.assertEqual(lines[0],expected_line)
            self.assertEqual(after.replace(lines[0],''),before)

    def test_original_heldout_plan_unchanged(self):
        tree=dict(corrected_codes=dict(soft=140,hard=210),fixed_residual_codes=dict(soft=125,hard=140))
        self.assertEqual(old.heldout_plan(tree,10),new.heldout_plan(tree,10))

    def test_existing_nodeset_rejected(self):
        with self.assertRaises(AssertionError):new.add_fixed_nodeset('.nodeset v(vref)=1\n.control\n')

    def test_probe_numerical_acceptance_ast_unchanged(self):
        def probe(module):
            tree=ast.parse(Path(module.__file__).read_text())
            return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='probe')
        self.assertEqual(ast.dump(probe(old)),ast.dump(probe(new)))

    def test_json_provenance_conditions_roundtrip(self):
        actual=[list(c) for c in new.CONDITIONS]
        self.assertEqual(actual,json.loads(json.dumps(actual)))
        self.assertEqual(actual,[list(c) for c in old.CONDITIONS])

    def test_qualified14_gate_rejects_slow_inheritance(self):
        audit=new.SIM/'qualification/joint586-fast-nodeset-rescue-audit-20260923-b.json'
        with self.assertRaises(AssertionError):new.qualification(audit,audit,'slow')


if __name__=='__main__':unittest.main()
