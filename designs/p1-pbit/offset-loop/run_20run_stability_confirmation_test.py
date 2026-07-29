import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING 20-RUN STABILITY CONFIRMATION TEST ===")
print("Testing Fresh Independent Seeds at 90.0 mV (Seeds 321..330) and 180.0 mV (Seeds 611..620)")
print("Standardized Observation Protocol: Starting ALL Measurements at k_cross + 100,000 Cycles (Dropping R_W1)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed

target_dac_code = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac_code = target_dac_code - 254                          # 114,473

# Fresh Seed Matrix:
# 10 Fresh Seeds @ 90.0 mV (Seeds 321..330, 4 Relative Windows)
# 10 Fresh Seeds @ 180.0 mV (Seeds 611..620, 8 Relative Windows)

fresh_90mV  = [{"group": "Group 3 Fresh (90.0 mV)",  "seed": 320 + i, "sigma_n": 90.0e-3,  "n_windows": 4} for i in range(1, 11)]
fresh_180mV = [{"group": "Group 4 Fresh (180.0 mV)", "seed": 610 + i, "sigma_n": 180.0e-3, "n_windows": 8} for i in range(1, 11)]

all_fresh_runs = fresh_90mV + fresh_180mV

results = []
trajectory_dict = {}

for idx, r in enumerate(all_fresh_runs):
    group_name = r["group"]
    seed_val = r["seed"]
    sigma_n_amp = r["sigma_n"]
    n_windows = r["n_windows"]
    
    rng = np.random.default_rng(seed=seed_val)
    
    dac_history = []
    accumulator_val = 0
    curr_dac_code = start_dac_code
    
    k = 0
    crossing_cycle = -1
    required_post_cycles = n_windows * 50000 + 50000
    
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
        if k >= 800000:
            break
    
    dac_arr = np.array(dac_history, dtype=np.int32)
    
    traj_key = f"stability_fresh_{group_name.replace(' ', '_')}_seed_{seed_val}"
    trajectory_dict[traj_key] = dac_arr
    
    # Evaluate relative windows
    window_stds = []
    for w in range(1, n_windows + 1):
        w_start = crossing_cycle + w * 50000
        w_end = crossing_cycle + (w + 1) * 50000
        w_phase = dac_arr[w_start:w_end]
        window_stds.append(float(np.std(w_phase)))
    
    # DROPPING R_W1: Compute settled_std using R_W2..R_Wn
    settled_std_rw2_plus = float(np.mean(window_stds[1:]))
    
    res = {
        "group": group_name,
        "seed": seed_val,
        "sigma_n_mV": sigma_n_amp * 1e3,
        "M_target": target_dac_code,
        "crossing_cycle": crossing_cycle,
        "total_cycles": len(dac_arr),
        "num_windows": n_windows,
        "window_stds": window_stds,
        "settled_std_rw2_plus": settled_std_rw2_plus
    }
    results.append(res)

# Save Trajectories
npz_out = "p1_stability_fresh_trajectories.npz"
np.savez_compressed(npz_out, **trajectory_dict)
print(f"Preserved fresh stability trajectories to '{npz_out}' ({os.path.getsize(npz_out)/1e6:.2f} MB).\n")

# Target Baselines for Comparison
target_90_mean = 3.472; target_90_se = 0.110
target_180_mean = 3.945; target_180_se = 0.132

runs_90_fresh = [r["settled_std_rw2_plus"] for r in results if r["sigma_n_mV"] == 90.0]
runs_180_fresh = [r["settled_std_rw2_plus"] for r in results if r["sigma_n_mV"] == 180.0]

fresh_90_mean = np.mean(runs_90_fresh); fresh_90_sd = np.std(runs_90_fresh, ddof=1); fresh_90_se = fresh_90_sd / np.sqrt(10)
fresh_180_mean = np.mean(runs_180_fresh); fresh_180_sd = np.std(runs_180_fresh, ddof=1); fresh_180_se = fresh_180_sd / np.sqrt(10)

# Welch's t-test comparing fresh seeds to baseline
diff_90 = abs(fresh_90_mean - target_90_mean)
se_diff_90 = np.sqrt(fresh_90_se**2 + target_90_se**2)
t_90 = diff_90 / se_diff_90

diff_180 = abs(fresh_180_mean - target_180_mean)
se_diff_180 = np.sqrt(fresh_180_se**2 + target_180_se**2)
t_180 = diff_180 / se_diff_180

print("=========================================================================================================================")
print("=== STABILITY CONFIRMATION AUDIT (FRESH SEEDS VS BASELINE REPRODUCIBILITY) ===")
print("=========================================================================================================================")
print(f"{'Group':<22} | {'Fresh Mean std':<18} | {'Baseline Target std':<20} | {'Difference':<12} | {'Welch t-stat':<12}")
print("-" * 95)
print(f"{'Group 3 Fresh (90 mV)':<22} | {fresh_90_mean:.3f} +/- {fresh_90_se:.3f} LSBs | {target_90_mean:.3f} +/- {target_90_se:.3f} LSBs | {diff_90:.3f} LSBs    | t = {t_90:.2f} sigma")
print(f"{'Group 4 Fresh (180 mV)':<22} | {fresh_180_mean:.3f} +/- {fresh_180_se:.3f} LSBs | {target_180_mean:.3f} +/- {target_180_se:.3f} LSBs | {diff_180:.3f} LSBs    | t = {t_180:.2f} sigma")
print("=========================================================================================================================\n")

print("DETAILED FRESH SEED INDIVIDUAL RUNS:")
print(f"  * Group 3 Fresh (90.0 mV, Seeds 321..330):  {np.round(runs_90_fresh, 3).tolist()}")
print(f"  * Group 4 Fresh (180.0 mV, Seeds 611..620): {np.round(runs_180_fresh, 3).tolist()}")

# Save CSV
out_csv = "p1_stability_confirmation_results.csv"
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

print(f"\nSaved stability confirmation results CSV to '{out_csv}'.")
