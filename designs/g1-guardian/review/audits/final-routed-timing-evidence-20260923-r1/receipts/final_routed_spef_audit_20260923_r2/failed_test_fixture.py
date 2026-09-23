import copy
from decimal import Decimal
import unittest
from audit_routed_spef import audit,rounding_radius


def fixture():
    a,b,c,d=('A','X'),('B','Y'),('C','X'),('D','Y')
    values={
      'n1':dict(connections=[a,b],res=[(1,[a,b],'2')],caps=[(1,[a],'0.001'),(2,[a,c],'0.002')],total='0.003'),
      'n2':dict(connections=[c,d],res=[(1,[c,d],'3')],caps=[(1,[d],'0.001'),(2,[a,c],'0.002')],total='0.003')}
    inventory=dict(nets=[dict(net=n,endpoints=v['connections'],status='routed')for n,v in values.items()])
    return values,inventory


class RoutedSpef(unittest.TestCase):
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
