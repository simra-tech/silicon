import subprocess, time, os, sys, hashlib
import concurrent.futures
import numpy as np

run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

orig_corner_path = '$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib'

# Native Calibrated TRNOISE parameters for R = 10 Ohm
S0 = 4.51e-17 # V^2 / Hz
NT_ps = 2.0
NT_sec = 2.0e-12
NA_v   = np.sqrt(S0 / (2.0 * NT_sec)) # 3.3578 mV
R_damp = 10.0
IA_a   = NA_v / R_damp # 335.78 uA

T_sim_segment = 200e-9 # 200 ns per segment

def run_ac_wideband_segment(rate_ghz, seg_idx):
    out_txt = os.path.join(run_dir, f'pbit_raw_ac_wb10_{rate_ghz:.1f}g_seg{seg_idx}.txt')
    log_file = os.path.join(run_dir, f'ngspice_ac_wb10_{rate_ghz:.1f}g_seg{seg_idx}.log')
    op_file  = os.path.join(run_dir, f'pbit_op_ac_wb10_{rate_ghz:.1f}g_seg{seg_idx}.txt')
    deck_file = os.path.join(run_dir, f'tb_p1_ac_wb10_{rate_ghz:.1f}g_seg{seg_idx}.spice')
    
    clock_period_ps = 1000.0 / rate_ghz
    pw_ps = clock_period_ps * 0.40 # 40% pulse width
    
    sp_content = f'''* Production AC-Coupled Wideband TRNOISE 10-Seg Rate Map Rate {rate_ghz:.1f} GS/s Seg {seg_idx}
.lib {orig_corner_path} hbt_typ
.lib $PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt

.subckt p1_noise_gen RAW_NOISE_P RAW_NOISE_N VCC VSS
XQ1 RAW_NOISE_N b1_q1 e VSS npn13G2 Nx=1
XQ2 RAW_NOISE_P b2_q2 e VSS npn13G2 Nx=1
RC1 VCC RAW_NOISE_N 1.0k m=1
RC2 VCC RAW_NOISE_P 1.0k m=1
R_TAIL e VSS 316

VBM b_cm VSS DC 0.872

* AC-Coupled Norton Current Sources via 100nF DC-Blocking Caps
I_NOISE_P b_cm b2_ac DC 0 TRNOISE({IA_a:.6e} {NT_ps:.1f}p 0 0)
I_NOISE_N b_cm b1_ac DC 0 TRNOISE({IA_a:.6e} {NT_ps:.1f}p 0 0)

C_AC_P b2_ac b2_q2 100n
C_AC_N b1_ac b1_q1 100n

R1_DAMP b_cm b1_q1 10.0
R2_DAMP b_cm b2_q2 10.0
.ends

.subckt p1_noise_amp OUT_P OUT_N IN_P IN_N VCC VSS
R_DAMP_IN1 IN_P in_p_q1 100
R_DAMP_IN2 IN_N in_n_q2 100

XQ1 c1_n in_p_q1 e1_1 VSS npn13G2 Nx=2
XQ2 c1_p in_n_q2 e1_2 VSS npn13G2 Nx=2
RE1_1 e1_1 e1_common 15
RE1_2 e1_2 e1_common 15
RC1_1 VCC c1_n 240 m=1
RC1_2 VCC c1_p 240 m=1
R_TAIL1 e1_common VSS 316

XQEF1 VCC c1_p b2_p VSS npn13G2 Nx=1
XQEF2 VCC c1_n b2_n VSS npn13G2 Nx=1
REF1 b2_p VSS 5k m=1
REF2 b2_n VSS 5k m=1

* Stage 2
XQ3 OUT_N b2_p e2_1 VSS npn13G2 Nx=1
XQ4 OUT_P b2_n e2_2 VSS npn13G2 Nx=1
RE2_1 e2_1 e2_common 15
RE2_2 e2_2 e2_common 15
RC2_1 VCC OUT_N 240 m=1
RC2_2 VCC OUT_P 240 m=1
R_TAIL2 e2_common VSS 316
.ends

.subckt p1_comparator PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N VCC_HBT VDD VSS params: trim_val=512
RIN1 IN_P in_p_int 100
RIN2 IN_N in_n_int 100

RCLK1 CLK_P clk_p_int 100
RCLK2 CLK_N clk_n_int 100

XQEF_IN1 VCC_HBT in_p_int b_latch_p VSS npn13G2 Nx=1
XQEF_IN2 VCC_HBT in_n_int b_latch_n VSS npn13G2 Nx=1
REF_IN1 b_latch_p VSS 5k m=1
REF_IN2 b_latch_n VSS 5k m=1

XQCLK_TRACK e_track clk_p_int e_tail VSS npn13G2 Nx=1
XQCLK_LATCH e_latch clk_n_int e_tail VSS npn13G2 Nx=1
ISET e_tail VSS DC 2.0m

C_ETRACK e_track VSS 50f
C_ELATCH e_latch VSS 50f

XQ1 c_n b_latch_p e_track VSS npn13G2 Nx=1
XQ2 c_p b_latch_n e_track VSS npn13G2 Nx=1

XQ3 c_n c_p e_latch VSS npn13G2 Nx=1
XQ4 c_p c_n e_latch VSS npn13G2 Nx=1

RC1 VCC_HBT c_n 150 m=1
RC2 VCC_HBT c_p 150 m=1

ITRIM_P c_p VSS DC '66.85u + (trim_val - 512) * 0.1307u'
ITRIM_N c_n VSS DC '66.85u - (trim_val - 512) * 0.1307u'

XQEF1 VCC_HBT c_p ef_p VSS npn13G2 Nx=1
XQEF2 VCC_HBT c_n ef_n VSS npn13G2 Nx=1
REF1 ef_p VSS 5k m=1
REF2 ef_n VSS 5k m=1

R1_P ef_p g_p 10k m=1
R2_P g_p VSS 10k m=1
R1_N ef_n g_n 10k m=1
R2_N g_n VSS 10k m=1

XQBUF1 VCC_HBT g_p cml_out_p VSS npn13G2 Nx=1
XQBUF2 VCC_HBT g_n cml_out_n VSS npn13G2 Nx=1
RBUF1 cml_out_p VSS 5k m=1
RBUF2 cml_out_n VSS 5k m=1
.ends

XGEN gen_p gen_n vcc_hbt 0 p1_noise_gen
XAMP amp_p amp_n gen_p gen_n vcc_hbt 0 p1_noise_amp
XCOMP pbit_out raw clk_div amp_p amp_n clk_p clk_n vcc_hbt vdd 0 p1_comparator trim_val=512

VCC_HBT vcc_hbt 0 DC 2.50
VDD vdd 0 DC 1.20

VCLK_P clk_p 0 PULSE(0.775 0.925 0p 20p 20p {pw_ps:.1f}p {clock_period_ps:.1f}p)
VCLK_N clk_n 0 PULSE(0.925 0.775 0p 20p 20p {pw_ps:.1f}p {clock_period_ps:.1f}p)

.options method=gear reltol=1e-3

.control
op
wrdata {op_file} v(xgen.xq1.t) v(xamp.xq1.t) v(gen_p) v(amp_p) v(xcomp.b_latch_p)
tran 20p 200n 0 20p
setplot tran1
wrdata {out_txt} v(amp_p) v(amp_n) v(xcomp.c_p) v(xcomp.c_n) v(xcomp.b_latch_p) v(xcomp.b_latch_n)
quit
.endc
.end
'''

    if not os.path.exists(out_txt) or os.path.getsize(out_txt) < 100:
        with open(deck_file, 'w') as f: f.write(sp_content)
        res = subprocess.run(['ngspice', '-b', deck_file], capture_output=True, text=True)
        with open(log_file, 'w') as f: f.write(res.stdout + '\n=== STDERR ===\n' + res.stderr)

    return (rate_ghz, seg_idx)

if __name__ == '__main__':
    pass
