#!/usr/bin/env python3
"""Offline tests of g1_host.py against DummyTransport (a register-file model
written from G1_REGISTER_MAP.md 1.2). These test the host logic only; they are
not evidence about silicon. Run: python3 -m unittest -v test_g1_host
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import g1_host as h  # noqa: E402


def make(version=h.VERSION_R3, **kw):
    t = h.DummyTransport(version=version, **kw)
    t.set_en(True)
    t.idle(100e-6)
    inhibit_log = []

    def inhibit(asserted):
        inhibit_log.append(asserted)
    g = h.G1(t, inhibit=inhibit)
    g.set_inhibit(True)
    return t, g, inhibit_log


class Protocol(unittest.TestCase):
    def test_frames_and_identify(self):
        t, g, _ = make()
        info = g.identify()
        self.assertEqual(info["CHIP_ID"], 0x47)
        self.assertEqual(info["VERSION"], 0x12)
        reads = [f for f in t.frames if f[1] == "R"]
        self.assertEqual([f[2] for f in reads[:2]], [0x00, 0x01])
        self.assertEqual(t.violations, [])

    def test_idle_before_every_frame(self):
        t, g, _ = make()
        g.identify()
        g.write("HARD_N", 6)
        g.dump()
        self.assertEqual(t.violations, [])
        # >= 128 cycles even at the fastest simulated clock (12.43 MHz)
        self.assertGreaterEqual(g.idle_s * h.F_OSC_SIM_RANGE_HZ[1], 128 * 1.3)
        self.assertGreaterEqual(t.min_idle_cycles, 128)

    def test_fallback_version(self):
        t, g, _ = make(version=h.VERSION_R2)
        with self.assertRaises(h.G1Error):
            g.identify()
        self.assertEqual(g.identify(require_version=None)["VERSION"], 0x11)

    def test_readback_and_guards(self):
        t, g, _ = make()
        g.identify()
        with self.assertRaises(h.G1Error):
            g.write("STATUS", 1)            # RO
        with self.assertRaises(h.G1Error):
            g.write("SOFT_CFG", 0x10)       # reserved bit
        with self.assertRaises(h.G1SafetyError):
            g.write("OSC_CTRL", 0x08)       # OSC_EN = 0
        with self.assertRaises(h.G1SafetyError):
            g.write("TEMP_CTRL", 0x05)      # BGR_R4
        with self.assertRaises(h.G1SafetyError):
            g.write("MODE", 0x0B)           # TRIP_SET_SEL
        g.write_osc_trim(7)
        self.assertEqual(g.read("OSC_CTRL"), 0x17)

    def test_readback_mismatch_raises(self):
        t, g, _ = make()
        g.identify()
        orig = t._write_reg
        t._write_reg = lambda a, d: orig(a, d ^ 0x01)   # corrupt writes
        with self.assertRaises(h.G1VerifyError):
            g.write("HARD_N", 4)


class SafetyWrites(unittest.TestCase):
    def test_soft_time_r3_order_and_atomic(self):
        t, g, _ = make()
        g.identify()
        g.write_soft_time(0x030D)
        writes = [(a, d) for (_t, k, a, d) in t.frames if k == "W"]
        self.assertEqual(writes[-2:], [(0x05, 0x03), (0x04, 0x0D)])   # H then L
        self.assertEqual(g.read16("SOFT_TIME_L"), 0x030D)

    def test_soft_time_r2_clears_soft_en(self):
        t, g, _ = make(version=h.VERSION_R2)
        g.identify(require_version=None)
        g.write_soft_time(0x0100)
        modes = [d for (_t, k, a, d) in t.frames if k == "W" and a == h.ADDR["MODE"]]
        self.assertEqual(modes, [0x02, 0x03])     # SOFT_EN cleared, then restored
        self.assertEqual(g.read16("SOFT_TIME_L"), 0x0100)

    def test_inrush_requires_inhibit(self):
        t, g, _ = make()
        g.identify()
        g.set_inhibit(False)
        with self.assertRaises(h.G1SafetyError):
            g.write_inrush(0x14)
        with self.assertRaises(h.G1SafetyError):
            g.write("INRUSH", 0x14)
        g.set_inhibit(True)
        g.write_inrush(0x14)
        self.assertEqual(g.read("INRUSH"), 0x14)

    def test_en_cycle_restores_defaults(self):
        t, g, _ = make()
        g.identify()
        g.write("DAC_HARD", 0xC8)
        self.assertEqual(g.safe_defaults(), {})
        self.assertEqual(g.read("DAC_HARD"), 0xFE)
        self.assertEqual(t.violations, [])

    def test_safe_defaults_without_en(self):
        t, g, _ = make()
        t.has_en = False
        g.identify()
        g.write("DAC_HARD", 0xC8)
        g.write("MODE", 0x07)
        self.assertEqual(g.safe_defaults(), {})

    def test_en_cycle_needs_inhibit(self):
        t, g, _ = make()
        g.set_inhibit(False)
        with self.assertRaises(h.G1SafetyError):
            g.en_cycle()


class Calibration(unittest.TestCase):
    def test_soft_offset(self):
        # +1.0 mV input offset -> about +5 codes of SENSE_OFS
        t, g, _ = make(vref_V=1.04, sense_offset_mV=1.0)
        t.vin_mV = 25.0
        g.identify()
        r = g.calibrate_soft(25.0)
        self.assertEqual(r["c_high"], 132)         # floor((25+1)/0.19623)
        self.assertEqual(r["raw_correction"], 5)
        self.assertTrue(r["monotonic_confirm"])
        self.assertEqual(r["c_high_upward"], 132)
        self.assertEqual(g.read("SENSE_OFS"), 0)    # restored
        self.assertEqual(g.read("MODE"), 0x03)

    def test_hard_kick(self):
        t, g, _ = make(vref_V=1.04, hard_kick_lsb=45)
        t.vin_mV = 25.0
        g.identify()
        r = g.calibrate_hard(25.0)
        self.assertEqual(r["c_high"], 172)          # 127 + 45
        self.assertTrue(r["within_expected_sim"])
        self.assertEqual(r["expected_c_high_sim"], 172)
        self.assertEqual(r["raw_correction"], 45)

    def test_full_cal_and_arm(self):
        t, g, _ = make(vref_V=1.04, sense_offset_mV=0.6, hard_kick_lsb=47)
        t.vin_mV = 25.0
        g.identify()
        s = g.calibrate_soft(25.0)
        hh = g.calibrate_hard(25.0)
        cal = g.compute_calibration(s, hh)
        self.assertEqual(cal["sense_ofs"], 3)
        self.assertEqual(cal["hard_extra"], 47)
        g.measure_fosc()
        res = g.arm(hard_mV=35.0, soft_mV=30.0, soft_time_ms=1.0)
        self.assertEqual(res["codes"]["DAC_HARD"], 178 + 47)
        self.assertEqual(g.read("DAC_HARD_EFF"), 178 + 47 + 3)
        self.assertEqual(g.read("MODE"), 0x03)
        self.assertAlmostEqual(res["soft_window_ms"], 1.0, delta=0.03)
        # with the bus released and nominal 25 mV, no trip; Kelvin check passes
        g.set_inhibit(False)
        t.sleep(2e-3)
        self.assertFalse(g.status()["tripped"])
        self.assertTrue(g.kelvin_check()["pass"])
        self.assertEqual(g.read("MODE"), 0x03)
        # the demo fault: 45 mV step -> hard trip
        t.vin_mV = 45.0
        t.sleep(5e-6)
        st = g.status()
        self.assertTrue(st["tripped"])
        self.assertEqual(st["cause"], "hard")
        self.assertEqual(st["trip_cnt"], 1)
        self.assertEqual(t.violations, [])

    def test_unreachable_target_refused(self):
        t, g, _ = make(vref_V=1.04, sense_offset_mV=1.0, hard_kick_lsb=50)
        t.vin_mV = 25.0
        g.identify()
        g.compute_calibration(g.calibrate_soft(25.0), g.calibrate_hard(25.0))
        with self.assertRaises(h.G1SafetyError):
            g.arm(hard_mV=45.0, soft_mV=30.0, soft_time_ms=1.0)   # 229+50+5 > 255

    def test_arm_requires_calibration(self):
        t, g, _ = make()
        g.identify()
        with self.assertRaises(h.G1SafetyError):
            g.arm(35.0, 30.0, 1.0)
        res = g.arm(35.0, 30.0, 1.0, allow_uncalibrated=True)
        self.assertTrue(any("UNCALIBRATED" in w for w in res["warnings"]))

    def test_no_bracket(self):
        t, g, _ = make(vref_V=1.04)
        t.vin_mV = 60.0
        g.identify()
        with self.assertRaises(h.CalibrationError):
            g.calibrate_soft(60.0)
        t.vin_mV = 25.0
        t.sense_n_open = True
        with self.assertRaises(h.CalibrationError):
            g.calibrate_soft(25.0)

    def test_noise_majority(self):
        t, g, _ = make(vref_V=1.04, noise_lsb=0.3, seed=7)
        t.vin_mV = 25.0
        g.identify()
        r = g.calibrate_soft(25.0, n_reads=32)
        self.assertIn(r["c_high"], (126, 127, 128))

    def test_calibration_needs_inhibit(self):
        t, g, _ = make()
        g.identify()
        g.set_inhibit(False)
        with self.assertRaises(h.G1SafetyError):
            g.calibrate_soft(25.0)

    def test_kelvin_open_sense_n(self):
        t, g, _ = make(vref_V=1.04)
        g.identify()
        t.vin_mV = 25.0
        t.sense_n_open = True
        self.assertFalse(g.kelvin_check()["pass"])


class Clock(unittest.TestCase):
    def test_measure_and_trim(self):
        t, g, _ = make()
        g.identify()
        f = g.measure_fosc()
        self.assertAlmostEqual(f / h.F_OSC_NOMINAL_HZ, 1.0, delta=0.005)
        r = g.trim_osc(10e6)
        self.assertEqual(r["best_code"], 6)      # 9.436 MHz / (1 - 2*0.027) = 9.975 MHz
        self.assertEqual(g.read("OSC_CTRL"), 0x16)

    def test_watchdog_ok(self):
        t, g, inh = make()
        g.identify()
        g.arm(35.0, 30.0, 1.0, allow_uncalibrated=True)
        r = g.watchdog(duration_s=0.2, period_s=3e-3)
        self.assertTrue(r["ok"])
        self.assertAlmostEqual(r["f_osc_est_hz"] / h.F_OSC_NOMINAL_HZ, 1.0, delta=0.02)
        self.assertTrue(t.en)

    def test_watchdog_stopped_clock(self):
        t, g, inh = make()
        g.identify()
        g.set_inhibit(False)
        fired = []
        t.clock_stopped = True
        r = g.watchdog(duration_s=0.2, period_s=3e-3, on_fail=fired.append)
        self.assertFalse(r["ok"])
        self.assertFalse(t.en)                  # EN dropped
        self.assertEqual(inh[-1], True)         # inhibit asserted
        self.assertEqual(len(fired), 1)

    def test_watchdog_config_upset(self):
        t, g, inh = make()
        g.identify()
        g.arm(35.0, 30.0, 1.0, allow_uncalibrated=True)
        t.r[h.ADDR["HARD_N"]] = 0x80            # simulated register upset (H5)
        r = g.watchdog(duration_s=0.5, period_s=3e-3, check_config_every=5)
        self.assertFalse(r["ok"])
        self.assertIn("HARD_N", r["reason"])

    def test_r2_osc_en_write_refused(self):
        t, g, _ = make(version=h.VERSION_R2)
        g.identify(require_version=None)
        with self.assertRaises(h.G1SafetyError):
            g.write("OSC_CTRL", 0x08)
        self.assertFalse(t.clock_stopped)


class StatusSeuT2f(unittest.TestCase):
    def test_forced_trip_and_clear(self):
        t, g, _ = make()
        g.identify()
        g.write("MODE", 0x03 | h.MODE_FORCE_TRIP)
        t.sleep(1e-3)
        st = g.status()
        self.assertTrue(st["tripped"])
        self.assertEqual(st["cause"], "forced")
        self.assertFalse(st["gate_en"])
        g.write("MODE", 0x03)
        g.command(h.CTRL_CLEAR)
        self.assertFalse(g.status()["tripped"])

    def test_seu_self_test(self):
        t, g, _ = make()
        g.identify()
        r = g.seu_self_test()
        self.assertTrue(r["pass"])

    def test_t2f(self):
        t, g, _ = make()
        g.identify()
        r = g.t2f_read("ptat", gate_time=0.1, counter=lambda gt: 1.518e6, temp_C=27.0)
        self.assertAlmostEqual(r["expected_hz_sim"], 1.5172e6, delta=200)
        self.assertAlmostEqual(r["uncalibrated_temp_C"], 27.2, delta=0.1)
        self.assertEqual(g.read("TEMP_CTRL"), 0x01)
        g.t2f_read("ref")
        self.assertEqual(g.read("TEMP_CTRL"), 0x03)

    def test_cli_dummy(self):
        self.assertEqual(h.main(["--transport", "dummy", "identify"]), 0)
        self.assertEqual(h.main(["--transport", "dummy", "--inhibit-asserted",
                                 "--dummy-offset-mV", "0.4", "arm", "--hard-mV", "35",
                                 "--soft-mV", "30", "--soft-time-ms", "1"]), 0)
        self.assertEqual(h.main(["--transport", "dummy", "arm", "--hard-mV", "35",
                                 "--soft-mV", "30", "--soft-time-ms", "1"]), 1)


if __name__ == "__main__":
    unittest.main()
