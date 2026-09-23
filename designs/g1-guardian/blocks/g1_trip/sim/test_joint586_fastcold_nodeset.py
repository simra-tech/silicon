import unittest
from prepare_joint586_fastcold_nodeset import ORIGINAL,NODES,guesses,transform
from analyze_joint586_fastcold_initialization import initial_nodes,hbt_rows

class NodesetTests(unittest.TestCase):
    def setUp(self):
        self.original=(ORIGINAL/'population_transient.cir').read_text()
        self.values=guesses((ORIGINAL/'run.log').read_text())

    def test_three_exact_inverse_transforms(self):
        for label in ['sparse','sparse_nodeset','klu_nodeset']:
            deck,audit=transform(self.original,'test-op',label,self.values)
            self.assertTrue(audit['exact_inverse_restores_original'])
            self.assertEqual(deck.count('\nop\n'),1)
            self.assertFalse(any(l.startswith(('tran ','meas tran ')) for l in deck.splitlines()))
            self.assertEqual(deck.count('print @'),self.original.count('print @'))

    def test_paired_solver_only_diff(self):
        a,_=transform(self.original,'test-op','sparse_nodeset',self.values)
        b,_=transform(self.original,'test-op','klu_nodeset',self.values)
        self.assertEqual(b.replace('.options klu\n',''),a)

    def test_unknown_or_reordered_nodes_rejected(self):
        with self.assertRaises(AssertionError):transform(self.original,'test-op','sparse',dict(reversed(list(self.values.items()))))
        values=dict(self.values);values['xs.xref#si']='0'
        with self.assertRaises(AssertionError):transform(self.original,'test-op','klu_nodeset',values)

    def test_initial_table_separator_and_grounded_dummy(self):
        log=(ORIGINAL/'run.log').read_text();nodes=initial_nodes(log)
        rows=hbt_rows((ORIGINAL/'bgr.spice').read_text(),nodes)
        q55,=[r for r in rows if r['source_id']=='xq55']
        self.assertTrue(q55['grounded_dummy']);self.assertEqual(q55['VCE_V'],0)
        self.assertEqual(len(rows),301)

if __name__=='__main__':unittest.main()
