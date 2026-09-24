import unittest
from audit_manual_pad_variant import inverse

class InverseTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'Xtap a bulk ptap1 R=12\n'
        self.edit=[dict(line=1,before='Xtap a bulk ptap1 R=15\n',after=self.raw.decode())]
    def test_exact_inverse(self):self.assertEqual(inverse(self.raw,self.edit,1),self.edit[0]['before'].encode())
    def test_node_change_rejected(self):
        self.edit[0]['before']='Xtap a iovss ptap1 R=15\n'
        with self.assertRaises(AssertionError):inverse(self.raw,self.edit,1)
    def test_omitted_edit_rejected(self):
        with self.assertRaises(AssertionError):inverse(self.raw,[],1)
    def test_duplicate_rejected(self):
        with self.assertRaises(AssertionError):inverse(self.raw,self.edit*2,2)
if __name__=='__main__':unittest.main()
