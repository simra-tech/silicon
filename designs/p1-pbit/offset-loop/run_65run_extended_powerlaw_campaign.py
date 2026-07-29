import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING 65-RUN EXTENDED TARGETED NOISE POWER-LAW CAMPAIGN ===")
print("Campaign Matrix:")
print("  - Level 0 (11.5 mV):  10 Seeds (501..510)")
print("  - Level 1 (23.0 mV):  10 Seeds (101..110)")
print("  - Level 2 (45.5 mV):   5 Seeds (201..205)")
print("  - Level 3 (90.0 mV):  20 Seeds (301..320) -- 10 New Seeds Added")
print("  - Level 4 (180.0 mV): 10 Seeds (601..610)")
print("  - Level 5 (360.0 mV): 10 Seeds (701..710) -- 10 New Seeds Added")
print("Total Run Duration: N = 200,000 Clock Cycles (40.0 us at 5.0 GS/s)")
print("Fixed Observation Window: Cycles 150,000 to 200,000 (Exact 50,000 Cycles for All 65 Runs)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps
N_clock_cycles = 300000 # Extended to 300,000 cycles for 360 mV crossing safety
fixed_window_len = 50000 # Fixed 50,000 cycles

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed

target_dac_code = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac_code = target_dac_code - 254                          # 114,473

# 65-Run Matrix
runs_11p5mV = [{"group": "Group 0 (11.5 mV)", "seed": 500 + i, "sigma_n": 11.5e-3} for i in range(1, 11)]
runs_23mV   = [{"group": "Group 1 (23.0 mV)", "seed": 100 + i, "sigma_n": 23.0e-3} for i in range(1, 11)]
runs_45mV   = [{"group": "Group 2 (45.5 mV)", "seed": 200 + i, "sigma_n": 45.5e-3} for i in range(1, 6)]
runs_90mV   = [{"group": "Group 3 (90.0 mV)", "seed": 300 + i, "sigma_n": 90.0e-3} for i in range(1, 21)]
runs_180mV  = [{"group": "Group 4 (180.0 mV)", "seed": 600 + i, "sigma_n": 180.0e-3} for i in range(1, 11)]
runs_360mV  = [{"group": "Group 5 (360.0 mV)", "seed": 700 + i, "sigma_n": 360.0e-3} for i in range(1, 11)]

all_runs = runs_11p5mV + runs_23mV + runs_45mV + runs_90mV + runs_180mV + runs_360mV

results = []

for r in all_runs:
    group_name = r["group"]
    seed_val = r["seed"]
    sigma_n_amp = r["sigma_n"]
    
    # Explicit PRNG seeding per process run
    rng = np.random.default_rng(seed=seed_val)
    
    dac_history = []
    accumulator_val = 0
    curr_dac_code = start_dac_code
    
    for k in range(N_clock_cycles):
        v_res_in = V_in_step - (131072 - curr_dac_code) * delta_V_fine
        v_res_amp = v_res_in * A_op
        
        noise_k = rng.normal(0.0, sigma_n_amp)
        v_latch_diff = v_res_amp + noise_k
        
        b_k = 1 if v_latch_diff > 0 else 0
        accumulator_val += (1 - 2 * b_k)
        curr_dac_code = start_dac_code + int(accumulator_val // 16)
        dac_history.append(curr_dac_code)
    
    dac_arr = np.array(dac_history)
    
    # Null crossing cycle
    crossing_indices = np.where(dac_arr >= target_dac_code)[0]
    has_crossed = len(crossing_indices) > 0
    crossing_cycle = int(crossing_indices[0]) if has_crossed else -1
    
    # FIXED OBSERVATION WINDOW: Exactly cycles 250,000 to 300,000 for EVERY run!
    fixed_settled_phase = dac_arr[250000:300000]
    
    settled_mean = float(np.mean(fixed_settled_phase))
    settled_std = float(np.std(fixed_settled_phase))
    settled_min = int(np.min(fixed_settled_phase))
    settled_max = int(np.max(fixed_settled_phase))
    dither_span = settled_max - settled_min + 1
    
    res = {
        "group": group_name,
        "seed": seed_val,
        "sigma_n_mV": sigma_n_amp * 1e3,
        "M_target": target_dac_code,
        "crossing_cycle": crossing_cycle,
        "crossing_time_us": (crossing_cycle * T_s) * 1e6,
        "settled_mean": settled_mean,
        "settled_error_lsb": abs(settled_mean - target_dac_code),
        "settled_std": settled_std,
        "dither_span": dither_span,
        "obs_window_len": len(fixed_settled_phase)
    }
    results.append(res)

# Verification of window safety: Assert ALL runs crossed before cycle 250,000!
late_crossing_runs = [r for r in results if r["crossing_cycle"] < 0 or r["crossing_cycle"] >= 250000]
print(f"WINDOW INTEGRITY AUDIT: Number of runs crossing after cycle 150,000 = {len(late_crossing_runs)}")
assert len(late_crossing_runs) == 0, f"WINDOW CONFOUND ERROR: Runs failed to settle before cycle 150,000: {late_crossing_runs}"

# Group Analysis across 6 Noise Levels
groups_info = [
    ("Group 0 (11.5 mV)", 11.5),
    ("Group 1 (23.0 mV)", 23.0),
    ("Group 2 (45.5 mV)", 45.5),
    ("Group 3 (90.0 mV)", 90.0),
    ("Group 4 (180.0 mV)", 180.0),
    ("Group 5 (360.0 mV)", 360.0)
]

grp_means_std = []
grp_sds_std = []
grp_means_cross = []
grp_sds_cross = []

print("===============================================================================================================")
print(f"=== 65-RUN EXTENDED TARGETED CAMPAIGN RESULTS (FIXED 50,000-CYCLE WINDOW) ===")
print("===============================================================================================================")
print(f"{'Group':<20} | {'Seed':<6} | {'Noise (mV)':<10} | {'M_target':<9} | {'Crossing Cycle':<14} | {'settled_std (LSBs)':<18} | {'Dither Span':<11}")
print("-" * 110)

for res in results:
    print(f"{res['group']:<20} | {res['seed']:<6} | {res['sigma_n_mV']:<10.1f} | {res['M_target']:<9,} | {res['crossing_cycle']:<14,} | {res['settled_std']:<18.3f} | {res['dither_span']:<11}")

print("===============================================================================================================\n")

print("UNINTERPRETED 6-GROUP MEANS (FIXED WINDOW CYCLES 150,000 TO 200,000 FOR ALL 65 RUNS):")

for grp_label, noise_val in groups_info:
    stds = [r["settled_std"] for r in results if r["sigma_n_mV"] == noise_val]
    crosses = [r["crossing_cycle"] for r in results if r["sigma_n_mV"] == noise_val]
    
    m_std = np.mean(stds); sd_std = np.std(stds, ddof=1)
    m_cross = np.mean(crosses); sd_cross = np.std(crosses, ddof=1)
    
    grp_means_std.append(m_std); grp_sds_std.append(sd_std)
    grp_means_cross.append(m_cross); grp_sds_cross.append(sd_cross)
    
    print(f"  * {grp_label} (N={len(stds)}):")
    print(f"    - Individual settled_std: {np.round(stds, 3).tolist()}")
    print(f"    - Mean settled_std:       {m_std:.3f} +/- {sd_std:.3f} Fine LSBs")
    print(f"    - Mean Crossing Cycle:    {m_cross:,.0f} +/- {sd_cross:,.0f} cycles ({m_cross*T_s*1e6:.2f} us)")

# 1. 4-Level Power Law Fit (11.5 mV to 90.0 mV)
runs_4lvl = [r for r in results if r["sigma_n_mV"] <= 90.0]
x_log_4 = np.array([np.log(r["sigma_n_mV"]) for r in runs_4lvl])
y_log_4 = np.array([np.log(r["settled_std"]) for r in runs_4lvl])

poly4, cov4 = np.polyfit(x_log_4, y_log_4, 1, cov=True)
alpha_4lvl = poly4[0]
alpha_4lvl_err = np.sqrt(cov4[0, 0])

# Weighted WLS on 4 Group Means (11.5, 23, 45.5, 90 mV)
x_g4 = np.log([11.5, 23.0, 45.5, 90.0])
y_g4 = np.log(grp_means_std[:4])
se_g4 = np.array([grp_sds_std[0]/np.sqrt(10), grp_sds_std[1]/np.sqrt(10), grp_sds_std[2]/np.sqrt(5), grp_sds_std[3]/np.sqrt(20)]) / grp_means_std[:4]
weights_g4 = 1.0 / se_g4**2

poly4_w, cov4_w = np.polyfit(x_g4, y_g4, 1, w=np.sqrt(weights_g4), cov=True)
alpha_4lvl_wls = poly4_w[0]
alpha_4lvl_wls_err = np.sqrt(cov4_w[0, 0])

# Chi-squared on 4 Group Means
y_pred_4 = poly4_w[0] * x_g4 + poly4_w[1]
chi2_4lvl = np.sum(((y_g4 - y_pred_4) / se_g4)**2)

# 2. 6-Level Full Fit (11.5 mV to 360.0 mV)
x_log_6 = np.array([np.log(r["sigma_n_mV"]) for r in results])
y_log_6 = np.array([np.log(r["settled_std"]) for r in results])

poly6, cov6 = np.polyfit(x_log_6, y_log_6, 1, cov=True)
alpha_6lvl = poly6[0]
alpha_6lvl_err = np.sqrt(cov6[0, 0])

x_g6 = np.log([11.5, 23.0, 45.5, 90.0, 180.0, 360.0])
y_g6 = np.log(grp_means_std)
se_g6 = np.array([grp_sds_std[0]/np.sqrt(10), grp_sds_std[1]/np.sqrt(10), grp_sds_std[2]/np.sqrt(5), grp_sds_std[3]/np.sqrt(20), grp_sds_std[4]/np.sqrt(10), grp_sds_std[5]/np.sqrt(10)]) / grp_means_std
weights_g6 = 1.0 / se_g6**2

poly6_w, cov6_w = np.polyfit(x_g6, y_g6, 1, w=np.sqrt(weights_g6), cov=True)
alpha_6lvl_wls = poly6_w[0]
alpha_6lvl_wls_err = np.sqrt(cov6_w[0, 0])

y_pred_6 = poly6_w[0] * x_g6 + poly6_w[1]
chi2_6lvl = np.sum(((y_g6 - y_pred_6) / se_g6)**2)

print("\n===============================================================================================================")
print("=== REGRESSION AUDIT & CHI-SQUARED MODEL EVALUATION ===")
print("===============================================================================================================")
print(f" 1. Clean 4-Level Power-Law Fit (11.5 mV to 90.0 mV, N=45 Runs):")
print(f"    - OLS Exponent alpha:       alpha = {alpha_4lvl:.3f} +/- {alpha_4lvl_err:.3f}")
print(f"    - WLS Weighted Exponent:    alpha_wls = {alpha_4lvl_wls:.3f} +/- {alpha_4lvl_wls_err:.3f}")
print(f"    - Weighted Chi-Squared:     chi2 = {chi2_4lvl:.3f} on df=2 degrees of freedom (p = {1.0 - np.exp(-chi2_4lvl/2):.3f})")

print(f"\n 2. Full 6-Level Fit (11.5 mV to 360.0 mV, All N=65 Runs):")
print(f"    - OLS Exponent alpha:       alpha = {alpha_6lvl:.3f} +/- {alpha_6lvl_err:.3f}")
print(f"    - WLS Weighted Exponent:    alpha_wls = {alpha_6lvl_wls:.3f} +/- {alpha_6lvl_wls_err:.3f}")
print(f"    - Weighted Chi-Squared:     chi2 = {chi2_6lvl:.3f} on df=4 degrees of freedom")

# Save CSV
out_csv = "p1_65run_extended_noise_campaign_results.csv"
header = ["group", "seed", "sigma_n_mV", "M_target", "crossing_cycle", "crossing_time_us", "settled_mean", "settled_error_lsb", "settled_std", "dither_span", "obs_window_len"]
data_rows = [[r["group"], r["seed"], r["sigma_n_mV"], r["M_target"], r["crossing_cycle"], r["crossing_time_us"], r["settled_mean"], r["settled_error_lsb"], r["settled_std"], r["dither_span"], r["obs_window_len"]] for r in results]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved 65-run extended noise campaign results to '{out_csv}'.")
