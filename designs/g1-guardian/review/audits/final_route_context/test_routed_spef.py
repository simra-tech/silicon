import copy
from decimal import Decimal
import unittest
from audit_routed_spef import audit,rounding_radius,parse


def fixture():
    a,b,c,d=('A','X'),('B','Y'),('C','X'),('D','Y')
    values={
      'n1':dict(connections=[a,b],res=[(1,[a,b],'2')],caps=[(1,[a],'0.001'),(2,[a,c],'0.002')],total='0.003'),
      'n2':dict(connections=[c,d],res=[(1,[c,d],'3')],caps=[(1,[d],'0.001'),(2,[a,c],'0.002')],total='0.003')}
    inventory=dict(nets=[dict(net=n,endpoints=copy.deepcopy(v['connections']),status='routed')for n,v in values.items()])
    return values,inventory


class RoutedSpef(unittest.TestCase):
    specimen='''*SPEF "ieee 1481-1999"
*T_UNIT 1 NS
*C_UNIT 1 PF
*R_UNIT 1 OHM
*NAME_MAP
*1 net
*2 cell\\.a
*3 cell\\.b
*PORTS
P I
*D_NET *1 0.002
*CONN
*I *2:X I *D block
*I *3:Y O *D block
*CAP
1 *2:X 0.001
2 *3:Y 0.001
*RES
1 *2:X *3:Y 2
*END
'''

    def test_parser_positive_and_escape(self):
        n,p=parse(self.specimen)
        self.assertEqual(n['net']['connections'],[('cell.a','X'),('cell.b','Y')])
        self.assertEqual(p,[('P','I')])

    def test_parser_rejects_units(self):
        with self.assertRaises(AssertionError):parse(self.specimen.replace('*C_UNIT 1 PF','*C_UNIT 1 FF'))

    def test_parser_rejects_unfinished_net(self):
        with self.assertRaises(AssertionError):parse(self.specimen.replace('*END',''))

    def test_parser_rejects_negative_cap(self):
        with self.assertRaises(AssertionError):parse(self.specimen.replace('1 *2:X 0.001','1 *2:X -0.001'))

    def test_parser_rejects_duplicate_net(self):
        with self.assertRaises(AssertionError):parse(self.specimen+'*D_NET *1 0.002\n*END\n')

    def test_parser_rejects_nonfinite_resistance(self):
        with self.assertRaises(AssertionError):parse(self.specimen.replace('1 *2:X *3:Y 2','1 *2:X *3:Y NaN'))

    def test_reversed_local_coupling_order(self):
        n,i=fixture();self.assertEqual(audit(n,i)['paired_coupling_count'],1)

    def test_missing_terminal(self):
        n,i=fixture();n['n1']['connections'].pop()
        with self.assertRaises(AssertionError):audit(n,i)

    def test_missing_reciprocal(self):
        n,i=fixture();n['n2']['caps'].pop();n['n2']['total']='0.001'
        with self.assertRaises(AssertionError):audit(n,i)

    def test_wrong_grounded_node(self):
        n,i=fixture();n['n1']['caps'][0][1][0]=('wrong','node')
        with self.assertRaises(AssertionError):audit(n,i)

    def test_floating_resistor_island(self):
        n,i=fixture();n['n1']['res'].append((2,[('U','1'),('U','2')],'2'))
        with self.assertRaises(AssertionError):audit(n,i)

    def test_wrong_cap_sum(self):
        n,i=fixture();n['n1']['total']='0.100'
        with self.assertRaises(AssertionError):audit(n,i)

    def test_zero_print_is_not_half_pf_uncertainty(self):
        self.assertEqual(rounding_radius('0'),Decimal(0))
        self.assertEqual(rounding_radius('0.003'),Decimal('0.0005'))


if __name__=='__main__':unittest.main()
