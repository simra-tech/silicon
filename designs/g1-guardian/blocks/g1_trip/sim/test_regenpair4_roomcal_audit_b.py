import copy
import json
import unittest
from audit_regenpair4_roomcal_b import serialized_tree,replay


class Controls(unittest.TestCase):
    def records(self):
        records=[]
        for i in range(10):
            codes=[0,0] if i==0 else [255,255] if i==1 else replay(records)['next_required_codes']
            records.append(dict(run='c%d'%i,codes=codes,status='passed',decisions={k:c<n for k,c,n in zip(['soft','hard'],codes,[132,145])}))
        return records

    def test_exact_json_representation(self):
        records=self.records();raw=replay(records);saved=json.loads(json.dumps(raw))
        self.assertNotEqual(raw,saved)
        self.assertEqual(serialized_tree(records),saved)
        self.assertEqual(serialized_tree(records)['all_attempts'],records)

    def test_changed_value_order_failed_status_not_normalized(self):
        records=self.records();saved=json.loads(json.dumps(replay(records)))
        for mutate in ['code','order','failure']:
            bad=copy.deepcopy(records)
            if mutate=='code':bad[-1]['codes'][0]+=2
            elif mutate=='order':bad.reverse()
            else:bad[-1]['status']='failed'
            self.assertNotEqual(serialized_tree(bad),saved)


if __name__=='__main__':unittest.main()
