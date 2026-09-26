#!/usr/bin/env python3
"""G1 guardian bench host library and CLI (register map 1.2, chip of record r3).

Contract: ``../../specification/G1_REGISTER_MAP.md`` (serial protocol, register
map, reset behaviour) and ``../../specification/G1_TOP_LEVEL_SPECIFICATION.md``
section 6 (host rules H1-H5, power rules P1-P9, calibration contract).
Bench plan: ``../README.md``. Board rules: ``BOARD_CHECKLIST.md``.

Status: this library has been exercised only against ``DummyTransport``, a
model of the register file written from the map (``test_g1_host.py``). It has
**not run** against silicon, an FTDI adapter or a Raspberry Pi. The
hardware transports below are stubs with TODOs.

Dependencies: Python >= 3.6 standard library. ``pyftdi`` or ``spidev`` only
for the corresponding hardware transport.

Serial interface summary (map section 1):
  * SPI mode 0 (SCLK idles low, SDI sampled on rising edge, SDO changes on
    falling edge), MSB first, no chip select.
  * Command byte: bit 7 = R/nW (1 = read), bits 6:0 = address.
  * Write frame: 16 clocks (command, data).
  * Read frame: 24 clocks (command, turnaround byte, data on SDO).
  * Framing is restored by SCLK idle >= 64 osc_clk cycles; the host idles
    >= 128 osc_clk cycles (SCLK low) before *every* frame here, never starts a
    frame 64-80 cycles into an idle, and keeps every SCLK-low phase inside a
    frame < 64 osc_clk cycles (the transport must clock the 16/24 bits as one
    contiguous burst).
  * After power-up or an EN rise: wait >= 128 osc_clk cycles before the first
    frame.

Safety conventions enforced by ``G1``:
  * every RW write is preceded by the idle and followed by a read-back (H3);
    a mismatch re-synchronises and raises ``G1VerifyError``;
  * ``SOFT_TIME`` is written H then L (map 1.2 atomic load on L); on a map-1.1
    part (VERSION 0x11, r2 fallback) ``MODE.SOFT_EN`` is cleared first (H4);
  * ``INRUSH`` is written only while the external load inhibit is asserted
    (both map versions; on 1.1 the host also waits for INRUSH_ACTIVE = 0, H2);
  * ``OSC_CTRL`` is always written with bit 4 (OSC_EN) = 1; a 0 there stops the
    clock on a map-1.1 part and removes all protection;
  * ``TEMP_CTRL.BGR_R4`` is never set (it lowers VREF and every threshold by
    about 12 %);
  * EN cycles and calibration require the external inhibit asserted.
"""

from __future__ import print_function

import argparse
import json
import math
import random
import sys
import time

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Register map (G1_REGISTER_MAP.md section 4, version 1.2)
# ---------------------------------------------------------------------------

CHIP_ID_VALUE = 0x47          # 'G'
VERSION_R3 = 0x12             # map 1.2, chip of record r3
VERSION_R2 = 0x11             # map 1.1, documented fallback r2 (and r1)

# name: (address, access, reset value map 1.2, writable-bit mask)
REGS = {
    "CHIP_ID":      (0x00, "RO", 0x47, 0x00),
    "VERSION":      (0x01, "RO", 0x12, 0x00),
    "DAC_SOFT":     (0x02, "RW", 0x99, 0xFF),
    "DAC_HARD":     (0x03, "RW", 0xFE, 0xFF),
    "SOFT_TIME_L":  (0x04, "RW", 0x27, 0xFF),
    "SOFT_TIME_H":  (0x05, "RW", 0x00, 0xFF),
    "SOFT_CFG":     (0x06, "RW", 0x00, 0x0F),
    "HARD_N":       (0x07, "RW", 0x04, 0xFF),
    "INRUSH":       (0x08, "RW", 0x02, 0xFF),
    "HOLD_TIME":    (0x09, "RW", 0x0C, 0xFF),
    "RETRY_MAX":    (0x0A, "RW", 0x03, 0xFF),
    "MODE":         (0x0B, "RW", 0x03, 0x3F),
    "CTRL":         (0x0C, "WO", 0x00, 0x0F),
    "STATUS":       (0x0D, "RO", 0x80, 0x00),
    "STATUS2":      (0x0E, "RO", None, 0x00),
    "TRIP_CNT_L":   (0x0F, "RO", 0x00, 0x00),
    "TRIP_CNT_H":   (0x10, "RO", 0x00, 0x00),
    "SOFT_PEAK_L":  (0x11, "RO", 0x00, 0x00),
    "SOFT_PEAK_H":  (0x12, "RO", 0x00, 0x00),
    "SEU_CTRL":     (0x18, "RW", 0x01, 0x07),
    "SEU_CMD":      (0x19, "WO", 0x00, 0x07),
    "SEU_STATUS":   (0x1A, "RO", None, 0x00),
    "SEU_PLAIN_L":  (0x1B, "RO", 0x00, 0x00),
    "SEU_PLAIN_H":  (0x1C, "RO", 0x00, 0x00),
    "SEU_CORR_L":   (0x1D, "RO", 0x00, 0x00),
    "SEU_CORR_H":   (0x1E, "RO", 0x00, 0x00),
    "SEU_UNC":      (0x1F, "RO", 0x00, 0x00),
    "SEU_RUN":      (0x20, "RO", 0x00, 0x00),
    "OSC_CNT_L":    (0x24, "RO", 0x00, 0x00),
    "OSC_CNT_H":    (0x25, "RO", 0x00, 0x00),
    "OSC_DIV":      (0x26, "RW", 0x00, 0x07),
    "SENSE_OFS":    (0x27, "RW", 0x00, 0xFF),
    "OSC_CTRL":     (0x28, "RW", 0x18, 0x1F),
    "TEMP_CTRL":    (0x29, "RW", 0x01, 0x07),
    "DAC_SOFT_EFF": (0x2A, "RO", 0x99, 0x00),
    "DAC_HARD_EFF": (0x2B, "RO", 0xFE, 0x00),
}
ADDR = {k: v[0] for k, v in REGS.items()}
NAME = {v[0]: k for k, v in REGS.items()}

# Reset values that differ on the map-1.1 (r2 fallback) part.
RESET_OVERRIDES_1_1 = {"VERSION": 0x11, "INRUSH": 0x14}

# Configuration registers the host owns (H5 read-back / rewrite set).
CONFIG_REGS = ["DAC_SOFT", "DAC_HARD", "SOFT_TIME_L", "SOFT_TIME_H", "SOFT_CFG",
               "HARD_N", "INRUSH", "HOLD_TIME", "RETRY_MAX", "MODE", "OSC_DIV",
               "SENSE_OFS", "OSC_CTRL", "TEMP_CTRL", "SEU_CTRL"]

# MODE bits
MODE_SOFT_EN = 0x01
MODE_HARD_EN = 0x02
MODE_RETRIG = 0x04
MODE_TRIP_SET_SEL = 0x08     # no effect on the chip of record; never set here
MODE_FORCE_TRIP = 0x10
MODE_FAST_EN = 0x20
# CTRL bits (self-clearing)
CTRL_CLEAR = 0x01
CTRL_CLR_TRIP_CNT = 0x02
CTRL_CLR_PEAK = 0x04
CTRL_CLR_OSC_CNT = 0x08
# SEU_CMD bits
SEU_CLR_CNT = 0x01
SEU_INJ_PLAIN = 0x02
SEU_INJ_TMR = 0x04
# TEMP_CTRL bits
T2F_EN = 0x01
T2F_MODE_REF = 0x02
BGR_R4 = 0x04
# OSC_CTRL
OSC_EN_BIT = 0x10

CAUSES = {0: "none", 1: "soft", 2: "hard", 3: "forced"}

# ---------------------------------------------------------------------------
# Analog scaling and simulated expectations (all SIMULATED, none measured)
# ---------------------------------------------------------------------------

VREF_NOMINAL_V = 1.04         # nominal mapping of the calibration contract
VREF_BGR586_SIM_V = 1.04546   # simulated BGR586, tt/27 C (pin open)


def lsb_mV(vref_V=VREF_NOMINAL_V):
    """Shunt-referred DAC LSB in mV: VREF/530 at icmp, /10 to the shunt.

    Code 200 -> 39.25 mV, 0x99 -> 30.0 mV, 0xFE -> 49.8 mV at VREF 1.04 V
    (register map section 2; TRIP postlayout README).
    """
    return vref_V * 1000.0 / 5300.0


# Hard-comparator kick offset: the hard comparator trips 40-56 LSB below its
# code (TRIP NF4 block bench, tt/ss/ff at codes 200 and 254), about 41-47 LSB
# on the chip netlists at tt/27 C. Expected hard crossing code for an input
# Vin = Cideal + offset (the effective *threshold* is ~45 codes below the code,
# so the crossing *code* is ~45 above the ideal code).
HARD_KICK_NOMINAL_LSB = 45
HARD_KICK_RANGE_LSB = (40, 56)
SOFT_KICK_RANGE_LSB = (0, 1)   # NF4 soft path trips 0-1 LSB early (simulated)
USABLE_HARD_RANGE_MV = (25.0, 40.0)

# TEMP_OUT (simulated): BGR586 block level, typical, PTAT mode.
T2F_F25_HZ = 1.5074e6
T2F_SLOPE_HZ_PER_C = 4.9085e3
T2F_CHIP_27C_HZ = 1.518e6      # chip netlists, tt/27 C
T2F_REF_MODE_HZ_APPROX = 1.6e6  # g1_t2f/INTERFACE.md "about 1.6 MHz"; not re-established with BGR586

# Oscillator (simulated): trim 8 loaded 9.436 MHz tt/27 C; 7.61-12.43 MHz corners.
F_OSC_NOMINAL_HZ = 9.436e6
F_OSC_SIM_RANGE_HZ = (7.61e6, 12.43e6)
OSC_TRIM_STEP = 0.027          # ~2.7 %/LSB, higher code = slower


class G1Error(Exception):
    """Base error."""


class G1VerifyError(G1Error):
    """Read-back after a write did not match."""


class G1SafetyError(G1Error):
    """An operation was refused because a safety precondition is not met."""


class CalibrationError(G1Error):
    """The comparator crossing could not be bracketed."""


def s8(v):
    """Unsigned byte -> two's complement int."""
    return v - 256 if v & 0x80 else v


def u8(v):
    """int -128..127 -> unsigned byte."""
    if not -128 <= v <= 127:
        raise ValueError("SENSE_OFS out of range: %d" % v)
    return v & 0xFF


def sat8(v):
    return max(0, min(255, v))


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------

class Transport(object):
    """Physical access to the three-wire interface and the EN pin.

    ``xfer(data)`` clocks ``len(data)*8`` bits in SPI mode 0, MSB first,
    full duplex, as one contiguous burst (no SCLK-low stall >= 64 osc_clk
    cycles, i.e. keep inter-bit/inter-byte gaps well under 5 us) and returns
    the bytes seen on SDO. SCLK must be low before and after.
    ``idle(s)`` holds SCLK low for at least ``s`` seconds.
    ``set_en(level)`` drives the EN pin (low = reset). Optional: the base
    class raises NotImplementedError; ``G1`` then refuses EN-dependent steps.
    """

    has_en = False

    def xfer(self, data):
        raise NotImplementedError

    def idle(self, seconds):
        self.sleep(seconds)

    def set_en(self, level):
        raise NotImplementedError("this transport has no EN control")

    def sleep(self, seconds):
        time.sleep(seconds)

    def now(self):
        return time.monotonic()

    def close(self):
        pass


class SpidevTransport(Transport):
    """Raspberry Pi (Linux spidev) transport. STUB, not run on hardware.

    TODO(bench):
      * Wire SCLK/SDI/SDO to SPI0 SCLK/MOSI/MISO (3.3 V IO; the G1 inputs are
        3.3 V pads, SDO is a 3.3 V push-pull output). Leave CE0 unconnected:
        G1 has no chip select. Keep the board's 100 kOhm pull-downs on SCLK
        and SDI (P8/B6).
      * Confirm with a scope that one 3-byte ``xfer2`` is a single contiguous
        24-clock burst (no inter-byte gap >= ~5 us) at the chosen speed and
        that SCLK idles low (mode 0).
      * Use speed_hz <= 1 MHz for bring-up (limit: f_SCLK <= f_OSC, >= 7.6 MHz
        simulated minimum; lower bound: each SCLK-low phase < 64 osc_clk
        cycles, i.e. f_SCLK above ~100 kHz).
      * EN via a GPIO through a CMOS/Schmitt buffer (P8); the inhibit is a
        separate GPIO or hardware interlock, passed to ``G1`` as a callback.
        Implement ``set_en`` with python3-gpiod or RPi.GPIO.
    """

    has_en = False

    def __init__(self, bus=0, device=0, speed_hz=1000000, en_gpio=None):
        import spidev  # noqa: F401  (hardware dependency)
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.mode = 0
        self.spi.max_speed_hz = int(speed_hz)
        try:
            self.spi.no_cs = True   # TODO(bench): driver support varies
        except (OSError, IOError, AttributeError):
            pass
        self.en_gpio = en_gpio
        # TODO(bench): request en_gpio as output, initial LOW, and set has_en.

    def xfer(self, data):
        return bytes(self.spi.xfer2(list(bytearray(data))))

    def set_en(self, level):
        raise NotImplementedError("TODO(bench): drive EN GPIO %r" % self.en_gpio)

    def close(self):
        self.spi.close()


class FtdiTransport(Transport):
    """FTDI FT232H/FT2232H (pyftdi) transport. STUB, not run on hardware.

    TODO(bench):
      * ADBUS0 = SCLK, ADBUS1 = SDI (MOSI), ADBUS2 = SDO (MISO); do not
        connect the CS line (ADBUS3). EN on a GPIO (e.g. ADBUS4) through a
        CMOS/Schmitt buffer; inhibit on another GPIO or a hardware interlock.
      * pyftdi ``SpiController(cs_count=1)``, mode 0, ``exchange(..., duplex=True)``.
        Check with a scope that the burst is contiguous and SCLK idles low.
      * Implement ``set_en`` via ``SpiController.get_gpio()`` and set has_en.
    """

    has_en = False

    def __init__(self, url="ftdi://ftdi:232h/1", freq_hz=1e6):
        from pyftdi.spi import SpiController  # hardware dependency
        self.ctrl = SpiController(cs_count=1)
        self.ctrl.configure(url)
        self.port = self.ctrl.get_port(cs=0, freq=freq_hz, mode=0)
        # TODO(bench): gpio = self.ctrl.get_gpio(); gpio.set_direction(0x10, 0x10); EN low.

    def xfer(self, data):
        return bytes(self.port.exchange(bytes(data), duplex=True))

    def set_en(self, level):
        raise NotImplementedError("TODO(bench): drive EN via FTDI GPIO")

    def close(self):
        self.ctrl.terminate()


class DummyTransport(Transport):
    """Offline model of the G1 register file and a simplified breaker.

    Written from G1_REGISTER_MAP.md; *not* a model of the silicon or of the RTL
    timing. Simulated time advances with every frame, idle and sleep.
    The analog side is a pair of ideal comparators:
      cmp_soft = Vin + sense_offset > (dac_soft_eff - soft_kick) * LSB
      cmp_hard = Vin + sense_offset > (dac_hard_eff - hard_kick) * LSB
    with optional Gaussian decision noise (in LSB). ``vin_mV`` is the
    bench-injected shunt voltage. It also records protocol violations (idle
    shorter than 128 osc_clk cycles before a frame, frames while EN low, frames
    within 128 cycles of the EN rise) so tests can check the host obeys H3.
    """

    has_en = True

    def __init__(self, version=VERSION_R3, f_osc_trim8_hz=F_OSC_NOMINAL_HZ,
                 f_sclk_hz=1e6, vref_V=VREF_BGR586_SIM_V, sense_offset_mV=0.0,
                 hard_kick_lsb=HARD_KICK_NOMINAL_LSB, soft_kick_lsb=0.0,
                 noise_lsb=0.0, seed=1):
        self.version = version
        self.f0 = f_osc_trim8_hz
        self.f_sclk = f_sclk_hz
        self.vref_V = vref_V
        self.sense_offset_mV = sense_offset_mV
        self.hard_kick_lsb = hard_kick_lsb
        self.soft_kick_lsb = soft_kick_lsb
        self.noise_lsb = noise_lsb
        self.rng = random.Random(seed)
        self.vin_mV = 0.0
        self.sense_n_open = False
        self.sense_p_open = False
        self.clock_stopped = False
        self.t = 0.0
        self.last_frame_end = -1.0
        self.en = False
        self.en_rise_t = None
        self.en_fall_t = 0.0
        self.violations = []
        self.frames = []          # (t, 'R'/'W', addr, data)
        self.min_idle_cycles = None
        self._last_read = 0
        self._osc_cnt_base = 0.0
        self._reset_regs()

    # -- model state ------------------------------------------------------
    def _reset_regs(self):
        self.r = {}
        for name, (addr, acc, rst, _m) in REGS.items():
            if rst is not None:
                self.r[addr] = rst
        if self.version == VERSION_R2:
            for k, v in RESET_OVERRIDES_1_1.items():
                self.r[ADDR[k]] = v
        self.r[ADDR["VERSION"]] = self.version
        self.soft_time_staged_h = 0
        self.hi_hold = 0
        self.tripped = False
        self.cause = 0
        self.soft_cnt = 0.0
        self.soft_peak = 0.0
        self.hard_run = 0.0
        self.trip_cnt = 0
        self.inrush_left = 0.0
        self.seu = {"plain": 0, "corr": 0, "unc": 0, "run": 0}
        self._osc_cnt_base = self._osc_ticks()

    def f_osc(self):
        trim = self.r.get(ADDR["OSC_CTRL"], 0x18) & 0x0F
        return self.f0 / (1.0 + OSC_TRIM_STEP * (trim - 8))

    def _osc_ticks(self):
        return getattr(self, "_ticks", 0.0)

    def _advance(self, dt):
        if dt <= 0:
            return
        self.t += dt
        if self.clock_stopped or not self.en:
            return
        f = self.f_osc()
        self._ticks = self._osc_ticks() + dt * f
        # breaker model (continuous approximation)
        if self.inrush_left > 0:
            self.inrush_left = max(0.0, self.inrush_left - dt * f)
            return
        if self.tripped:
            return
        mode = self.r[ADDR["MODE"]]
        if mode & MODE_FORCE_TRIP:
            self._trip(3)
            return
        cs, ch = self._cmp(noise=False)
        if (mode & MODE_HARD_EN) and ch:
            self.hard_run += dt * f / 2.0
            n = max(1, self.r[ADDR["HARD_N"]])
            if self.hard_run >= n:
                self._trip(2)
                return
        else:
            self.hard_run = 0.0
        if mode & MODE_SOFT_EN:
            if cs:
                self.soft_cnt += dt * f
            else:
                decay = 4 ** (self.r[ADDR["SOFT_CFG"]] & 0x03)
                self.soft_cnt = max(0.0, self.soft_cnt - dt * f / decay)
            self.soft_peak = max(self.soft_peak, self.soft_cnt)
            st = (self.r[ADDR["SOFT_TIME_H"]] << 8) | self.r[ADDR["SOFT_TIME_L"]]
            if self.soft_cnt >= st * 256:
                self._trip(1)
        else:
            self.soft_cnt = 0.0

    def _trip(self, cause):
        self.tripped = True
        self.cause = cause
        self.trip_cnt = min(0xFFFF, self.trip_cnt + 1)

    def _eff_codes(self):
        ofs = s8(self.r[ADDR["SENSE_OFS"]])
        cfg = self.r[ADDR["SOFT_CFG"]]
        hyst = 0
        if (cfg & 0x04) and self.soft_cnt > 0:
            hyst = 2 if cfg & 0x08 else 1
        soft = sat8(self.r[ADDR["DAC_SOFT"]] - hyst + ofs)
        hard = sat8(self.r[ADDR["DAC_HARD"]] + ofs)
        return soft, hard

    def _cmp(self, noise=True):
        if self.sense_p_open:
            return True, True
        if self.sense_n_open:
            return False, False
        lsb = lsb_mV(self.vref_V)
        vin = self.vin_mV + self.sense_offset_mV
        soft, hard = self._eff_codes()
        ns = self.rng.gauss(0, self.noise_lsb) * lsb if (noise and self.noise_lsb) else 0.0
        nh = self.rng.gauss(0, self.noise_lsb) * lsb if (noise and self.noise_lsb) else 0.0
        cs = vin + ns > (soft - self.soft_kick_lsb) * lsb
        ch = vin + nh > (hard - self.hard_kick_lsb) * lsb
        return cs, ch

    # -- register reads with side effects --------------------------------
    def _read_reg(self, a):
        if a == ADDR["STATUS"]:
            v = 0x80 | (1 if self.tripped else 0) | (self.cause << 1)
            if self.inrush_left > 0:
                v |= 0x08
            if self.soft_cnt > 0:
                v |= 0x40
            return v
        if a == ADDR["STATUS2"]:
            cs, ch = self._cmp(noise=True)
            gate_en = self.en and not self.tripped
            return (1 if cs else 0) | (2 if ch else 0) | (4 if gate_en else 0) | \
                (8 if self.tripped else 0)
        pairs = {
            ADDR["TRIP_CNT_L"]: self.trip_cnt,
            ADDR["SOFT_PEAK_L"]: int(self.soft_peak // 256),
            ADDR["SEU_PLAIN_L"]: self.seu["plain"],
            ADDR["SEU_CORR_L"]: self.seu["corr"],
            ADDR["OSC_CNT_L"]: int((self._osc_ticks() - self._osc_cnt_base)
                                   / (256 * 2 ** (self.r[ADDR["OSC_DIV"]] & 7))) & 0xFFFF,
        }
        if a in pairs:
            val = min(pairs[a], 0xFFFF) if a != ADDR["OSC_CNT_L"] else pairs[a]
            self.hi_hold = (val >> 8) & 0xFF
            return val & 0xFF
        if a in (ADDR["TRIP_CNT_H"], ADDR["SOFT_PEAK_H"], ADDR["SEU_PLAIN_H"],
                 ADDR["SEU_CORR_H"], ADDR["OSC_CNT_H"]):
            return self.hi_hold
        if a == ADDR["SEU_UNC"]:
            return min(255, self.seu["unc"])
        if a == ADDR["SEU_RUN"]:
            return min(255, self.seu["run"])
        if a == ADDR["SEU_STATUS"]:
            return 0x01 if self.r[ADDR["SEU_CTRL"]] & 1 else 0x00
        if a == ADDR["DAC_SOFT_EFF"]:
            return self._eff_codes()[0]
        if a == ADDR["DAC_HARD_EFF"]:
            return self._eff_codes()[1]
        if a in NAME and REGS[NAME[a]][1] == "WO":
            return 0
        return self.r.get(a, 0)

    def _write_reg(self, a, d):
        name = NAME.get(a)
        if name is None:
            return
        acc, mask = REGS[name][1], REGS[name][3]
        if acc == "RO":
            return
        d &= mask
        if name == "CTRL":
            if d & CTRL_CLEAR:
                self.tripped, self.cause, self.soft_cnt, self.hard_run = False, 0, 0.0, 0.0
            if d & CTRL_CLR_TRIP_CNT:
                self.trip_cnt = 0
            if d & CTRL_CLR_PEAK:
                self.soft_peak = 0.0
            if d & CTRL_CLR_OSC_CNT:
                self._osc_cnt_base = self._osc_ticks()
            return
        if name == "SEU_CMD":
            if d & SEU_CLR_CNT:
                self.seu = {"plain": 0, "corr": 0, "unc": 0, "run": 0}
            if d & SEU_INJ_PLAIN:
                self.seu["plain"] += 1
                self.seu["run"] = max(self.seu["run"], 1)
            if d & SEU_INJ_TMR:
                self.seu["corr"] += 1
            return
        if name == "SOFT_TIME_H" and self.version == VERSION_R3:
            self.soft_time_staged_h = d
            return
        if name == "SOFT_TIME_L" and self.version == VERSION_R3:
            self.r[ADDR["SOFT_TIME_H"]] = self.soft_time_staged_h
            self.r[a] = d
            return
        if name == "OSC_CTRL":
            if self.version == VERSION_R3:
                d |= OSC_EN_BIT
            elif not d & OSC_EN_BIT:
                self.clock_stopped = True
        if name == "INRUSH" and self.version == VERSION_R2 and self.inrush_left == 0 \
                and d > self.r[a] and self.en:
            # map 1.1 hazard M2: raising INRUSH re-opens the mask
            self.inrush_left = (d - self.r[a]) * 512.0
        if name == "SOFT_TIME_L":
            self.soft_time_staged_h = self.r[ADDR["SOFT_TIME_H"]]
        self.r[a] = d

    # -- Transport API -------------------------------------------------------
    def xfer(self, data):
        data = bytearray(data)
        f = self.f_osc() if not self.clock_stopped else self.f0
        if self.last_frame_end >= 0:
            gap_cycles = (self.t - self.last_frame_end) * f
            if self.min_idle_cycles is None or gap_cycles < self.min_idle_cycles:
                self.min_idle_cycles = gap_cycles
            if gap_cycles < 128:
                self.violations.append("idle %.1f cycles before frame at t=%.6f s"
                                       % (gap_cycles, self.t))
        if not self.en:
            self.violations.append("frame while EN low at t=%.6f s" % self.t)
        elif self.en_rise_t is not None and (self.t - self.en_rise_t) * f < 133:
            self.violations.append("frame within 128+5 cycles of EN rise")
        self._advance(len(data) * 8 / self.f_sclk)
        self.last_frame_end = self.t
        out = bytearray(len(data))
        if not self.en:
            return bytes(out)
        cmd = data[0]
        a = cmd & 0x7F
        if cmd & 0x80:
            if len(data) != 3:
                self.violations.append("read frame of %d bytes" % len(data))
                return bytes(out)
            if self.clock_stopped:
                v = self._last_read            # stale holding register
            else:
                v = self._read_reg(a)
                self._last_read = v
            out[2] = v
            self.frames.append((self.t, "R", a, v))
        else:
            if len(data) != 2:
                self.violations.append("write frame of %d bytes" % len(data))
                return bytes(out)
            if not self.clock_stopped:
                self._write_reg(a, data[1])
            self.frames.append((self.t, "W", a, data[1]))
        return bytes(out)

    def idle(self, seconds):
        self._advance(seconds)

    def sleep(self, seconds):
        self._advance(seconds)

    def now(self):
        return self.t

    def set_en(self, level):
        level = bool(level)
        if level == self.en:
            return
        if level:
            low_s = self.t - self.en_fall_t
            f = self.f0
            # map 1.2: reset after 8 consecutive low samples (~10 cycles); 1.1: any low
            if self.version == VERSION_R2 or low_s * f >= 10 or self.en_rise_t is None:
                self._reset_regs()
                self.clock_stopped = False
            self.en = True
            self.en_rise_t = self.t
            self.inrush_left = self.r[ADDR["INRUSH"]] * 512.0
        else:
            self.en = False
            self.en_fall_t = self.t
            self.tripped = False    # en_core clears the G1_GATE latch


# ---------------------------------------------------------------------------
# Host library
# ---------------------------------------------------------------------------

class G1(object):
    """Host driver for one G1 part.

    ``inhibit`` is a callable ``inhibit(asserted: bool)`` that drives the
    independent load-bus inhibit (P2). If it is None the library assumes the
    operator controls the inhibit manually and must declare its state with
    ``declare_inhibit(True/False)``; operations that need it refuse to run
    until it is declared asserted.
    """

    def __init__(self, transport, inhibit=None, f_osc_min_hz=7.0e6,
                 vref_V=None, log=None):
        self.t = transport
        self._inhibit_cb = inhibit
        self.inhibit_asserted = None      # unknown until set/declared
        self.f_osc_min_hz = f_osc_min_hz
        # >= 128 osc_clk cycles at the slowest assumed clock, 30 % margin
        self.idle_s = max(25e-6, 1.3 * 128.0 / f_osc_min_hz)
        self.post_en_s = self.idle_s + 2e-6    # 5 cycles release + 128 idle
        self.vref_V = vref_V if vref_V is not None else VREF_NOMINAL_V
        self.version = None
        self.f_osc_hz = None
        self.calibration = None
        self.config_snapshot = {}
        self.log = log if log is not None else (lambda msg: None)

    # -- inhibit / EN -----------------------------------------------------
    def set_inhibit(self, asserted):
        if self._inhibit_cb is None:
            raise G1SafetyError("no inhibit callback; use declare_inhibit()")
        self._inhibit_cb(bool(asserted))
        self.inhibit_asserted = bool(asserted)
        self.log("inhibit %s" % ("ASSERTED" if asserted else "released"))

    def declare_inhibit(self, asserted):
        """Operator declares the state of a manually controlled inhibit."""
        self.inhibit_asserted = bool(asserted)

    def _require_inhibit(self, what):
        if self.inhibit_asserted is not True:
            raise G1SafetyError("%s requires the external load inhibit asserted" % what)

    def enable(self, vref_cap_nF=10.0, rails_stable_wait=True):
        """First EN rise after power-up (P4/P5/P6), inhibit asserted.

        Waits the VREF settling delay for the fitted VREF capacitor
        (0.2 ms per nF, >= 2 ms at 10 nF per P4; simulated 1 % settling 1.20-1.32 ms
        at 10 nF, 7-8 us at 0 nF, 11.8-13.2 ms at 100 nF), raises EN, then waits
        >= 128 osc_clk cycles before the first frame.
        """
        self._require_inhibit("EN rise")
        if rails_stable_wait:
            self.t.sleep(max(50e-6, 0.2e-3 * vref_cap_nF))
        self.t.set_en(True)
        self.t.idle(self.post_en_s)
        self.config_snapshot = {}

    def en_cycle(self, low_s=10e-6):
        """Deliberate reset: EN low >= 2 us (map 1.2 section 3), inhibit asserted.

        Restores every register to its reset value; the host must reprogram.
        """
        self._require_inhibit("EN cycle")
        self.t.set_en(False)
        self.t.sleep(max(low_s, 2e-6))
        self.t.set_en(True)
        self.t.idle(self.post_en_s)
        self.config_snapshot = {}

    def fail_safe(self, reason):
        """Assert the inhibit and drop EN (H1). Never raises."""
        self.log("FAIL-SAFE: %s" % reason)
        errors = []
        try:
            if self._inhibit_cb is not None:
                self._inhibit_cb(True)
                self.inhibit_asserted = True
        except Exception as e:  # pragma: no cover - hardware path
            errors.append("inhibit: %r" % e)
        try:
            self.t.set_en(False)
        except Exception as e:  # pragma: no cover
            errors.append("EN: %r" % e)
        return {"reason": reason, "errors": errors}

    # -- raw frames ---------------------------------------------------------
    def _addr(self, reg):
        return ADDR[reg] if isinstance(reg, str) else int(reg)

    def resync(self):
        """Hold SCLK low >= 128 osc_clk cycles (map section 1.2)."""
        self.t.idle(self.idle_s)

    def read(self, reg):
        a = self._addr(reg)
        self.t.idle(self.idle_s)
        resp = bytearray(self.t.xfer(bytes(bytearray([0x80 | a, 0x00, 0x00]))))
        return resp[2]

    def read16(self, reg_l):
        """L/H pair: low byte first, the L read latches the H byte."""
        a = self._addr(reg_l)
        lo = self.read(a)
        hi = self.read(a + 1)
        return (hi << 8) | lo

    def write(self, reg, value, verify=True):
        """Write one register with the H3 idle and read-back."""
        a = self._addr(reg)
        name = NAME.get(a)
        if name is None:
            raise G1Error("unmapped address 0x%02X" % a)
        acc, mask = REGS[name][1], REGS[name][3]
        if acc == "RO":
            raise G1Error("%s is read-only" % name)
        value = int(value) & 0xFF
        if value & ~mask & 0xFF:
            raise G1Error("%s: reserved bits set in 0x%02X (mask 0x%02X)" % (name, value, mask))
        if name == "OSC_CTRL" and not value & OSC_EN_BIT:
            raise G1SafetyError("OSC_CTRL bit 4 (OSC_EN) must be written 1")
        if name == "TEMP_CTRL" and value & BGR_R4:
            raise G1SafetyError("BGR_R4 lowers every threshold ~12 %; refused")
        if name == "MODE" and value & MODE_TRIP_SET_SEL:
            raise G1SafetyError("MODE.TRIP_SET_SEL has no effect on the chip of record; refused")
        if name == "INRUSH":
            self._require_inhibit("INRUSH write")
        if name in ("SOFT_TIME_L", "SOFT_TIME_H"):
            raise G1Error("use write_soft_time() for SOFT_TIME")
        self._raw_write(a, value)
        if verify and acc == "RW":
            self._verify(name, value)
        return value

    def _raw_write(self, a, value):
        self.t.idle(self.idle_s)
        self.t.xfer(bytes(bytearray([a & 0x7F, value & 0xFF])))

    def _expected_readback(self, name, value):
        if name == "OSC_CTRL":
            return value | OSC_EN_BIT
        return value

    def _verify(self, name, value):
        exp = self._expected_readback(name, value)
        got = self.read(name)
        if got != exp:
            self.resync()
            got2 = self.read(name)
            raise G1VerifyError("%s read-back 0x%02X (then 0x%02X), wrote 0x%02X"
                                % (name, got, got2, exp))
        self.config_snapshot[name] = got

    # -- identification ------------------------------------------------------
    def identify(self, require_version=VERSION_R3):
        """Read CHIP_ID and VERSION. r3 reads 0x47 / 0x12.

        ``require_version=None`` accepts the r2 fallback (0x11) and switches the
        library to the map-1.1 rules (H2, H4, OSC_EN hazard).
        """
        cid = self.read("CHIP_ID")
        ver = self.read("VERSION")
        info = {"CHIP_ID": cid, "VERSION": ver,
                "map": "%d.%d" % (ver >> 4, ver & 0xF),
                "revision": {VERSION_R3: "r3 (chip of record)",
                             VERSION_R2: "r2 fallback / r1 (map 1.1)"}.get(ver, "unknown")}
        if cid != CHIP_ID_VALUE:
            raise G1Error("CHIP_ID 0x%02X, expected 0x47 (check wiring, EN, pull-downs, "
                          "idle timing)" % cid)
        if ver not in (VERSION_R3, VERSION_R2):
            raise G1Error("unknown VERSION 0x%02X" % ver)
        if require_version is not None and ver != require_version:
            raise G1Error("VERSION 0x%02X, required 0x%02X" % (ver, require_version))
        self.version = ver
        return info

    def _need_version(self):
        if self.version is None:
            self.identify(require_version=None)

    def reset_values(self):
        self._need_version()
        vals = {k: v[2] for k, v in REGS.items() if v[1] == "RW"}
        if self.version == VERSION_R2:
            vals.update({k: v for k, v in RESET_OVERRIDES_1_1.items() if k in vals})
        return vals

    def dump(self):
        out = {}
        for name, (a, acc, _r, _m) in sorted(REGS.items(), key=lambda kv: kv[1][0]):
            if acc == "WO":
                continue
            out[name] = self.read(a)
        return out

    def safe_defaults(self):
        """Return the part to the reset configuration and verify it.

        With EN control: a deliberate EN cycle (>= 2 us low) under the inhibit.
        Without: rewrite each RW reset value (MODE last) with read-back.
        Returns {register: (expected, read)} for any mismatch (empty = pass).
        """
        self._require_inhibit("safe_defaults")
        self._need_version()
        rv = self.reset_values()
        if getattr(self.t, "has_en", False):
            self.en_cycle()
        else:
            self.write("MODE", 0x00)
            for name in ["DAC_SOFT", "DAC_HARD", "SOFT_CFG", "HARD_N", "INRUSH",
                         "HOLD_TIME", "RETRY_MAX", "OSC_DIV", "SENSE_OFS", "OSC_CTRL",
                         "TEMP_CTRL", "SEU_CTRL"]:
                self.write(name, rv[name])
            self.write_soft_time((rv["SOFT_TIME_H"] << 8) | rv["SOFT_TIME_L"])
            self.write("MODE", rv["MODE"])
        bad = {}
        for name, exp in rv.items():
            got = self.read(name)
            if got != exp:
                bad[name] = (exp, got)
        for name in ("DAC_SOFT_EFF", "DAC_HARD_EFF"):
            exp = REGS[name][2]
            got = self.read(name)
            if got != exp:
                bad[name] = (exp, got)
        self.config_snapshot = {k: v for k, v in rv.items()}
        return bad

    # -- safety-relevant multi-byte writes -----------------------------------
    def write_soft_time(self, value):
        """SOFT_TIME (window = value x 256 osc_clk). r3: H then L, atomic on L.

        r2 fallback (map 1.1): MODE.SOFT_EN cleared during the write (H4).
        """
        self._need_version()
        value = int(value)
        if not 0 <= value <= 0xFFFF:
            raise ValueError("SOFT_TIME 0..0xFFFF")
        hi, lo = (value >> 8) & 0xFF, value & 0xFF
        restore_mode = None
        if self.version == VERSION_R2:
            mode = self.read("MODE")
            if mode & MODE_SOFT_EN:
                restore_mode = mode
                self.write("MODE", mode & ~MODE_SOFT_EN)
        self._raw_write(ADDR["SOFT_TIME_H"], hi)
        if self.version == VERSION_R2:
            self._verify("SOFT_TIME_H", hi)
        self._raw_write(ADDR["SOFT_TIME_L"], lo)
        self._verify("SOFT_TIME_L", lo)
        self._verify("SOFT_TIME_H", hi)     # r3: byte in effect after the L load
        if restore_mode is not None:
            self.write("MODE", restore_mode)
        return value

    def write_inrush(self, value, timeout_s=0.1):
        """INRUSH (mask = value x 512 osc_clk), only under the external inhibit.

        r2 fallback: wait STATUS.INRUSH_ACTIVE = 0 before returning (H2).
        """
        self._require_inhibit("INRUSH write")
        self.write("INRUSH", value)
        if self.version == VERSION_R2:
            t0 = self.t.now()
            while self.read("STATUS") & 0x08:
                if self.t.now() - t0 > timeout_s:
                    raise G1Error("INRUSH_ACTIVE did not clear")
                self.t.sleep(1e-3)

    # -- oscillator ------------------------------------------------------------
    def read_osc_cnt(self):
        return self.read16("OSC_CNT_L")

    def measure_fosc(self, interval_s=0.05):
        """f_OSC from two OSC_CNT reads a known host time apart (map 4.5).

        interval_s must stay below the 16-bit wrap (1.68 s at 10 MHz, 1.35 s at
        12.4 MHz). Host timing error dominates on real hardware: use >= 50 ms.
        """
        div = self.read("OSC_DIV") & 7
        t0 = self.t.now()
        c0 = self.read_osc_cnt()
        self.t.sleep(interval_s)
        t1 = self.t.now()
        c1 = self.read_osc_cnt()
        delta = (c1 - c0) & 0xFFFF
        f = delta * 256.0 * (2 ** div) / (t1 - t0)
        self.f_osc_hz = f
        return f

    def write_osc_trim(self, code):
        if not 0 <= code <= 15:
            raise ValueError("OSC_TRIM 0..15")
        return self.write("OSC_CTRL", OSC_EN_BIT | code)

    def trim_osc(self, target_hz=10e6, interval_s=0.05):
        """Sweep OSC_TRIM 0..15 (higher = slower, ~2.7 %/LSB), pick the closest."""
        results = {}
        for code in range(16):
            self.write_osc_trim(code)
            self.t.sleep(1e-3)
            results[code] = self.measure_fosc(interval_s)
        best = min(results, key=lambda c: abs(results[c] - target_hz))
        self.write_osc_trim(best)
        self.f_osc_hz = results[best]
        return {"best_code": best, "f_hz": results[best], "sweep": results}

    # -- status -------------------------------------------------------------------
    def status(self):
        """Decode STATUS, STATUS2, counters, effective DAC codes and SEU counters."""
        st = self.read("STATUS")
        st2 = self.read("STATUS2")
        d = {
            "STATUS": st, "STATUS2": st2,
            "tripped": bool(st & 1),
            "cause": CAUSES[(st >> 1) & 3],
            "inrush_active": bool(st & 0x08),
            "holding": bool(st & 0x10),
            "gave_up": bool(st & 0x20),
            "soft_armed": bool(st & 0x40),
            "en_bit": bool(st & 0x80),
            "cmp_soft": bool(st2 & 1),
            "cmp_hard": bool(st2 & 2),
            "gate_en": bool(st2 & 4),
            "tripped_analog": bool(st2 & 8),
            "retry_cnt": st2 >> 4,
            "trip_cnt": self.read16("TRIP_CNT_L"),
            "soft_peak": self.read16("SOFT_PEAK_L"),
            "mode": self.read("MODE"),
            "dac_soft_eff": self.read("DAC_SOFT_EFF"),
            "dac_hard_eff": self.read("DAC_HARD_EFF"),
            "sense_ofs": s8(self.read("SENSE_OFS")),
        }
        d["soft_peak_fraction_of_window"] = None
        st_val = (self.read("SOFT_TIME_H") << 8) | self.read("SOFT_TIME_L")
        if st_val:
            d["soft_peak_fraction_of_window"] = d["soft_peak"] / float(st_val)
        if not d["en_bit"]:
            d["warning"] = "STATUS bit 7 reads 0: EN low, part unpowered or bus fault"
        d["seu"] = self.seu_readout()
        return d

    def seu_readout(self):
        return {
            "SEU_CTRL": self.read("SEU_CTRL"),
            "SEU_STATUS": self.read("SEU_STATUS"),
            "plain": self.read16("SEU_PLAIN_L"),
            "corr": self.read16("SEU_CORR_L"),
            "unc": self.read("SEU_UNC"),
            "run": self.read("SEU_RUN"),
        }

    def seu_self_test(self):
        """INJ_PLAIN and INJ_TMR each add one count (plain, corr); unc stays."""
        before = self.seu_readout()
        self.t.idle(self.idle_s)
        self._raw_write(ADDR["SEU_CMD"], SEU_INJ_PLAIN)
        self.t.sleep(100e-6)     # > 256-stage propagation (27 us at 9.4 MHz)
        self._raw_write(ADDR["SEU_CMD"], SEU_INJ_TMR)
        self.t.sleep(100e-6)
        after = self.seu_readout()
        ok = (after["plain"] - before["plain"] == 1 and after["corr"] - before["corr"] == 1
              and after["unc"] == before["unc"])
        return {"before": before, "after": after, "pass": ok}

    def command(self, bits):
        """CTRL self-clearing command (CLEAR, CLR_TRIP_CNT, CLR_PEAK, CLR_OSC_CNT)."""
        self._raw_write(ADDR["CTRL"], bits & 0x0F)

    # -- calibration ------------------------------------------------------------
    def _cmp_fraction(self, bit, n_reads):
        hi = 0
        for _ in range(n_reads):
            if self.read("STATUS2") & bit:
                hi += 1
        return hi / float(n_reads)

    def _calibrate(self, path, vin_mV, vref_V=None, n_reads=16, settle_s=200e-6,
                   coarse_step=4, other_code=None, both_directions=True, restore=True):
        self._require_inhibit("calibration")
        self._need_version()
        vref = vref_V if vref_V is not None else self.vref_V
        lsb = lsb_mV(vref)
        c_ideal = vin_mV / lsb
        dac, eff, bit = {"soft": ("DAC_SOFT", "DAC_SOFT_EFF", 0x01),
                         "hard": ("DAC_HARD", "DAC_HARD_EFF", 0x02)}[path]
        saved = {k: self.read(k) for k in ("MODE", "SOFT_CFG", "SENSE_OFS", "DAC_SOFT", "DAC_HARD")}
        # Both digital trip paths off (no latch during the sweep), FAST_EN off,
        # hysteresis off, SENSE_OFS 0 (contract, spec section 6).
        self.write("MODE", 0x00)
        self.write("SOFT_CFG", 0x00)
        self.write("SENSE_OFS", 0x00)
        if path == "hard":
            self.write("DAC_SOFT", saved["DAC_SOFT"] if other_code is None else other_code)
        else:
            self.write("DAC_HARD", saved["DAC_HARD"] if other_code is None else other_code)
        sweep = []

        def probe(code):
            self.write(dac, code)
            if self.read(eff) != code:
                raise G1VerifyError("%s_EFF != %d with SENSE_OFS 0" % (dac, code))
            self.t.sleep(settle_s)
            f = self._cmp_fraction(bit, n_reads)
            sweep.append((code, f))
            return f >= 0.5

        try:
            if probe(255):
                raise CalibrationError(
                    "%s comparator high at code 255 with %.3f mV: no bracket (input above "
                    "range, SENSE_P open, or offset); reduce Vin" % (path, vin_mV))
            last_low = 255
            code = 255
            c_high = None
            while code > 0:                       # coarse, downward
                code = max(0, code - coarse_step)
                if probe(code):
                    c_high = code
                    break
                last_low = code
            if c_high is None:
                raise CalibrationError("%s comparator never high down to code 0 "
                                       "(SENSE_N open? no input?)" % path)
            for code in range(last_low - 1, c_high - 1, -1):   # fine, downward
                if probe(code):
                    c_high = code
                    break
            # confirm: the two codes below stay high (monotonic)
            confirm = [probe(c) for c in range(c_high - 1, max(-1, c_high - 3), -1)]
            up_high = None
            if both_directions:
                for code in range(max(0, c_high - 4), min(255, c_high + 5) + 1):
                    if probe(code):
                        up_high = code
        finally:
            if restore:
                self.write("SENSE_OFS", saved["SENSE_OFS"])
                self.write("SOFT_CFG", saved["SOFT_CFG"])
                self.write("DAC_SOFT", saved["DAC_SOFT"])
                self.write("DAC_HARD", saved["DAC_HARD"])
                self.write("MODE", saved["MODE"])
        c_cross = c_high + 0.5            # bracketed: c_high high, c_high+1 low
        raw = c_cross - c_ideal
        if path == "hard":
            exp_lo = math.floor(c_ideal) + HARD_KICK_RANGE_LSB[0]
            exp_hi = math.floor(c_ideal) + HARD_KICK_RANGE_LSB[1]
            exp_nom = math.floor(c_ideal) + HARD_KICK_NOMINAL_LSB
            note = ("hard comparator trips ~40-56 LSB below its code (kick offset, simulated); "
                    "crossing code expected ~Cideal+45")
        else:
            exp_lo = math.floor(c_ideal) + SOFT_KICK_RANGE_LSB[0]
            exp_hi = math.floor(c_ideal) + SOFT_KICK_RANGE_LSB[1]
            exp_nom = math.floor(c_ideal)
            note = "soft comparator within 1 LSB of its code (simulated)"
        return {
            "path": path, "vin_mV": vin_mV, "vref_V": vref, "lsb_mV": lsb,
            "c_ideal": c_ideal, "c_high": c_high, "c_cross": c_cross,
            "c_high_upward": up_high,
            "raw_correction": int(round(raw)),
            "raw_correction_exact": raw,
            "monotonic_confirm": all(confirm),
            "expected_c_high_sim": exp_nom, "expected_range_sim": (exp_lo, exp_hi),
            "within_expected_sim": exp_lo <= c_high <= exp_hi + 1,
            "note": note, "n_reads": n_reads, "settle_s": settle_s, "sweep": sweep,
        }

    def calibrate_soft(self, vin_mV, **kw):
        """Soft-comparator crossing at a known interior shunt voltage.

        Contract (spec section 6): external inhibit asserted, a traceable
        interior shunt voltage (nominally 25 mV) at the Kelvin pins, SENSE_OFS 0,
        hysteresis off, other path disabled. Sweeps DAC_SOFT down from 255
        (coarse, then 1-code steps), reads STATUS2.CMP_SOFT n_reads times per
        code after settling, brackets the crossing to one code.
        Ccross = highest code reading high + 0.5; Cideal = Vin / LSB;
        correction = round(Ccross - Cideal) (positive input offset -> positive
        SENSE_OFS). Expected at 25 mV, VREF 1.04 V: Cideal 127.4, crossing
        code 127 (0-1 LSB early, simulated), correction ~0 plus the part's
        sense-amplifier offset / 0.196 mV.
        """
        return self._calibrate("soft", vin_mV, **kw)

    def calibrate_hard(self, vin_mV, **kw):
        """Hard-comparator crossing, same procedure as calibrate_soft.

        Expectation (simulated): the effective hard threshold lies ~45 LSB
        (40-56 over tt/ss/ff on the TRIP NF4 bench; 41-47 on the chip
        netlists at tt/27 C) *below* the DAC code, i.e. the crossing code is
        ~Cideal + 45: at 25 mV about code 172 (range 167-183). The sweep starts
        at 255, >= 56 codes above the expected crossing for Vin <= 38 mV.
        """
        return self._calibrate("hard", vin_mV, **kw)

    def compute_calibration(self, soft_res, hard_res=None):
        """Per-sample calibration from the two crossings.

        SENSE_OFS = soft correction (shared sense-path offset; the soft
        comparator is within 1 LSB in simulation). hard_extra = hard correction
        - SENSE_OFS: the hard comparator's own offset (kick), applied through
        DAC_HARD (independent threshold programming, spec section 6), since one
        shared SENSE_OFS cannot correct both comparators.
        """
        ofs = soft_res["raw_correction"]
        if not -128 <= ofs <= 127:
            raise CalibrationError("SENSE_OFS %d outside -128..127" % ofs)
        cal = {"sense_ofs": ofs, "hard_extra": None, "vref_V": soft_res["vref_V"],
               "lsb_mV": soft_res["lsb_mV"], "soft": soft_res["c_high"],
               "vin_mV": soft_res["vin_mV"]}
        if hard_res is not None:
            cal["hard_extra"] = hard_res["raw_correction"] - ofs
            cal["hard"] = hard_res["c_high"]
        self.calibration = cal
        return cal

    def codes_for(self, hard_mV, soft_mV, allow_uncalibrated=False):
        """DAC codes for target thresholds; refuses clipping (spec section 6)."""
        cal = self.calibration
        if cal is None or cal.get("hard_extra") is None:
            if not allow_uncalibrated:
                raise G1SafetyError("no soft+hard calibration; run calibrate_soft/hard "
                                    "and compute_calibration, or allow_uncalibrated=True")
            cal = {"sense_ofs": 0, "hard_extra": 0, "lsb_mV": lsb_mV(self.vref_V)}
        lsb = cal["lsb_mV"]
        ofs, extra = cal["sense_ofs"], cal["hard_extra"]
        soft_nom = int(round(soft_mV / lsb))
        hard_nom = int(round(hard_mV / lsb))
        dac_soft = soft_nom
        dac_hard = hard_nom + extra
        warnings = []
        for nm, reg in (("DAC_SOFT", dac_soft), ("DAC_HARD", dac_hard)):
            if not 0 <= reg <= 255:
                raise G1SafetyError("%s %d outside 0..255 (target not reachable)" % (nm, reg))
            if not 0 <= reg + ofs <= 255:
                raise G1SafetyError("%s %d + SENSE_OFS %d clips (calibration failure for this "
                                    "target)" % (nm, reg, ofs))
        if not USABLE_HARD_RANGE_MV[0] <= hard_mV <= USABLE_HARD_RANGE_MV[1]:
            warnings.append("hard target %.2f mV outside the usable ~25-40 mV range "
                            "(simulated kick offset)" % hard_mV)
        if soft_mV >= hard_mV:
            warnings.append("soft threshold not below hard threshold")
        if allow_uncalibrated and (self.calibration is None):
            warnings.append("UNCALIBRATED: effective hard threshold ~45 LSB (~8.8 mV) below code")
        return {"DAC_SOFT": dac_soft, "DAC_HARD": dac_hard, "SENSE_OFS": ofs,
                "soft_nominal_code": soft_nom, "hard_nominal_code": hard_nom,
                "driven_soft": dac_soft + ofs, "driven_hard": dac_hard + ofs,
                "warnings": warnings}

    # -- arming ------------------------------------------------------------------
    def soft_time_code(self, soft_time_ms):
        f = self.f_osc_hz or F_OSC_NOMINAL_HZ
        code = int(round(soft_time_ms * 1e-3 * f / 256.0))
        return max(1, min(0xFFFF, code))

    def arm(self, hard_mV, soft_mV, soft_time_ms, hard_n=4, inrush=None,
            retrig=False, fast_en=False, allow_uncalibrated=False):
        """Program and verify a breaker configuration under the inhibit.

        Does NOT release the inhibit: the operator releases it deliberately
        (``set_inhibit(False)``) and then runs ``kelvin_check()`` with load
        current flowing (P9). Timer values use the measured f_OSC if
        ``measure_fosc``/``trim_osc`` ran, else 9.436 MHz (simulated trim 8).
        FAST_EN stays 0 unless requested (feasibility envelope: off).
        """
        self._require_inhibit("arm")
        self._need_version()
        codes = self.codes_for(hard_mV, soft_mV, allow_uncalibrated)
        st = self.soft_time_code(soft_time_ms)
        self.write("MODE", 0x00)                  # paths off while reprogramming
        self.write("SOFT_CFG", 0x00)              # hysteresis off (demo envelope)
        self.write("SENSE_OFS", u8(codes["SENSE_OFS"]))
        self.write("DAC_SOFT", codes["DAC_SOFT"])
        self.write("DAC_HARD", codes["DAC_HARD"])
        self.write("HARD_N", hard_n)
        self.write_soft_time(st)
        if inrush is not None:
            self.write_inrush(inrush)
        for nm in ("DAC_SOFT_EFF", "DAC_HARD_EFF"):
            got = self.read(nm)
            exp = codes["driven_soft" if nm == "DAC_SOFT_EFF" else "driven_hard"]
            if got != exp:
                raise G1VerifyError("%s 0x%02X, expected 0x%02X" % (nm, got, exp))
        mode = MODE_SOFT_EN | MODE_HARD_EN | (MODE_RETRIG if retrig else 0) | \
            (MODE_FAST_EN if fast_en else 0)
        s = self.read("STATUS")
        if s & 1:
            self.command(CTRL_CLEAR)
        self.write("MODE", mode)
        self.config_snapshot = {k: self.read(k) for k in CONFIG_REGS}
        f = self.f_osc_hz or F_OSC_NOMINAL_HZ
        return {"codes": codes, "SOFT_TIME": st,
                "soft_window_ms": st * 256.0 / f * 1e3,
                "hard_filter_us": max(1, hard_n) * 2.0 / f * 1e6,
                "MODE": mode, "f_osc_used_hz": f, "warnings": codes["warnings"]}

    def kelvin_check(self, low_code=5, n_reads=16):
        """P9: with load current flowing, CMP_SOFT must read 1 at a low DAC_SOFT.

        SOFT_EN is cleared for the check so the low code cannot accumulate a
        soft trip; the hard path stays armed. DAC_SOFT and MODE are restored.
        An open SENSE_N makes the breaker blind with no other indication.
        """
        mode = self.read("MODE")
        dac = self.read("DAC_SOFT")
        self.write("MODE", mode & ~MODE_SOFT_EN)
        try:
            self.write("DAC_SOFT", low_code)
            self.t.sleep(200e-6)
            frac = self._cmp_fraction(0x01, n_reads)
        finally:
            self.write("DAC_SOFT", dac)
            self.write("MODE", mode)
        return {"cmp_soft_fraction": frac, "pass": frac >= 0.9, "low_code": low_code}

    # -- watchdog -----------------------------------------------------------------
    def check_config(self):
        """H5 / unexpected-reset check: compare RW registers to the snapshot."""
        bad = {}
        for k, v in self.config_snapshot.items():
            got = self.read(k)
            if got != v:
                bad[k] = (v, got)
        return bad

    def watchdog(self, duration_s=1.0, period_s=5e-3, check_config_every=20,
                 on_fail=None, stall_limit=2):
        """H1 clock watchdog. Alternates CHIP_ID and OSC_CNT reads.

        Fails (assert inhibit, drop EN, call ``on_fail(result)``) when CHIP_ID
        != 0x47, OSC_CNT stops changing for ``stall_limit`` consecutive checks,
        or (every ``check_config_every`` checks) a configuration register no
        longer matches the snapshot (upset or unexpected EN reset, H5).
        OSC_CNT increments every 25.6 us at 10 MHz; period_s must not be a
        multiple of the 1.68 s 16-bit wrap.
        """
        t_end = self.t.now() + duration_s
        last_cnt, last_t = None, None
        stalls, n = 0, 0
        f_est = None
        while self.t.now() < t_end:
            cid = self.read("CHIP_ID")
            if cid != CHIP_ID_VALUE:
                return self._wd_fail("CHIP_ID 0x%02X" % cid, n, on_fail)
            now = self.t.now()
            cnt = self.read_osc_cnt()
            if last_cnt is not None:
                if cnt == last_cnt:
                    stalls += 1
                    if stalls >= stall_limit:
                        return self._wd_fail("OSC_CNT stopped at 0x%04X" % cnt, n, on_fail)
                else:
                    stalls = 0
                    f_est = ((cnt - last_cnt) & 0xFFFF) * 256.0 / (now - last_t)
            last_cnt, last_t = cnt, now
            n += 1
            if check_config_every and self.config_snapshot and n % check_config_every == 0:
                bad = self.check_config()
                if bad:
                    return self._wd_fail("configuration changed: %r" % bad, n, on_fail)
            self.t.sleep(period_s)
        return {"ok": True, "checks": n, "f_osc_est_hz": f_est}

    def _wd_fail(self, reason, n, on_fail):
        res = self.fail_safe(reason)
        res.update({"ok": False, "checks": n})
        if on_fail is not None:
            on_fail(res)
        return res

    # -- temperature sensor -------------------------------------------------------
    def t2f_read(self, mode="ptat", gate_time=1.0, counter=None, temp_C=None,
                 settle_s=10e-3):
        """Select the T2F mode and (optionally) count TEMP_OUT.

        TEMP_OUT is QFN24 lead 14 (die pad 17), a 3.3 V push-pull 16 mA pad.
        Count it with a reciprocal frequency counter: 1 MOhm/high-Z input,
        DC coupled, trigger ~1.65 V, short ground lead, <= 20 pF total load
        (the chip campaign used 20 pF). Gate time 1 s gives 1 Hz resolution
        (0.2 mK at 4.9 kHz/C); 0.1 s is enough for bring-up. Count PTAT and
        REF with the same gate for the ratio readout. Toggling TEMP_OUT adds
        ~100-130 uA to IOVDD (simulated, 20 pF); disable it (TEMP_CTRL = 0)
        for quiescent-current and low-leakage device measurements.

        ``counter(gate_time) -> Hz`` is a user callable for the instrument.
        Expected (simulated, BGR586, typical, PTAT): 1.5074 MHz at 25 C +
        4.9085 kHz/C; chip netlists 1.518 MHz at 27 C. REF: ~1.6 MHz
        (interface value, not re-established with BGR586).
        """
        mode_bit = {"ptat": 0, "ref": T2F_MODE_REF}[mode]
        self.write("TEMP_CTRL", T2F_EN | mode_bit)
        self.t.sleep(settle_s)
        res = {"mode": mode, "gate_time_s": gate_time,
               "resolution_hz": 1.0 / gate_time, "TEMP_CTRL": T2F_EN | mode_bit}
        if mode == "ptat":
            tc = 25.0 if temp_C is None else temp_C
            res["expected_hz_sim"] = T2F_F25_HZ + T2F_SLOPE_HZ_PER_C * (tc - 25.0)
            res["expected_at_C"] = tc
        else:
            res["expected_hz_sim"] = T2F_REF_MODE_HZ_APPROX
        if counter is not None:
            f = counter(gate_time)
            res["f_hz"] = f
            if mode == "ptat":
                res["uncalibrated_temp_C"] = 25.0 + (f - T2F_F25_HZ) / T2F_SLOPE_HZ_PER_C
        return res


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_transport(args):
    if args.transport == "dummy":
        t = DummyTransport(sense_offset_mV=args.dummy_offset_mV)
        t.vin_mV = args.dummy_vin_mV
        t.set_en(True)
        t.idle(100e-6)
        return t
    if args.transport == "spidev":
        return SpidevTransport(bus=args.bus, device=args.device, speed_hz=args.speed)
    if args.transport == "ftdi":
        return FtdiTransport(url=args.url, freq_hz=args.speed)
    raise SystemExit("unknown transport")


def _print(obj):
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def main(argv=None):
    p = argparse.ArgumentParser(description="G1 guardian bench host (map 1.2, r3)")
    p.add_argument("--transport", choices=["dummy", "spidev", "ftdi"], default="dummy")
    p.add_argument("--bus", type=int, default=0)
    p.add_argument("--device", type=int, default=0)
    p.add_argument("--url", default="ftdi://ftdi:232h/1")
    p.add_argument("--speed", type=float, default=1e6, help="SCLK Hz (<= 1 MHz for bring-up)")
    p.add_argument("--allow-fallback", action="store_true", help="accept VERSION 0x11 (r2)")
    p.add_argument("--inhibit-asserted", action="store_true",
                   help="operator declares the external load inhibit ASSERTED")
    p.add_argument("--vref", type=float, default=None, help="measured VREF pin voltage (V)")
    p.add_argument("--dummy-vin-mV", type=float, default=25.0)
    p.add_argument("--dummy-offset-mV", type=float, default=0.0)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("identify")
    sub.add_parser("dump")
    sub.add_parser("status")
    sub.add_parser("safe-defaults")
    sub.add_parser("fosc")
    sub.add_parser("trim-osc")
    sub.add_parser("seu-selftest")
    for nm in ("cal-soft", "cal-hard"):
        c = sub.add_parser(nm)
        c.add_argument("--vin-mV", type=float, required=True)
    a = sub.add_parser("arm")
    a.add_argument("--hard-mV", type=float, required=True)
    a.add_argument("--soft-mV", type=float, required=True)
    a.add_argument("--soft-time-ms", type=float, required=True)
    a.add_argument("--vin-mV", type=float, default=25.0, help="calibration voltage")
    a.add_argument("--uncalibrated", action="store_true")
    w = sub.add_parser("watchdog")
    w.add_argument("--duration", type=float, default=1.0)
    tp = sub.add_parser("t2f")
    tp.add_argument("--mode", choices=["ptat", "ref"], default="ptat")
    tp.add_argument("--gate", type=float, default=1.0)
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return 2
    t = _make_transport(args)
    g = G1(t, vref_V=args.vref, log=lambda m: print("#", m, file=sys.stderr))
    if args.inhibit_asserted:
        g.declare_inhibit(True)
    try:
        info = g.identify(require_version=None if args.allow_fallback else VERSION_R3)
        if args.cmd == "identify":
            _print(info)
        elif args.cmd == "dump":
            _print({k: "0x%02X" % v for k, v in g.dump().items()})
        elif args.cmd == "status":
            _print(g.status())
        elif args.cmd == "safe-defaults":
            _print({"mismatches": g.safe_defaults()})
        elif args.cmd == "fosc":
            _print({"f_osc_hz": g.measure_fosc()})
        elif args.cmd == "trim-osc":
            _print(g.trim_osc())
        elif args.cmd == "seu-selftest":
            _print(g.seu_self_test())
        elif args.cmd in ("cal-soft", "cal-hard"):
            fn = g.calibrate_soft if args.cmd == "cal-soft" else g.calibrate_hard
            r = fn(args.vin_mV)
            r.pop("sweep")
            _print(r)
        elif args.cmd == "arm":
            if not args.uncalibrated:
                s = g.calibrate_soft(args.vin_mV)
                h = g.calibrate_hard(args.vin_mV)
                g.compute_calibration(s, h)
            _print(g.arm(args.hard_mV, args.soft_mV, args.soft_time_ms,
                         allow_uncalibrated=args.uncalibrated))
        elif args.cmd == "watchdog":
            _print(g.watchdog(duration_s=args.duration))
        elif args.cmd == "t2f":
            _print(g.t2f_read(mode=args.mode, gate_time=args.gate))
    except G1Error as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    finally:
        t.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
