#!/usr/bin/env python3
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import klayout.db as k
from replace_analog_pair_candidate import protected, structural_digest, root_without, main, sha


class Controls(unittest.TestCase):
    def fixture(self):
        layout = k.Layout(); layout.dbu = .001
        top, a, b, shared = [layout.create_cell(n) for n in ['TOP','A','B','SHARED']]
        for cell in [a, b, shared]:
            top.insert(k.CellInstArray(cell.cell_index(), k.Trans()))
        a.insert(k.CellInstArray(shared.cell_index(), k.Trans(100,0)))
        shared.shapes(layout.layer(8,0)).insert(k.Box(0,0,100,100))
        shared.shapes(layout.layer(8,25)).insert(k.Text('INTERNAL', k.Trans()))
        return layout, top, a, b, shared

    def test_two_targets_and_shared_protection(self):
        layout, top, a, b, shared = self.fixture()
        self.assertEqual(set(protected(top, {'A','B'})), {'TOP','SHARED'})

    def test_shared_mutation_rejected(self):
        layout, top, a, b, shared = self.fixture()
        before = protected(top, {'A','B'})
        shared.shapes(layout.layer(8,0)).insert(k.Box(0,0,200,100))
        self.assertNotEqual(before, protected(top, {'A','B'}))

    def test_instance_transform_rejected(self):
        layout, top, a, b, shared = self.fixture()
        before = protected(top, {'A','B'})
        next(top.each_inst()).trans = k.Trans(10,0)
        self.assertNotEqual(before, protected(top, {'A','B'}))

    def test_property_change_rejected(self):
        layout, top, a, b, shared = self.fixture()
        before = protected(top, {'A','B'})
        shared.set_property('intent', 'changed')
        self.assertNotEqual(before, protected(top, {'A','B'}))

    def test_copy_alias_preserves_hierarchy(self):
        layout, top, a, b, shared = self.fixture()
        copy = k.Layout(); copy.dbu = .001
        cell = copy.create_cell('DIFFERENT_NAME'); cell.copy_tree(a)
        self.assertEqual(structural_digest(a), structural_digest(cell))

    def test_flattened_internal_pin_scope_rejected(self):
        layout, top, a, b, shared = self.fixture()
        before = structural_digest(a)
        a.flatten(-1)
        self.assertNotEqual(before, structural_digest(a))

    def test_internal_label_rejected(self):
        layout, top, a, b, shared = self.fixture()
        before = structural_digest(a)
        shared.shapes(layout.layer(8,25)).insert(k.Text('WRONG_NET', k.Trans()))
        self.assertNotEqual(before, structural_digest(a))

    def test_only_declared_added_instance_excluded(self):
        layout, top, a, b, shared = self.fixture()
        before = root_without(top, set())
        added = layout.create_cell('ADDED')
        top.insert(k.CellInstArray(added.cell_index(), k.Trans(50,0)))
        self.assertEqual(before, root_without(top, {'ADDED'}))
        next(top.each_inst()).trans = k.Trans(20,0)
        self.assertNotEqual(before, root_without(top, {'ADDED'}))

    def pair_fixture(self, directory):
        def view(name, cell_name, boxes):
            ly = k.Layout(); ly.dbu = .001; top = ly.create_cell(cell_name)
            for box in boxes: top.shapes(ly.layer(8,0)).insert(k.Box(*box))
            path = directory/name; ly.write(str(path))
            return ly, top, dict(path=str(path), cell=cell_name, sha256=sha(path))
        _, _, old_bgr = view('old_bgr.gds', 'g1_bgr', [(0,0,100,100),(100,0,200,100)])
        _, _, new_bgr = view('new_bgr.gds', 'g1_bgr', [(0,0,100,100),(100,0,200,100),(200,0,300,100)])
        _, _, overlay = view('cuts.gds', 'CUTS', [(200,0,300,100)])
        old, ot, old_sense = view('old_sense.gds', 'SENSE', [(0,0,100,100)])
        new, nt, new_sense = view('new_sense.gds', 'SENSE', [(0,0,100,100),(20,20,30,30)])
        # Actual physical change stays in the old bbox and contains hierarchy.
        child = new.create_cell('INNER'); child.shapes(new.layer(8,25)).insert(k.Text('INTERNAL',k.Trans()))
        nt.insert(k.CellInstArray(child.cell_index(),k.Trans(5,5)))
        new.write(new_sense['path']); new_sense['sha256'] = sha(new_sense['path'])
        ly, top, parent = view('parent.gds','TOP',[(0,0,1414000,1414000)])
        bgr = ly.create_cell('g1_bgr_candidate'); bgr.shapes(ly.layer(8,0)).insert(k.Box(0,0,100,100))
        supply = ly.create_cell('bgr_supply_additive_context_candidate')
        supply.shapes(ly.layer(8,0)).insert(k.Box(331100,732000,331200,732100))
        sense = ly.create_cell('g1_sense_candidate'); sense.copy_tree(ot)
        top.insert(k.CellInstArray(bgr.cell_index(),k.Trans(331000,732000)))
        top.insert(k.CellInstArray(supply.cell_index(),k.Trans()))
        top.insert(k.CellInstArray(sense.cell_index(),k.Trans(k.Trans.R90,1031000,331000)))
        ly.write(parent['path']); parent['sha256'] = sha(parent['path'])
        proof = directory/'synthetic_proof.json'; proof.write_text(json.dumps(dict(status='passed synthetic fixture')))
        predicates = [dict(path=str(proof),sha256=sha(proof),equals=[[['status'],'passed synthetic fixture']])]
        contract = dict(status='frozen preparation only; no source adoption',parent=dict(gds=parent,top_cell='TOP'),
                        replacements=[dict(role='SENSE',old_gds=old_sense,new_gds=new_sense,target_cell='g1_sense_candidate',
                            transform='r90 *1 1031000,331000',proofs=predicates)],
                        bgr_additive=dict(old_effective=old_bgr,new_effective=new_bgr,overlay=overlay,proofs=predicates))
        return contract

    def execute_pair(self, directory, contract):
        manifest = directory/'contract.json'; manifest.write_text(json.dumps(contract))
        with patch('sys.argv',['fixture','--manifest',str(manifest),'--manifest-sha256',sha(manifest),'--output',str(directory/'output')]):
            main()

    def test_complete_pair_saved_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); self.execute_pair(directory, self.pair_fixture(directory))
            result = json.loads((directory/'output/analysis.json').read_text())
            self.assertEqual(result['status'],'passed isolated analog-pair hierarchy replacement')

    def test_wrong_declared_transform_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); contract = self.pair_fixture(directory)
            contract['replacements'][0]['transform'] = 'r0 *1 1031000,331000'
            with self.assertRaises(AssertionError): self.execute_pair(directory, contract)

    def test_duplicate_supply_overlay_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp); contract = self.pair_fixture(directory)
            contract['bgr_additive']['overlay'] = contract['bgr_additive']['old_effective']
            with self.assertRaises(AssertionError): self.execute_pair(directory, contract)


if __name__ == '__main__':
    unittest.main()
