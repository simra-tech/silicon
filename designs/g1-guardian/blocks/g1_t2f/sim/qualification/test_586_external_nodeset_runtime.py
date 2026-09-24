import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from run_586_external_nodeset_control import analyze
from audit_586_external_nodeset_controls import pair


class RuntimeTests(unittest.TestCase):
    def test_failed_baseline_never_promoted(self):
        self.assertEqual(pair(None,dict(status='passed OP/full3180 evidence'))['status'],'not run; missing or failed comparison arm')
        self.assertEqual(pair(dict(status='failed'),dict(status='passed OP/full3180 evidence'))['status'],'not run; missing or failed comparison arm')

    def fixture(self,directory):
        out=Path(directory)
        vectors=['v(fout)','v(vref)','i(vdd)','i(vdd12)','v(xt2f.cap1)','v(xt2f.cap2)',
            'v(xt2f.ca1)','v(xt2f.tail1)','v(xt2f.cb1)','v(xt2f.ca2)','v(xt2f.tail2)','v(xt2f.cb2)',
            'v(pbias)','v(pcasc)','v(vbe)','v(dvbe)']
        (out/'probe.cir').write_text('wrdata op.dat '+' '.join(vectors)+'\n')
        (out/'op.dat').write_text('opscale '+' '.join(vectors)+'\n'+' '.join(['0']*17)+'\n')
        (out/'run.log').write_text('Using SPARSE 1.3 as Direct Linear Solver\nPHASE0_BEGIN\nPHASE0_END\n')
        vector=[['@x%d[p]'%i,'1.0'] for i in range(3180)]
        packet=dict(groups={'TEST':[x[0] for x in vector]},expected_parameters={'TEST':vector})
        return out,packet,dict(label='sparse-original',solver='sparse'),dict(status='completed',returncode=0),vector

    def test_valid_named_finite_vector(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,packet,case,state,vector=self.fixture(tmp)
            with patch('run_586_external_nodeset_control.read_group',return_value=vector):result=analyze(out,packet,case,state)
            self.assertEqual(result['status'],'passed OP/full3180 evidence')

    def test_zero_exit_abort_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,packet,case,state,vector=self.fixture(tmp)
            (out/'run.log').write_text((out/'run.log').read_text()+'analysis aborted\n')
            result=analyze(out,packet,case,state);self.assertEqual(result['status'],'failed')

    def test_wrong_header_and_timeout_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,packet,case,state,vector=self.fixture(tmp)
            (out/'op.dat').write_text((out/'op.dat').read_text().replace('v(vref)','v(wrong)'))
            with patch('run_586_external_nodeset_control.read_group',return_value=vector):result=analyze(out,packet,case,state)
            self.assertEqual(result['status'],'failed')
            state['status']='timeout';self.assertEqual(analyze(out,packet,case,state)['status'],'failed')

    def test_mismatch_and_nonfinite_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out,packet,case,state,vector=self.fixture(tmp);bad=[list(row) for row in vector];bad[-1][1]='2.0'
            with patch('run_586_external_nodeset_control.read_group',return_value=bad):result=analyze(out,packet,case,state)
            self.assertEqual(result['status'],'failed')
            (out/'op.dat').write_text((out/'op.dat').read_text().replace('\n0 ','\nnan ',1))
            with patch('run_586_external_nodeset_control.read_group',return_value=vector):result=analyze(out,packet,case,state)
            self.assertEqual(result['status'],'failed')


if __name__=='__main__':unittest.main()
