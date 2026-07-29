import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING TARGETED 180mV EXTENSION (8 RELATIVE WINDOWS) AND 128mV BREAK-LOCATION CAMPAIGN ===")
print("Task 1: Extend Group 4 (180.0 mV, 10 Seeds) to 8 Relative Post-Crossing Windows (400,000 Post-Crossing Cycles)...")
print("Task 2: Add Group 6 (128.0 mV, 10 Seeds 801..810) with 4 Relative Post-Crossing Windows...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed

target_dac_code = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac_code = target_dac_code - 254                          # 114,473

# Matrix:
# 1. 180 mV extended runs (10 Seeds, 601..610) -> 8 Relative Windows (k_cross + 50k to k_cross + 450k)
# 2. 128 mV new runs (10 Seeds, 801..810)      -> 4 Relative Windows (k_cross + 50k to k_cross + 250k)

runs_180mV_ext = [{"group": "Group 4 Ext (180.0 mV)", "seed": 600 + i, "sigma_n": 180.0e-3, "num_windows": 8} for i in range(1, 11)]
runs_128mV_new = [{"group": "Group 6 (128.0 mV)",     "seed": 800 + i, "sigma_n": 128.0e-3, "num_windows": 4} for i in range(1, 11)]

all_targeted_runs = runs_180mV_ext + runs_128mV_new

results = []
trajectory_dict = {}

for idx, r in enumerate(all_targeted_runs):
    group_name = r["group"]
    seed_val = r["seed"]
    sigma_n_amp = r["sigma_n"]
    n_windows = r["num_windows"]
    
    rng = np.random.default_rng(seed=seed_val)
    
    dac_history = []
    accumulator_val = 0
    curr_dac_code = start_dac_code
    
    k = 0
    crossing_cycle = -1
    required_post_cycles = n_windows * 50000 + 50000 # 50k buffer + 50k per window
    
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
    
    traj_key = f"targeted_{group_name.replace(' ', '_')}_seed_{seed_val}"
    trajectory_dict[traj_key] = dac_arr
    
    # Evaluate relative windows
    window_stds = []
    for w in range(1, n_windows + 1):
        w_start = crossing_cycle + w * 50000
        w_end = crossing_cycle + (w + 1) * 50000
        w_phase = dac_arr[w_start:w_end]
        window_stds.append(float(np.std(w_phase)))
    
    res = {
        "group": group_name,
        "seed": seed_val,
        "sigma_n_mV": sigma_n_amp * 1e3,
        "crossing_cycle": crossing_cycle,
        "total_cycles": len(dac_arr),
        "window_stds": window_stds
    }
    results.append(res)

# Save Trajectories NPZ File
npz_out = "p1_targeted_180mV_128mV_trajectories.npz"
np.savez_compressed(npz_out, **trajectory_dict)
print(f"Saved targeted trajectories to '{npz_out}' ({os.path.getsize(npz_out)/1e6:.2f} MB).\n")

# Print Group Audits
print("=========================================================================================================================")
print("=== TASK 1: GROUP 4 (180.0 mV) EXTENDED 8 RELATIVE WINDOWS AUDIT (10 SEEDS) ===")
print("=========================================================================================================================")
runs_180_ext = [r for r in results if r["sigma_n_mV"] == 180.0]

for w in range(8):
    w_vals = [r["window_stds"][w] for r in runs_180_ext]
    print(f"  * R_W{w+1} (+{(w+1)*50}k..+{(w+2)*50}k cycles): {np.mean(w_vals):.3f} +/- {np.std(w_vals, ddof=1):.3f} LSBs -> {np.round(w_vals, 3).tolist()}")

print("\n=========================================================================================================================")
print("=== TASK 2: GROUP 6 (128.0 mV) NEW LEVEL 4 RELATIVE WINDOWS AUDIT (10 SEEDS) ===")
print("=========================================================================================================================")
runs_128 = [r for r in results if r["sigma_n_mV"] == 128.0]

for w in range(4):
    w_vals = [r["window_stds"][w] for r in runs_128]
    print(f"  * R_W{w+1} (+{(w+1)*50}k..+{(w+2)*50}k cycles): {np.mean(w_vals):.3f} +/- {np.std(w_vals, ddof=1):.3f} LSBs -> {np.round(w_vals, 3).tolist()}")

# Pooled Means Across Settled Windows
# For 180 mV, check plateau across windows 4..8
stds_180_settled = [np.mean(r["window_stds"][3:]) for r in runs_180_ext]
# For 128 mV, check mean across windows 1..4
stds_128_all = [np.mean(r["window_stds"]) for r in runs_128]

print("\n=== SUMMARY OF POOLED GROUP MEANS FOR NEW / EXTENDED LEVELS ===")
print(f"  * Group 6 (128.0 mV, N=10): mean settled_std = {np.mean(stds_128_all):.3f} +/- {np.std(stds_128_all, ddof=1):.3f} Fine LSBs")
print(f"  * Group 4 Ext (180.0 mV, N=10, Settled R_W4..8): mean settled_std = {np.mean(stds_180_settled):.3f} +/- {np.std(stds_180_settled, ddof=1):.3f} Fine LSBs")

# Save CSV
out_csv = "p1_targeted_180mV_128mV_results.csv"
header = ["group", "seed", "sigma_n_mV", "crossing_cycle", "total_cycles"] + [f"rw_{i+1}_std" for i in range(8)]
data_rows = []
for r in results:
    row = [r["group"], r["seed"], r["sigma_n_mV"], r["crossing_cycle"], r["total_cycles"]] + r["window_stds"]
    if len(row) < len(header):
        row += [None] * (len(header) - len(row))
    data_rows.append(row)

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved targeted results CSV to '{out_csv}'.")
