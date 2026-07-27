v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {devices/code_shown.sym} 0 0 0 0 {name=NGSPICE only_toplevel=true
value="
.lib $PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib CACE\{corner\}
.options temp=CACE\{temperature\}
.include CACE\{DUT_path\}

X1 in out vdd vss ihp_sg13g2_inv

VVDD vdd vss DC CACE\{vdd\}
VVSS vss 0   DC 0.0
VVIN in vss DC 0.6

.control
osdi $PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
dc VVIN 0 CACE\{vdd\} 0.0005
meas dc vth FIND v(in) WHEN v(out)='CACE\{vdd\}/2'
echo $&vth > CACE\{simpath\}/CACE\{filename\}_CACE\{N\}.data
quit
.endc
.end
"
}
