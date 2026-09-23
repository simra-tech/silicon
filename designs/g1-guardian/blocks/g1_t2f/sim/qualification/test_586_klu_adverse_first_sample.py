import unittest
from prepare_586_klu_adverse_first_sample import klu_deck, reference_run, sample_deck, CONDITIONS


class SolverOnly(unittest.TestCase):
    def test_six_original_inputs_exact_inverse(self):
        body = (reference_run('fast')/'probe.cir').read_text()
        for label, *_ in CONDITIONS:
            sparse = sample_deck(body, 'fast', 75201, label)
            klu = klu_deck(sparse)
            self.assertEqual(klu.replace('\n.options klu\n', '\n'), sparse)
            self.assertEqual(klu.count('tran 5n 32u\n'), 1)
            self.assertEqual(klu.count('setseed 75201\n'), 1)

    def test_repeated_solver_insertion_rejected(self):
        with self.assertRaises(AssertionError):
            klu_deck('.options klu\n.control\n')


if __name__ == '__main__':
    unittest.main()
