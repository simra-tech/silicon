import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import audit_dac_coverage as audit


class CoverageContracts(unittest.TestCase):
    def test_duplicate_or_missing_code_rejected(self):
        self.assertTrue(audit.code_coverage([[0,125,172],[0,125,173]],172,174))
        self.assertFalse(audit.code_coverage([[0,125,172],[0,125,172]],172,174))
        self.assertFalse(audit.code_coverage([[0,125,172]],172,174))

    def exercise(self, changed=False):
        def fake_load(name):
            reference = name == 'reference'
            codes = [0,127,255] if reference or name == 'anchors' else [172,173]
            fp = [['parameter%d'%i,'0'] for i in range(31)]
            if changed and name == 'candidate':fp[0][1] = '1'
            rows = [[1 if reference else 0,125,c,.5+c*.001,.51+c*.001,1,1.5,-.001] for c in codes]
            result = {'seed':51001,'status':'passed','rows':rows,'fingerprints':[fp,fp] if reference else [fp],
                      'frozen_fingerprints':True,'wall_s':0}
            prov = {k:'synthetic' for k in ['model_hashes','image_id','ngspice','pdk_commit','solver']}
            prov['arguments']=['--codes',','.join(map(str,codes))]
            return Path(name),result,prov
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'audit.json'
            args = ['audit','--reference','reference','--reference-phase','1','--runs','candidate',
                    '--anchor-runs','anchors','--code-start','172','--code-stop','174','--output',str(output)]
            with patch.object(sys,'argv',args),patch.object(audit,'load',fake_load),patch.object(audit,'digest',lambda _: 'synthetic'),patch.object(audit,'circuit',lambda *args: 'synthetic'):
                with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as stop:audit.main()
            result=json.loads(output.read_text())
            self.assertEqual(stop.exception.code,1 if changed else 0)
            return result

    def test_valid_partial_scope_is_not_full256(self):
        result=self.exercise()
        self.assertEqual(result['status'],'passed')
        self.assertFalse(result['full256_completion'])

    def test_changed_sample_cannot_join_coverage(self):
        result=self.exercise(changed=True)
        self.assertEqual(result['status'],'failed')
        self.assertFalse(result['checks']['all_leaf_contracts'])


if __name__ == '__main__':unittest.main()
