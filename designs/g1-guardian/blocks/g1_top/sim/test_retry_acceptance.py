"""Synthetic negative controls for the retry/readback acceptance checker."""
import copy
import unittest
from unittest.mock import patch

from check_campaign import check_retry, decode_serial


class RetryAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.cols = ['time'] + [f'v({n})' for n in
            ['gate', 'dig_trip', 'inrush_active', 'tripped', 'fault_n', 'iprof']] + ['i(vim)']
        self.t1 = 41e-6
        self.tr = self.t1 + 8193 / 8.994e6
        self.t2 = self.tr + 1.5e-6
        self.rows = [
            [38e-6, 3.3, 0, 0, 0, 3.3, 1, 1],
            [39e-6, 3.3, 0, 0, 0, 3.3, 1, 1],
            [self.tr + .5e-6, 3.3, 0, 0, 0, 3.3, 1.8, 1.8],
            [1000e-6, 0, 1.2, 0, 1.2, 0, 1.8, 0],
            [1140e-6, 0, 1.2, 0, 1.2, 0, 1.8, 0],
        ]
        self.sc = ['time', 'v(dig_trip)']
        self.sr = [[0, 0], [40.5e-6, 0]]
        for t, before, after in [(self.t1, 0, 1.2), (self.tr, 1.2, 0), (self.t2, 0, 1.2)]:
            self.sr += [[t - .5e-9, before], [t + .5e-9, after]]
        self.sr += [[1140e-6, 1.2]]
        self.frames = [dict(command=c, data=d) for c, d in
            [(8, 0), (3, 200), (11, 7), (9, 0), (10, 1),
             (0x8D, 0xA5), (0x8E, 0x18), (0x8F, 2), (0x90, 0)]]

    def evaluate(self):
        with patch('check_campaign.decode_serial', return_value=self.frames):
            return check_retry(self.cols, self.rows, self.sc, self.sr)[0]

    def test_declared_sequence_passes(self):
        self.assertTrue(all(self.evaluate().values()))

    def test_wrong_counter_rejected(self):
        self.frames[-2]['data'] = 1
        self.assertFalse(self.evaluate()['serial_config_status_retry_count'])

    def test_no_load_reenable_rejected(self):
        self.rows[2][-1] = 0
        self.assertFalse(self.evaluate()['gate_and_load_reenabled'])

    def test_short_hold_rejected(self):
        for row in self.sr[4:]:
            row[0] -= 10e-6
        self.sr[-1][0] = 1140e-6
        self.assertFalse(self.evaluate()['hold_8192cycles'])

    def test_extra_retry_rejected(self):
        self.sr[-1:-1] = [[1050e-6, 1.2], [1050.001e-6, 0],
                          [1060e-6, 0], [1060.001e-6, 1.2]]
        self.assertFalse(self.evaluate()['two_trips_one_retry'])

    def test_serial_decoder_read_and_write(self):
        cols = ['time', 'v(sclk_pad)', 'v(sdi_pad)', 'v(sdo)']
        rows = [[0, 0, 0, 0]]
        frames = [(3, 200), (0x8F, 2)]
        for command, data in frames:
            command_bits = [(command >> n) & 1 for n in range(7, -1, -1)]
            data_bits = [(data >> n) & 1 for n in range(7, -1, -1)]
            inputs = command_bits + ([0] * 16 if command & 128 else data_bits)
            outputs = [0] * 16 + data_bits if command & 128 else [0] * 16
            for inp, out in zip(inputs, outputs):
                t = rows[-1][0] + 100e-9
                rows += [[t, 0, inp * 3.3, out * 1.2],
                         [t + 100e-9, 3.3, inp * 3.3, out * 1.2],
                         [t + 120e-9, 3.3, inp * 3.3, out * 1.2],
                         [t + 200e-9, 0, inp * 3.3, out * 1.2]]
        self.assertEqual(decode_serial(cols, rows),
                         [dict(command=c, data=d) for c, d in frames])
        invalid = copy.deepcopy(rows)
        invalid[3][3] = .6
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            decode_serial(cols, invalid)


if __name__ == '__main__':
    unittest.main()
