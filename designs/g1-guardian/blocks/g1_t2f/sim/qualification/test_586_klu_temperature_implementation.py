import unittest
from run_586_klu_temperature import compare_wave
class Comparisons(unittest.TestCase):
    def wave(self,change=0):
        return ('time '+' '.join('v(n%d)'%i for i in range(12))+'\n'+'0 '+' '.join(['0']*12)+'\n'+'0.000032 '+str(1+change)+' '+' '.join(['0']*11)+'\n').encode()
    def test_exact(self):
        x=compare_wave(self.wave(),self.wave());self.assertTrue(x['decoded_bytes_exact']);self.assertTrue(x['numeric_rows_exact']);self.assertTrue(x['time_grid_exact'])
    def test_no_exact_waiver(self):
        x=compare_wave(self.wave(),self.wave(.000001));self.assertFalse(x['decoded_bytes_exact']);self.assertFalse(x['numeric_rows_exact']);self.assertTrue(x['time_grid_exact'])
if __name__=='__main__':unittest.main()
