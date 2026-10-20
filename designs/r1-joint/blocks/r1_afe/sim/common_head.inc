* (template fragment, inserted by run_afe.py) models, netlist, supplies, bias, gain controls
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib @@RES@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib @@CAP@@
.include ../schematic/r1_afe.spice
.temp @@TEMP@@
.param VDDA=@@VDDA@@ VCMI=@@VCMI@@
.option gmin=1e-13 itl1=400 itl2=200
Vdd vdd 0 dc {VDDA} ac @@ACVDD@@
Vcm2 vcm2 0 dc 0.6
* bias: 10 uA per OTA from r1_bgr (ideal here)
Ib1 vdd ib_s1 10u
Ib2 vdd ib_s2 10u
Ib3 vdd ib_c1 10u
Ib4 vdd ib_c2 10u
* gain controls (3.3 V logic, from the PGA_GAIN decoder)
Vc1 c1 0 dc 0
Vc2 c2 0 dc 0
Vc3 c3 0 dc 0
Vc4 c4 0 dc 0
