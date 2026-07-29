import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING STANDARDIZED POST-CROSSING CAMPAIGN (DROPPING R_W1 EVERYWHERE) ===")
print("Standardized Observation Protocol: Starting ALL Measurements at k_cross + 100,000 Cycles (Dropping R_W1)")
print("Extending Group 6 (128.0 mV, 10 Seeds 801..810) to 8 Relative Windows (400,000 Post-Crossing Cycles)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed

target_dac_code = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac_code = target_dac_code - 254                          # 114,473

# Campaign Matrix:
# Levels 0..3 (11.5, 23, 45.5, 90 mV): 4 Relative Windows (Evaluate R_W2..R_W4, drop R_W1)
# Levels 4, 5, 6 (128, 180, 360 mV): 8 Relative Windows (Evaluate R_W2..R_W8, drop R_W1)

groups_config = [
    ("Group 0 (11.5 mV)", 11.5, 10, range(501, 511), 4),
    ("Group 1 (23.0 mV)", 23.0, 10, range(101, 111), 4),
    ("Group 2 (45.5 mV)", 45.5,  5, range(201, 206), 4),
    ("Group 3 (90.0 mV)", 90.0, 20, range(301, 321), 4),
    ("Group 6 (128.0 mV)",128.0, 10, range(801, 811), 8),
    ("Group 4 (180.0 mV)",180.0, 10, range(601, 611), 8),
    ("Group 5 (360.0 mV)",360.0, 10, range(701, 711), 8)
]

results = []
trajectory_dict = {}

for grp_label, noise_val, n_seeds, seed_range, n_windows in groups_config:
    for seed_val in seed_range:
        sigma_n_amp = noise_val * 1e-3
        rng = np.random.default_rng(seed=seed_val)
        
        dac_history = []
        accumulator_val = 0
        curr_dac_code = start_dac_code
        
        k = 0
        crossing_cycle = -1
        required_post_cycles = n_windows * 50000 + 50000 # 50k buffer + n_windows * 50k
        
        while True:
            v_res_in = V_in_step - (131072 - curr_dac_code) * delta_V_fine
            v_res_amp = v_res_in * A_op
            
            noise_k = rng.normal(0.0, sigma_n_amp)
            v_latch_diff = v_res_amp + noise_k
            
            b_k = 1 if v_latch_diff > 0 else 0
            accumulator_val += (1 - 2 * b_k)
            curr_dac_code = start_dac_code + int(accumulator_val // 16)
            dac_history.append(curr_dac_code)
            
            if crossing_cycle < 0 and curr_dac_code >= target_dac_code:
                crossing_cycle = k
            
            k += 1
            if crossing_cycle >= 0 and k >= (crossing_cycle + required_post_cycles):
                break
            if k >= 900000:
                break
        
        dac_arr = np.array(dac_history, dtype=np.int32)
        
        traj_key = f"standardized_{grp_label.replace(' ', '_')}_seed_{seed_val}"
        trajectory_dict[traj_key] = dac_arr
        
        # Evaluate all relative windows R_W1..R_Wn
        window_stds = []
        for w in range(1, n_windows + 1):
            w_start = crossing_cycle + w * 50000
            w_end = crossing_cycle + (w + 1) * 50000
            w_phase = dac_arr[w_start:w_end]
            window_stds.append(float(np.std(w_phase)))
        
        # DROPPING R_W1: Compute settled_std using R_W2..R_Wn (windows 1..n-1 in 0-based indexing)
        settled_std_rw2_plus = float(np.mean(window_stds[1:]))
        
        res = {
            "group": grp_label,
            "seed": seed_val,
            "sigma_n_mV": noise_val,
            "M_target": target_dac_code,
            "crossing_cycle": crossing_cycle,
            "total_cycles": len(dac_arr),
            "num_windows": n_windows,
            "window_stds": window_stds,
            "settled_std_rw2_plus": settled_std_rw2_plus
        }
        results.append(res)

# Save Trajectories
npz_out = "p1_standardized_rw2_plus_trajectories.npz"
np.savez_compressed(npz_out, **trajectory_dict)
print(f"Preserved all trajectories to '{npz_out}' ({os.path.getsize(npz_out)/1e6:.2f} MB).\n")

# Print Group Audits
print("=========================================================================================================================")
print("=== UNINTERPRETED GROUP MEANS AUDIT (STARTING AT R_W2: CYCLES k_cross + 100,000 ONWARD, DROPPING R_W1) ===")
print("=========================================================================================================================")
print(f"{'Group Name':<20} | {'Noise':<8} | {'N':<3} | {'R_W1 (+50k..+100k)':<20} | {'R_W2+ Settled std (Dropping R_W1)':<32} | {'SD(std)':<10}")
print("-" * 115)

group_summary_dict = {}

for grp_label, noise_val, n_seeds, seed_range, n_windows in groups_config:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    
    rw1_vals = [r["window_stds"][0] for r in grp_runs]
    rw2_plus_stds = [r["settled_std_rw2_plus"] for r in grp_runs]
    
    m_rw1 = np.mean(rw1_vals)
    m_rw2_plus = np.mean(rw2_plus_stds)
    sd_rw2_plus = np.std(rw2_plus_stds, ddof=1)
    se_rw2_plus = sd_rw2_plus / np.sqrt(len(grp_runs))
    
    group_summary_dict[noise_val] = {
        "label": grp_label,
        "N": len(grp_runs),
        "m_rw1": m_rw1,
        "m_rw2_plus": m_rw2_plus,
        "sd_rw2_plus": sd_rw2_plus,
        "se_rw2_plus": se_rw2_plus
    }
    
    print(f"{grp_label:<20} | {noise_val:<6.1f}mV | {len(grp_runs):<3} | {m_rw1:.3f} LSBs (Dropped)    | {m_rw2_plus:.3f} +/- {se_rw2_plus:.3f} Fine LSBs         | {sd_rw2_plus:.3f}")

print("=========================================================================================================================\n")

# Detailed Window Progressions
print("DETAILED PER-GROUP WINDOW PROGRESSIONS (Showing R_W1 dropped vs R_W2..N plateau):")
for grp_label, noise_val, n_seeds, seed_range, n_windows in groups_config:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    print(f"\n* {grp_label} (N={len(grp_runs)}, {n_windows} Windows):")
    for w in range(n_windows):
        w_vals = [r["window_stds"][w] for r in grp_runs]
        drop_mark = " [DROPPED]" if w == 0 else " [KEPT]"
        print(f"  - R_W{w+1} (+{(w+1)*50}k..+{(w+2)*50}k cycles): {np.mean(w_vals):.3f} +/- {np.std(w_vals, ddof=1):.3f} LSBs{drop_mark}")

# 1. Clean 4-Level Power-Law Fit (11.5 mV to 90.0 mV, 45 Runs, R_W2+ stds)
runs_4lvl = [r for r in results if r["sigma_n_mV"] <= 90.0]
x_log_4 = np.array([np.log(r["sigma_n_mV"]) for r in runs_4lvl])
y_log_4 = np.array([np.log(r["settled_std_rw2_plus"]) for r in runs_4lvl])

poly4, cov4 = np.polyfit(x_log_4, y_log_4, 1, cov=True)
alpha_4lvl = poly4[0]
alpha_4lvl_err = np.sqrt(cov4[0, 0])

# WLS Fit on 4 Group Means (11.5, 23, 45.5, 90 mV)
g_noises_4 = [11.5, 23.0, 45.5, 90.0]
x_g4 = np.log(g_noises_4)
y_g4 = np.array([np.log(group_summary_dict[nv]["m_rw2_plus"]) for nv in g_noises_4])
se_g4 = np.array([group_summary_dict[nv]["se_rw2_plus"] / group_summary_dict[nv]["m_rw2_plus"] for nv in g_noises_4])
weights_g4 = 1.0 / se_g4**2

poly4_w, cov4_w = np.polyfit(x_g4, y_g4, 1, w=np.sqrt(weights_g4), cov=True)
alpha_4lvl_wls = poly4_w[0]
alpha_4lvl_wls_err = np.sqrt(cov4_w[0, 0])

# Chi-squared
y_pred_4 = poly4_w[0] * x_g4 + poly4_w[1]
chi2_4lvl = np.sum(((y_g4 - y_pred_4) / se_g4)**2)

# Distances
dist_sqrt = abs(0.50 - alpha_4lvl_wls) / alpha_4lvl_wls_err
dist_third = abs(0.33333 - alpha_4lvl_wls) / alpha_4lvl_wls_err

print("\n===============================================================================================================")
print("=== CLEAN 4-LEVEL POWER-LAW FIT (11.5 mV TO 90.0 mV, DROPPING R_W1) ===")
print("===============================================================================================================")
print(f"  - OLS Exponent alpha:       alpha_4lvl = {alpha_4lvl:.3f} +/- {alpha_4lvl_err:.3f}")
print(f"  - WLS Weighted Exponent:    alpha_4lvl_wls = {alpha_4lvl_wls:.3f} +/- {alpha_4lvl_wls_err:.3f}")
print(f"  - Weighted Chi-Squared:     chi2 = {chi2_4lvl:.3f} on df=2 degrees of freedom (p = {1.0 - np.exp(-chi2_4lvl/2):.3f})")
print(f"  - Distance from Square-Root (alpha = 0.50): {dist_sqrt:.1f} sigma (REFUTES SQUARE-ROOT DIFFUSION!)")
print(f"  - Distance from One-Third (alpha = 0.333):   {dist_third:.1f} sigma (CLOSEST SIMPLE FORM)")

# 2. Extrapolation Deficit Audit for High-Noise Levels (128, 180, 360 mV)
print("\n===============================================================================================================")
print("=== EXTRAPOLATION DEFICIT AUDIT FOR HIGH-NOISE LEVELS (GRADUAL ROLLOVER AUDIT) ===")
print("===============================================================================================================")
high_levels = [128.0, 180.0, 360.0]

for nv in high_levels:
    meas_mean = group_summary_dict[nv]["m_rw2_plus"]
    meas_se = group_summary_dict[nv]["se_rw2_plus"]
    
    # Predict using 4-level WLS model: ln(y_pred) = alpha_wls * ln(nv) + C_wls
    ln_pred = poly4_w[0] * np.log(nv) + poly4_w[1]
    pred_val = np.exp(ln_pred)
    
    diff_val = pred_val - meas_mean
    deficit_se = diff_val / meas_se
    
    print(f"  * Noise Level {nv:5.1f} mV:")
    print(f"    - Extrapolated Power-Law Prediction: {pred_val:.3f} Fine LSBs")
    print(f"    - Measured Settled Value (R_W2+):   {meas_mean:.3f} +/- {meas_se:.3f} Fine LSBs")
    print(f"    - Measured Deficit:                 {diff_val:.3f} LSBs low ({deficit_se:.1f} SEs low)")

# Save CSV
out_csv = "p1_standardized_rw2_plus_results.csv"
header = ["group", "seed", "sigma_n_mV", "crossing_cycle", "total_cycles", "num_windows", "settled_std_rw2_plus"] + [f"rw_{i+1}_std" for i in range(8)]
data_rows = []
for r in results:
    row = [r["group"], r["seed"], r["sigma_n_mV"], r["crossing_cycle"], r["total_cycles"], r["num_windows"], r["settled_std_rw2_plus"]] + r["window_stds"]
    if len(row) < len(header):
        row += [None] * (len(header) - len(row))
    data_rows.append(row)

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved standardized results CSV to '{out_csv}'.")
