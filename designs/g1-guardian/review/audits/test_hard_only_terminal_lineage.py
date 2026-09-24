"""Reject incomplete clone provenance; connectivity still requires fresh extraction."""
import copy
import unittest
from audit_digital_parent_connectivity import hard_only_lineage

class Controls(unittest.TestCase):
    def setUp(self):
        self.meta=dict(status='passed isolated native preparation and strict comparator source checks; fullparent DRC not yet run',GDS_sha256='new',source_parent_sha256='old')
        pair=[dict(kind='nmos',ng=1,w=3,l=.13),dict(kind='nmos',ng=1,w=6,l=.26)]
        self.geometry=dict(output_sha256='new',input_sha256='old',pins_exact=True,all_other_generated_devices_exact=True,changed_devices=[pair,copy.deepcopy(pair)])
        self.audit=dict(status='passed isolated hard comparator DRC main/maximal and strict two-sided LVS',circuits=[dict(pins=7,nets=16,devices=25,subcircuits=0)],all_original_native_hierarchy_checks=dict(all_original_cells=293,all_original_direct_shapes_texts_exact=True,only_instance_change='hard comparator at208000,162000; root global overlays exact'))
    def test_valid(self):self.assertEqual(hard_only_lineage(self.meta,self.geometry,self.audit),'old')
    def test_reject_source_or_pin_changes(self):
        for key,value in [('pins_exact',False),('all_other_generated_devices_exact',False),('input_sha256','wrong'),('output_sha256','wrong'),('changed_devices',[])]:
            geometry=copy.deepcopy(self.geometry);geometry[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):hard_only_lineage(self.meta,geometry,self.audit)
    def test_reject_wrong_device(self):
        geometry=copy.deepcopy(self.geometry);geometry['changed_devices'][0][1]['l']=.13
        with self.assertRaises(AssertionError):hard_only_lineage(self.meta,geometry,self.audit)
    def test_reject_missing_or_different_native_proof(self):
        for key,value in [('all_original_cells',292),('all_original_direct_shapes_texts_exact',False),('only_instance_change','soft comparator')]:
            audit=copy.deepcopy(self.audit);audit['all_original_native_hierarchy_checks'][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):hard_only_lineage(self.meta,self.geometry,audit)

if __name__=='__main__':unittest.main()
