import copy
import unittest
from check_stream import evaluate

class StreamAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.cols=['time']+[f'v({n})' for n in ['gate','inrush_active','dig_trip','en_core','tripped','cause1','cause0','fault_n','iprof']]+['i(vim)']+[f'v({p}{i})' for p in ['soft','hard'] for i in range(8)]
        def row(t,trip):
            return [t,0 if trip else 3.3,0,1.2 if trip else 0,1.2,1.2 if trip else 0,1.2 if trip else 0,0,0 if trip else 3.3,1.8 if t>=16e-6 else 1,0 if trip else 1]+[1.2 if c&(1<<i) else 0 for c in [153,200] for i in range(8)]
        self.rows=[row(0,False),row(15e-6,False),row(16e-6,False),row(17e-6,True),row(28e-6,True)]
    def test_complete_fixture(self):
        self.assertEqual(evaluate(self.cols,self.rows,'passed')['status'],'passed')
    def test_missing_endpoint_and_partial(self):
        self.assertEqual(evaluate(self.cols,self.rows[:-1],'passed')['status'],'failed')
        self.assertEqual(evaluate(self.cols,self.rows,'not run to completion')['status'],'not run to completion')
    def test_wrong_configuration_cause_and_rearming(self):
        for row,col,value in [(1,'v(hard0)',1.2),(-1,'v(cause1)',0),(-1,'v(gate)',3.3),(1,'v(gate)',0)]:
            rows=copy.deepcopy(self.rows);rows[row][self.cols.index(col)]=value
            self.assertEqual(evaluate(self.cols,rows,'passed')['status'],'failed')

if __name__=='__main__':
    unittest.main()
