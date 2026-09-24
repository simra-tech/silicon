"""Synthetic rejection controls for the new lineage, not a connectivity claim."""
import copy
import unittest
from audit_digital_parent_connectivity import sense_projection_lineage

class Lineage(unittest.TestCase):
    def setUp(self):
        self.meta=dict(status='passed isolated SENSE-only native hierarchy replacement',saved_roundtrip='passed',all_root_shapes_texts_properties_instances_and_die_held=True,all_other_native_hierarchies_held=True,transform='r90 *1 1031000,331000',original_parent_sha256='parent')
        self.projection=dict(status='passed exact 33-object hierarchy-only projection; stock LVS not run',GDS_sha256='parent',original_GDS_sha256='prior',object_count=33,via_cut_count=26,metal_landing_count=7,full_affected_layer_XOR=[dict(xor_dbu2=0) for _ in range(7)],all_other_cell_definitions_exact=True,all_root_text_and_nonoverlay_objects_exact=True,source_bytes_exact=True,inverse_saved_projection_all_definitions_exact=True)
    def test_positive(self):self.assertEqual(sense_projection_lineage(self.meta,self.projection),'prior')
    def test_reject_metadata_changes(self):
        for key,value in [('status','failed'),('saved_roundtrip','not run'),('all_root_shapes_texts_properties_instances_and_die_held',False),('all_other_native_hierarchies_held',False),('transform','r0'),('original_parent_sha256','wrong')]:
            m=copy.deepcopy(self.meta);m[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):sense_projection_lineage(m,self.projection)
    def test_reject_projection_changes(self):
        for key,value in [('object_count',32),('via_cut_count',25),('metal_landing_count',8),('inverse_saved_projection_all_definitions_exact',False),('full_affected_layer_XOR',[dict(xor_dbu2=1) for _ in range(7)]),('source_bytes_exact',False)]:
            p=copy.deepcopy(self.projection);p[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):sense_projection_lineage(self.meta,p)

if __name__=='__main__':unittest.main()
