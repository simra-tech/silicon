import subprocess, os, sys, math, shutil, random

def run_phase_sweep_corner(label, temp_c, vdd_v, vcc_v, hbt_sec, res_sec, cap_sec, mos_sec):
    raw_file = f"./raw_phase_{temp_c}c.raw"
    tb_file = f"./tb_phase_{temp_c}c.cir"

    if os.path.exists(raw_file):
        os.remove(raw_file)

    random.seed(42)
    dt = 20.0e-12
    t_stop = 40.0e-9
    sigma_n_in = 3.0818e-3

    pwl_points = []
    t_curr = 0.0
    while t_curr <= t_stop + dt:
        val = random.gauss(0.0, sigma_n_in)
        pwl_points.append(f"{t_curr*1e9:.4f}n {val*1e3:.6f}m")
        t_curr += dt

    pwl_str = " ".join(pwl_points)

    tb_spice = f"""* Sampling Phase Sweep across 200ps Clock Period: {label}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerHBT.lib {hbt_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerRES.lib {res_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerCAP.lib {cap_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerMOShv.lib {mos_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerMOSlv.lib {mos_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerDIO.lib dio_tt

.include ./cace_ihp_sg13g2_demo/xschem/simulations/p1_noise_amp.spice

.subckt p1_comp_cand2_phase PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N TRIM_P TRIM_N VCC_HBT VDD VSS
XRC1 VCC_HBT c_n sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1
XRC2 VCC_HBT c_p sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1
XQ1 c_n IN_P e_track sub! npn13G2 Nx=1 mm_ok=1
XQ2 c_p IN_N e_track sub! npn13G2 Nx=1 mm_ok=1
XQ3 c_n ef_p e_latch sub! npn13G2 Nx=1 mm_ok=1
XQ4 c_p ef_n e_latch sub! npn13G2 Nx=1 mm_ok=1
I_PTAT_TAIL e_tail VSS DC 1.958m
XQCLK_TRACK e_track CLK_P e_tail sub! npn13G2 Nx=1 mm_ok=1
XQCLK_LATCH e_latch CLK_N e_tail sub! npn13G2 Nx=1 mm_ok=1
XQEF1 VCC_HBT c_p ef_p sub! npn13G2 Nx=1 mm_ok=1
XQEF2 VCC_HBT c_n ef_n sub! npn13G2 Nx=1 mm_ok=1
XR1_P ef_p g_p sub! rppd w=1.0u l=22.0u m=1 b=0 mm_ok=1
XR2_P g_p VSS sub! rppd w=1.0u l=14.5u m=1 b=0 mm_ok=1
XR1_N ef_n g_n sub! rppd w=1.0u l=22.0u m=1 b=0 mm_ok=1
XR2_N g_n VSS sub! rppd w=1.0u l=14.5u m=1 b=0 mm_ok=1
XM1 cml_out_n g_p e_cmos VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
XM2 cml_out_p g_n e_cmos VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1
XMTAIL e_cmos VDD VSS VSS sg13_lv_nmos w=8.0u l=0.50u ng=1 m=1 mm_ok=1
XM3 cml_out_n cml_out_n VDD VDD sg13_lv_pmos w=8.0u l=0.13u ng=1 m=1 mm_ok=1
XM4 cml_out_p cml_out_n VDD VDD sg13_lv_pmos w=8.0u l=0.13u ng=1 m=1 mm_ok=1
XCDAMP1 cml_out_p VSS cap_cmim w=5.0u l=5.0u m=1 mm_ok=1
XCDAMP2 cml_out_n VSS cap_cmim w=5.0u l=5.0u m=1 mm_ok=1
XRFB raw_inv cml_out_p sub! rppd w=1.0u l=18.05u m=1 b=0 mm_ok=1
XM5 raw_inv cml_out_p VDD VDD sg13_lv_pmos w=2.83u l=0.13u ng=1 m=1 mm_ok=1
XM6 raw_inv cml_out_p VSS VSS sg13_lv_nmos w=2.0u l=0.13u ng=1 m=1 mm_ok=1
XM7 PBIT_RAW raw_inv VDD VDD sg13_lv_pmos w=2.83u l=0.13u ng=1 m=1 mm_ok=1
XM8 PBIT_RAW raw_inv VSS VSS sg13_lv_nmos w=2.0u l=0.13u ng=1 m=1 mm_ok=1
XM9 PBIT_OUT PBIT_RAW VDD VDD sg13_lv_pmos w=2.83u l=0.13u ng=1 m=1 mm_ok=1
XM10 PBIT_OUT PBIT_RAW VSS VSS sg13_lv_nmos w=2.0u l=0.13u ng=1 m=1 mm_ok=1
XQDAC_P c_p TRIM_P e_dac_p sub! npn13G2 Nx=1 mm_ok=1
XRDAC_P e_dac_p VSS sub! rppd w=1.0u l=3.0u m=1 b=0 mm_ok=1
XQDAC_N c_n TRIM_N e_dac_n sub! npn13G2 Nx=1 mm_ok=1
XRDAC_N e_dac_n VSS sub! rppd w=1.0u l=3.0u m=1 b=0 mm_ok=1
XTAP1 VSS sub! ptap1
.ends

.option temp = {temp_c}
.options reltol=1e-4 abstol=1e-12 vntol=1e-6 chgtol=1e-15 method=gear rshunt=1e12

VCC_HBT VCC 0 DC {vcc_v}
VDD VDD 0 DC {vdd_v}
VSS VSS 0 DC 0.000

VCM_CT v_cm 0 DC 1.440
VNOISE_SRC noise_src 0 DC 0.0 PWL({pwl_str})
E_NOISE_P RAW_NOISE_P v_cm noise_src 0 +0.5
E_NOISE_N RAW_NOISE_N v_cm noise_src 0 -0.5

VCLK_P CLK_P 0 PULSE({vdd_v} 0.0 0 20p 20p 80p 200p)
VCLK_N CLK_N 0 PULSE(0.0 {vdd_v} 0 20p 20p 80p 200p)
VTRIM_P TRIM_P 0 DC 0.800
VTRIM_N TRIM_N 0 DC 0.800

XAMP NOISE_AMP_P NOISE_AMP_N RAW_NOISE_P RAW_NOISE_N VCC VSS p1_noise_amp

XCAC1 NOISE_AMP_P in_p cap_cmim w=36.5u l=36.5u m=1
XCAC2 NOISE_AMP_N in_n cap_cmim w=36.5u l=36.5u m=1

* Optimal R_bias = 13.02 kOhm (L = 50 um)
XRBIAS1 VCC in_p sub! rppd w=1.0u l=10.547u m=1 b=0 mm_ok=1
XRBIAS2 in_p VSS sub! rppd w=1.0u l=14.353u m=1 b=0 mm_ok=1
XRBIAS3 VCC in_n sub! rppd w=1.0u l=10.547u m=1 b=0 mm_ok=1
XRBIAS4 in_n VSS sub! rppd w=1.0u l=14.353u m=1 b=0 mm_ok=1

XCOMP PBIT_OUT PBIT_RAW CLK_OUT_DIV in_p in_n CLK_P CLK_N TRIM_P TRIM_N VCC VDD VSS p1_comp_cand2_phase

.control
pre_osdi $PDK_ROOT/libs.tech/ngspice/osdi/psp103.osdi
pre_osdi $PDK_ROOT/libs.tech/ngspice/osdi/psp103_nqs.osdi
set filetype=ascii

save v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
tran 2p 40n 0 2p

linearize v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
write {raw_file} v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
.endc
.end
"""
    with open(tb_file, "w") as f:
        f.write(tb_spice)

    res = subprocess.run(["ngspice", "-b", tb_file], capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        print(f"ERROR: {label} failed!")
        return None

    # Parse raw file with CLK_P saved
    with open(raw_file, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    time_vals, pbit_vals, clk_vals = [], [], []
    in_values = False
    current_row = []

    for line in lines:
        line = line.strip()
        if line.startswith("Values:"):
            in_values = True
            continue
        if in_values:
            parts = line.split()
            if len(parts) == 2:
                if current_row and len(current_row) >= 2:
                    pbit_vals.append(current_row[0])
                    clk_vals.append(current_row[1])
                current_row = []
                try:
                    time_vals.append(float(parts[1]))
                except ValueError:
                    pass
            elif len(parts) == 1:
                try:
                    current_row.append(float(parts[0]))
                except ValueError:
                    pass

    if current_row and len(current_row) >= 2:
        pbit_vals.append(current_row[0])
        clk_vals.append(current_row[1])

    # Fine 10ps step sweep across 200ps clock period
    phase_results = []
    t_start = 2.0e-9
    t_period = 200.0e-12

    for phase_ps in range(0, 200, 10):
        t_sample_offset = (phase_ps * 1.0e-12)
        sampled_bits = []
        k = 0
        while True:
            t_target = t_start + k * t_period + t_sample_offset
            if t_target > (40.0e-9 - 50.0e-12):
                break
            if time_vals:
                idx = min(range(len(time_vals)), key=lambda i: abs(time_vals[i] - t_target))
                if idx < len(pbit_vals):
                    v_pbit = pbit_vals[idx]
                    sampled_bits.append(1 if v_pbit > (vdd_v / 2.0) else 0)
            k += 1

        N = len(sampled_bits)
        N_ones = sum(sampled_bits)
        P_ones = N_ones / N if N > 0 else 0.0

        mean_b = P_ones
        var_b = sum((x - mean_b)**2 for x in sampled_bits)
        rho_1 = sum((sampled_bits[i] - mean_b) * (sampled_bits[i+1] - mean_b) for i in range(N-1)) / var_b if var_b > 0 else 0.0

        phase_results.append((phase_ps, P_ones, rho_1))

    return phase_results

if __name__ == "__main__":
    print("\n" + "="*95)
    print("PERSISTENT SCRIPT: SAMPLING PHASE SWEEP ACROSS 200ps CLOCK PERIOD (R_bias = 13.02 kOhm):")
    print("="*95)

    configs = [
        ("TYPICAL: 27C, TT, VDD=1.20V", 27, 1.20, 2.50, "hbt_typ", "res_typ", "cap_typ", "mos_tt"),
        ("COLD: -40C, FF, VDD=1.32V", -40, 1.32, 2.75, "hbt_typ", "res_typ", "cap_typ", "mos_ff")
    ]

    for label, temp, vdd, vcc, hbt, res_s, cap_s, mos_s in configs:
        res_list = run_phase_sweep_corner(label, temp, vdd, vcc, hbt, res_s, cap_s, mos_s)
        if res_list:
            print(f"\n--- {label} ---")
            print(f"{'Sampling Phase (ps)':<20} | {'P(b=1)':<12} | {'Lag-1 Correlation rho_1':<25} | {'Phase Status'}")
            print("-" * 95)
            valid_count = 0
            for ph_ps, p1, r1 in res_list:
                is_valid = abs(r1) < 0.050
                if is_valid:
                    valid_count += 1
                status = "VALID (< 0.050)" if is_valid else "TRANSITION REGION"
                print(f"{ph_ps:<20.0f} | {p1*100:>8.1f}%   | {r1:>+20.4f}             | {status}")
            
            valid_window_ps = valid_count * 10
            print(f"Total Valid Sampling Window Width (|rho_1| < 0.050): {valid_window_ps} ps out of 200 ps period")

    print("="*95)
