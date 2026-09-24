from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from prepare_dac586_dc_controls import ADDED
from run_dac586_dc_control import analyze,table


class RuntimeTests(unittest.TestCase):
    def setup_fixture(self,temp):
        root=Path(temp);ref=root/'qualification/ref';ref.mkdir(parents=True);out=root/'candidate';out.mkdir()
        header=['clk']+['v(n%d)'%i for i in range(9)]+['i(vdda)','i(vdd)']
        original=[0.]*12;values=original+[1.2*((127>>i)&1) for j in range(2) for i in range(8)]+[0.,0.]
        (ref/'op0.dat').write_text(' '.join(header)+'\n'+' '.join(map(str,original))+'\n')
        (out/'op0.dat').write_text(' '.join(header+ADDED)+'\n'+' '.join(map(str,values))+'\n')
        (out/'run.log').write_text('Using SPARSE 1.3 as Direct Linear Solver\nPOPULATION_OP_END\n')
        vector=[['@x%d[p]'%i,'1.0'] for i in range(11512)]
        prep=dict(method='behavioral-bit OP',reference_static='ref',temperatures_C=[25],expected_full_parameters=vector,
            groups=dict(NON_BGR=[k for k,v in vector],BGR=[],LEGACY27=[k for k,v in vector[:27]]),codes=[127,127])
        def groups(log,tag,keys):return [[key,'1.0'] for key in keys]
        state=dict(status='completed',returncode=0,wall_s=1)
        return root,out,prep,state,groups

    def test_valid_and_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out,prep,state,groups=self.setup_fixture(temp)
            with patch('run_dac586_dc_control.SIM',root),patch('run_dac586_dc_control.read_group',side_effect=groups):result=analyze(out,prep,state)
            self.assertTrue(result['status'].startswith('passed conditional'));self.assertEqual(result['strict_static_equivalence'],'passed')

    def test_small_difference_never_relabels_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out,prep,state,groups=self.setup_fixture(temp)
            lines=(out/'op0.dat').read_text().splitlines();values=lines[1].split();values[1]='1e-10'
            (out/'op0.dat').write_text(lines[0]+'\n'+' '.join(values)+'\n')
            with patch('run_dac586_dc_control.SIM',root),patch('run_dac586_dc_control.read_group',side_effect=groups):result=analyze(out,prep,state)
            self.assertTrue(result['status'].startswith('passed conditional'));self.assertEqual(result['strict_static_equivalence'],'failed')

    def test_large_difference_and_wrong_bit_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out,prep,state,groups=self.setup_fixture(temp)
            lines=(out/'op0.dat').read_text().splitlines();values=lines[1].split();values[1]='1e-6'
            (out/'op0.dat').write_text(lines[0]+'\n'+' '.join(values)+'\n')
            with patch('run_dac586_dc_control.SIM',root),patch('run_dac586_dc_control.read_group',side_effect=groups):result=analyze(out,prep,state)
            self.assertEqual(result['status'],'failed method control')
            values[1]='0';values[12]='1.1999999999';(out/'op0.dat').write_text(lines[0]+'\n'+' '.join(values)+'\n')
            with patch('run_dac586_dc_control.SIM',root),patch('run_dac586_dc_control.read_group',side_effect=groups):result=analyze(out,prep,state)
            self.assertEqual(result['status'],'failed method control')

    def test_zero_exit_abort_and_timeout_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out,prep,state,groups=self.setup_fixture(temp)
            (out/'run.log').write_text((out/'run.log').read_text()+'analysis aborted\n')
            self.assertEqual(analyze(out,prep,state)['status'],'failed method control')
            state['status']='timeout';self.assertEqual(analyze(out,prep,state)['status'],'failed method control')

    def test_header_and_nonfinite_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'data';path.write_text('wrong\n0\n')
            with self.assertRaises(AssertionError):table(path,['right'],1)
            path.write_text('right\nnan\n')
            with self.assertRaises(AssertionError):table(path,['right'],1)


if __name__=='__main__':unittest.main()
