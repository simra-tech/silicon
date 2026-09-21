from pathlib import Path
import subprocess
here=Path(__file__).resolve().parent
src=here.parent/'postlayout/g1_bgr_pex.spice'
(here/'pex_mm.spice').write_text('\n'.join(x+' mm_ok=1' if x.startswith(('XM','XQ','XR')) else x for x in src.read_text().splitlines())+'\n')
p='/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/'
deck='* BGR PEX MC parameter introspection\n'+''.join(f'.lib {p}{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_typ_mismatch'),('cornerMOShv','mos_tt_mismatch'),('cornerRES','res_typ_mismatch')])+'''.include pex_mm.spice
.option seed=42001 gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7
.global sub!
Vsub sub! 0 0
Vdd vdd 0 3.3
Vr4 r4 0 0
Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr
Vload iptat 0 1
Cload vref 0 1p
.control
op
show n.xbgr.xm34.nsg13_hv_nmos
show q.xbgr.xq56.qnpn13g2
show n.xbgr.xr16.nr1
print v(vref)
quit
.endc
.end
'''
(here/'pilot.cir').write_text(deck)
p=subprocess.run(['ngspice','-b','pilot.cir'],cwd=here,stdout=(here/'pilot.log').open('w'),stderr=subprocess.STDOUT,timeout=120)
print(p.returncode)
