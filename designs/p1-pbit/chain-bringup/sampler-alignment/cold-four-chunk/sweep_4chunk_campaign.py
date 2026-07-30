import os, sys, math, hashlib

# Candidate 2 CMOS Inverter Switching Thresholds V_trip:
# TYPICAL (27C, TT, VDD=1.20V) : V_trip = 0.593 V

CHUNK_SEED_MAP = {
    0: 42,
    1: 43,
    2: 44,
    3: 45
}

def generate_chunk_pwl_and_deck(label, chunk_id, seed, temp_c, vdd_v, vcc_v, hbt_sec, res_sec, cap_sec, mos_sec, vtrip_v):
    raw_file = f"raw_chunk{chunk_id}_{temp_c}c.raw"
    tb_file = f"tb_chunk{chunk_id}_{temp_c}c.cir"

    import random
    random.seed(seed)
    sigma_n_in = 3.0818e-3

    # Schedule: Exactly 22,500 emitted PWL points
    # 1. Coarse Preamble: 500 points at dt=200ps over [0.000ns .. 99.800ns]
    # 2. Fine Window: 22,000 points at dt=2ps over [100.000ns .. 143.998ns]
    pwl_points = []
    
    # Coarse Preamble (500 points: i = 0 .. 499)
    dt_coarse = 0.200e-9
    for i in range(500):
        t_curr = i * dt_coarse
        val = random.gauss(0.0, sigma_n_in)
        pwl_points.append(f"{t_curr*1e9:.4f}n {val*1e3:.6f}m")

    # Fine Window (22,000 points: j = 0 .. 21,999)
    dt_fine = 2.0e-12
    t_base = 100.000e-9
    for j in range(22000):
        t_curr = t_base + j * dt_fine
        val = random.gauss(0.0, sigma_n_in)
        pwl_points.append(f"{t_curr*1e9:.4f}n {val*1e3:.6f}m")

    pwl_str = " ".join(pwl_points)

    tb_spice = f"""* 44ns Measurement Window Chunked Sweep (Chunk {chunk_id}, Seed {seed}): {label}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerHBT.lib {hbt_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerRES.lib {res_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerCAP.lib {cap_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerMOShv.lib {mos_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerMOSlv.lib {mos_sec}
.lib $PDK_ROOT/libs.tech/ngspice/models/cornerDIO.lib dio_tt

.include ./p1_noise_amp.spice

.subckt p1_comp_cand2_chunk PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N TRIM_P TRIM_N VCC_HBT VDD VSS
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

* Candidate 2 Exact Shunt Feedback Resistor: l=18.5u (4.88 kOhm)
XRFB raw_inv cml_out_p sub! rppd w=1.0u l=18.5u m=1 b=0 mm_ok=1

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

XCOMP PBIT_OUT PBIT_RAW CLK_OUT_DIV in_p in_n CLK_P CLK_N TRIM_P TRIM_N VCC VDD VSS p1_comp_cand2_chunk

.control
pre_osdi $PDK_ROOT/libs.tech/ngspice/osdi/psp103.osdi
pre_osdi $PDK_ROOT/libs.tech/ngspice/osdi/psp103_nqs.osdi
set filetype=ascii

save v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
tran 2p 144n 100n 2p

linearize v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
write {raw_file} v(PBIT_OUT) v(CLK_P) v(xcomp.cml_out_p)
.endc
.end
"""
    with open(tb_file, "w") as f:
        f.write(tb_spice)

    return tb_file, raw_file

def parse_chunk_raw(raw_file, vtrip_v):
    """
    Fail-closed parser for ASCII raw dataset.
    Requires strictly increasing time vector and complete coverage over target window [100.0ns, 143.998ns].
    For each target instant, requires nearest-point error <= 1.1ps and 220 distinct selected indices; otherwise raises.
    Computes N=220, se=1/sqrt(220), and rho_1 within chunk. Reports rho_1 as None ("UNAVAILABLE") if bit variance is zero.
    """
    if not os.path.exists(raw_file):
        raise FileNotFoundError(f"Fail-closed check failed: raw file {raw_file} does not exist!")

    with open(raw_file, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    time_vals, pbit_vals = [], []
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
                if current_row and len(current_row) >= 1:
                    pbit_vals.append(current_row[0])
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

    if current_row and len(current_row) >= 1:
        pbit_vals.append(current_row[0])

    if not time_vals or len(time_vals) != len(pbit_vals):
        raise ValueError(f"Fail-closed check failed: malformed raw data vectors in {raw_file}!")

    # Guard 1: Require strictly increasing time vector
    for i in range(len(time_vals) - 1):
        if time_vals[i+1] <= time_vals[i]:
            raise ValueError(f"Fail-closed check failed: non-monotonic time vector at index {i} in {raw_file}!")

    # Guard 2: Require complete coverage over target span [100.0ns, 143.998ns]
    t_start = 100.0e-9
    t_end_req = 143.998e-9
    t_period = 200.0e-12

    if time_vals[0] > t_start or time_vals[-1] < t_end_req:
        raise ValueError(f"Fail-closed check failed: raw time span [{time_vals[0]*1e9:.3f}ns, {time_vals[-1]*1e9:.3f}ns] does not cover required [{t_start*1e9:.3f}ns, {t_end_req*1e9:.3f}ns] in {raw_file}!")

    chunk_phase_results = {}

    # Phases 0..190ps in 10ps steps
    for phase_ps in range(0, 200, 10):
        t_offset = phase_ps * 1.0e-12
        bits = []
        selected_indices = []

        for k in range(220):
            t_target = t_start + k * t_period + t_offset
            # Binary search or min lookup for nearest index
            idx = min(range(len(time_vals)), key=lambda i: abs(time_vals[i] - t_target))
            err_sec = abs(time_vals[idx] - t_target)

            # Guard 3: Nearest point error must be <= 1.1ps
            if err_sec > 1.1e-12:
                raise ValueError(f"Fail-closed check failed: target t={t_target*1e9:.6f}ns has nearest-point error {err_sec*1e12:.3f}ps > 1.1ps in {raw_file}!")

            selected_indices.append(idx)
            v_pbit = pbit_vals[idx]
            bits.append(1 if v_pbit > vtrip_v else 0)

        # Guard 4: Require exactly 220 distinct selected indices
        if len(set(selected_indices)) != 220:
            raise ValueError(f"Fail-closed check failed: duplicate time indices selected for phase {phase_ps}ps in {raw_file}!")

        N = len(bits)
        se_chunk = 1.0 / math.sqrt(N)
        mean_b = sum(bits) / N
        var_b = sum((x - mean_b)**2 for x in bits)

        if var_b > 0:
            rho1 = sum((bits[i] - mean_b) * (bits[i+1] - mean_b) for i in range(N-1)) / var_b
        else:
            rho1 = None  # Explicitly UNAVAILABLE rather than 0.0 when bit variance is zero

        chunk_phase_results[phase_ps] = {
            "bits": bits,
            "N": N,
            "se": se_chunk,
            "p1": mean_b,
            "rho1": rho1
        }

    return chunk_phase_results

def aggregate_4chunk_results(temp_c, vtrip_v):
    """
    Fail-closed aggregation that requires all four chunk raw results to exist.
    If ANY chunk has rho1 = None for a phase, publishes aggregate rho1 as None (UNAVAILABLE) for that phase.
    Never averages a subset of valid chunks.
    Reports pooled N=880 and se=0.03371.
    """
    all_chunk_results = []
    for chunk_id in range(4):
        raw_file = f"raw_chunk{chunk_id}_{temp_c}c.raw"
        res = parse_chunk_raw(raw_file, vtrip_v)
        all_chunk_results.append(res)

    aggregated_phases = {}
    pooled_N = 880
    pooled_se = 1.0 / math.sqrt(pooled_N)  # 0.03371

    for phase_ps in range(0, 200, 10):
        chunk_rhos = []
        chunk_p1s = []

        all_rhos_valid = True
        for cid in range(4):
            c_res = all_chunk_results[cid][phase_ps]
            chunk_p1s.append(c_res["p1"])
            if c_res["rho1"] is None:
                all_rhos_valid = False
            else:
                chunk_rhos.append(c_res["rho1"])

        avg_p1 = sum(chunk_p1s) / len(chunk_p1s) if len(chunk_p1s) == 4 else 0.0

        # Require all 4 chunk rhos to be valid; otherwise publish aggregate rho as None
        if all_rhos_valid and len(chunk_rhos) == 4:
            avg_rho1 = sum(chunk_rhos) / 4.0
        else:
            avg_rho1 = None

        aggregated_phases[phase_ps] = {
            "p1_avg": avg_p1,
            "rho1_avg": avg_rho1,
            "pooled_N": pooled_N,
            "pooled_se": pooled_se,
            "chunk_identities": [0, 1, 2, 3],
            "chunk_Ns": [all_chunk_results[cid][phase_ps]["N"] for cid in range(4)]
        }

    return aggregated_phases

if __name__ == "__main__":
    # Generate Chunk 0 Deck for static inspection (NO SIMULATOR INVOCATION)
    tb_0, raw_0 = generate_chunk_pwl_and_deck(
        label="TYPICAL: 27C, TT, VDD=1.20V (Vtrip=0.593V)",
        chunk_id=0,
        seed=CHUNK_SEED_MAP[0],
        temp_c=27,
        vdd_v=1.20,
        vcc_v=2.50,
        hbt_sec="hbt_typ",
        res_sec="res_typ",
        cap_sec="cap_typ",
        mos_sec="mos_tt",
        vtrip_v=0.593
    )
    print(f"Generated Chunk 0 Deck: {tb_0}")
