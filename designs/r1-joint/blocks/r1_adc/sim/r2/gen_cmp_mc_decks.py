#!/usr/bin/env python3
"""Write sim/r2/tb_cmp2_offset_mc.cir and sim/r2/tb_cmp2_trnoise.cir for the chosen comparator r1_cmp2 (defaults).

offset MC: 30 copies of r1_cmp2 from r1_adc_r2_mm.spice (mos_tt_mismatch, mmos=1, every MOS draws its own
  mismatch), common bias. Differential input ramps from -@VR@ to +@VR@ over @NC@ clock cycles (30 MHz, as in the
  ADC). The offset of a copy is the input at which its decision changes (post_cmp2_mc.py).
transient noise (method B): 6 copies of the nominal r1_cmp2, each with its own TRNOISE source in series with inp
  (white, one-sided PSD @SN@ V^2/Hz, sample step 20 ps -> rms NA = sqrt(S/(2*20ps))), at fixed inputs
  -2..+3 x 45 uV. The fraction of 'high' decisions per input over @NC@ cycles gives sigma (probit fit).
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
HDR = ["* @TITLE@",
       ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib @CORNER@",
       ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ",
       ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib mos_tt",
       ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ",
       ".temp @TEMP@",
       ".option reltol=1e-4 vntol=1e-7 abstol=1e-13 method=gear",
       "Vdd vdd 0 @VDD@",
       "Vclk clk 0 PULSE(0 @VDD@ 2n 50p 50p 16.6167n 33.3333n)",
       "Vclkb clkb 0 PULSE(@VDD@ 0 2n 50p 50p 16.6167n 33.3333n)"]


def offset():
    L = [l.replace("@TITLE@", "tb_cmp2_offset_mc.cir -- r1_cmp2 offset, 30 mismatch copies") for l in HDR]
    L.insert(5, ".include schematic/r1_adc_r2_mm.spice")
    L += [".param mmos=1", "XB vbp vdd 0 r1_cmp2_bias ib=14u",
          "Bvd vd 0 v=-@VR@ + 2*@VR@*time/(@NC@*33.3333n)",
          "Bp inp 0 v=@VCM@ + v(vd)/2", "Bn inn 0 v=@VCM@ - v(vd)/2"]
    sv = []
    for i in range(30):
        L.append("X%d inp inn clk clkb op%d on%d vbp vdd 0 r1_cmp2" % (i, i, i))
        sv.append("v(op%d)" % i)
    tstop = "{:.6g}".format(0)
    L += [".control", "set num_threads=1", "save " + " ".join(sv) + " v(vd)",
          "tran 0.1n @TSTOP@ 0 0.5n", "write @RAW@/offset.raw", ".endc", ".end"]
    open(os.path.join(HERE, "tb_cmp2_offset_mc.cir"), "w").write("\n".join(L) + "\n")


def trnoise():
    L = [l.replace("@TITLE@", "tb_cmp2_trnoise.cir -- r1_cmp2 transient noise check (method B)") for l in HDR]
    L.insert(5, ".include schematic/r1_adc_r2.spice")
    L += ["XB vbp vdd 0 r1_cmp2_bias ib=14u", ".param na={sqrt(@SN@/(2*20e-12))}", "Vcm cm 0 @VCM@"]
    sv = []
    for i, k in enumerate(range(-2, 4)):
        vin = k * 45e-6
        L.append("Vn%d inp%d np%d TRNOISE({na} 20p 0 0)" % (i, i, i))
        L.append("Vp%d np%d cm %.7g" % (i, i, vin / 2))
        L.append("Vm%d inn%d cm %.7g" % (i, i, -vin / 2))
        L.append("X%d inp%d inn%d clk clkb op%d on%d vbp vdd 0 r1_cmp2" % (i, i, i, i, i))
        sv.append("v(op%d)" % i)
    L += [".control", "set num_threads=1", "save " + " ".join(sv),
          "tran 0.1n @TSTOP@ 0 20p", "write @RAW@/trnoise.raw", ".endc", ".end"]
    open(os.path.join(HERE, "tb_cmp2_trnoise.cir"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    offset()
    trnoise()
