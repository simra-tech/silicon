import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import check_campaign
import test_check_stream
import run_top
import compare_runtime

class CampaignCompletenessTests(unittest.TestCase):
    def test_runtime_comparison_does_not_extend_partial_trace(self):
        rows=[[0,0],[1,2]]
        self.assertEqual(compare_runtime.interpolate(rows,[0,1],.5,1),1)
        with self.assertRaises(ValueError):compare_runtime.interpolate(rows,[0,1],2,1)

    def test_missing_export_rejected_before_launch(self):
        deck='.save v(gate)\n+ v(en_core)\n.control\nwrdata state.txt v(en_core) v(sdo)\n.endc\n'
        with self.assertRaisesRegex(ValueError,'sdo'):run_top.validate_exports(deck)
        run_top.validate_exports(deck.replace('+ v(en_core)','+ v(en_core) v(sdo)'))

    def test_required_state_and_clean_log(self):
        fixture=test_check_stream.StreamAcceptanceTests();fixture.setUp()
        fixture.cols.append('v(fast_en)')
        for row in fixture.rows:row.append(0)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);here=root/'sim';(here/'logs').mkdir(parents=True)
            build=root/'build/g1_top';build.mkdir(parents=True)
            options=dict(cases=['c_mid'],analysis='functional',timeline='compact',tstop=28)
            (here/'logs/check.json').write_text(json.dumps(dict(options=options,status='completed')))
            log=here/'logs/check.log';log.write_text('simulation complete\n')
            text=' '.join(fixture.cols)+'\n'+'\n'.join(' '.join(map(str,r)) for r in fixture.rows)+'\n'
            (build/'waves_check.txt').write_text(text)
            with patch.object(check_campaign,'ROOT',root),patch.object(check_campaign,'HERE',here):
                result=check_campaign.check('check')
                self.assertEqual(result['status'],'failed')
                self.assertFalse(result['tests']['required_state_waveform'])
                (build/'state_check.txt').write_text(text)
                self.assertEqual(check_campaign.check('check')['status'],'passed')
                log.write_text('Error: no such vector fast_en\n')
                result=check_campaign.check('check')
                self.assertEqual(result['status'],'failed')
                self.assertFalse(result['tests']['solver_log_clean'])

    def test_short_pulse_requires_exercised_comparator_and_correct_mask(self):
        cols=['time']+['v('+n+')' for n in ['gate','dig_trip','tripped','fault_n','iprof','cmp_hard','inrush_active']]+['i(vim)']
        rows=[[t*1e-6,3.3,0,0,3.3,1.8 if t==30.1 else 1,1.2 if t==30.1 else 0,0,1.8 if t==30.1 else 1] for t in [28,29,30,30.1,34,36,44]]
        sc=['time','v(fast_en)','v(cause0)','v(cause1)','v(inrush_active)']+[f'v({p}{i})' for p in ['soft','hard'] for i in range(8)]
        bits=[1.2 if n&(1<<i) else 0 for n in [153,200] for i in range(8)]
        sr=[[t*1e-6,0,0,0,0]+bits for t in [28,44]]
        tests,_=check_campaign.check_transitions(cols,rows,sc,sr,'hard_pulse')
        self.assertTrue(all(tests.values()))
        rows[3][6]=0
        tests,_=check_campaign.check_transitions(cols,rows,sc,sr,'hard_pulse')
        self.assertFalse(tests['hard_comparator_exercised'])
        rows[3][6]=1.2;rows[3][7]=1.2
        tests,_=check_campaign.check_transitions(cols,rows,sc,sr,'hard_pulse')
        self.assertFalse(tests['unmasked'])

if __name__=='__main__':unittest.main()
