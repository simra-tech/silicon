import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING 65-RUN MULTI-WINDOW EQUILIBRATION AUDIT ===")
print("Total Run Duration: N = 300,000 Clock Cycles (60.0 us at 5.0 GS/s)")
print("Saving All 65 Full Trajectories to 'p1_65run_trajectories.npz'...")
print("Evaluating 4 Successive 50,000-Cycle Windows (100k-150k, 150k-200k, 200k-250k, 250k-300k)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps
N_clock_cycles = 300000 # 300,000 cycles

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
trajectory_dict = {}

windows_def = [
    ("W1 (100k-150k)", 100000, 150000),
    ("W2 (150k-200k)", 150000, 200000),
    ("W3 (200k-250k)", 200000, 250000),
    ("W4 (250k-300k)", 250000, 300000)
]

for idx, r in enumerate(all_runs):
    group_name = r["group"]
    seed_val = r["seed"]
    sigma_n_amp = r["sigma_n"]
    
    # Explicit PRNG seeding per process run
    rng = np.random.default_rng(seed=seed_val)
    
    accumulator_val = 0
    curr_dac_code = start_dac_code
    dac_history = np.zeros(N_clock_cycles, dtype=np.int32)
    
    for k in range(N_clock_cycles):
        v_res_in = V_in_step - (131072 - curr_dac_code) * delta_V_fine
        v_res_amp = v_res_in * A_op
        
        noise_k = rng.normal(0.0, sigma_n_amp)
        v_latch_diff = v_res_amp + noise_k
        
        b_k = 1 if v_latch_diff > 0 else 0
        accumulator_val += (1 - 2 * b_k)
        curr_dac_code = start_dac_code + int(accumulator_val // 16)
        dac_history[k] = curr_dac_code
    
    # Save full trajectory on disk
    traj_key = f"run_{idx:02d}_group_{sigma_n_amp*1e3:.1f}mV_seed_{seed_val}"
    trajectory_dict[traj_key] = dac_history
    
    # Null crossing cycle
    crossing_indices = np.where(dac_history >= target_dac_code)[0]
    has_crossed = len(crossing_indices) > 0
    crossing_cycle = int(crossing_indices[0]) if has_crossed else -1
    
    # Evaluate settled_std over all 4 windows
    w_stds = {}
    for w_name, w_start, w_end in windows_def:
        w_phase = dac_history[w_start:w_end]
        w_stds[w_name] = float(np.std(w_phase))
    
    res = {
        "run_idx": idx,
        "group": group_name,
        "seed": seed_val,
        "sigma_n_mV": sigma_n_amp * 1e3,
        "M_target": target_dac_code,
        "crossing_cycle": crossing_cycle,
        "crossing_time_us": (crossing_cycle * T_s) * 1e6,
        "std_w1": w_stds["W1 (100k-150k)"],
        "std_w2": w_stds["W2 (150k-200k)"],
        "std_w3": w_stds["W3 (200k-250k)"],
        "std_w4": w_stds["W4 (250k-300k)"],
    }
    results.append(res)

# Save Trajectory NPZ File
npz_out = "p1_65run_trajectories.npz"
np.savez_compressed(npz_out, **trajectory_dict)
print(f"Preserved all 65 full 300,000-cycle trajectories to '{npz_out}' ({os.path.getsize(npz_out)/1e6:.2f} MB).\n")

# Group Analysis across 4 Successive Windows
groups_info = [
    ("Group 0 (11.5 mV)", 11.5),
    ("Group 1 (23.0 mV)", 23.0),
    ("Group 2 (45.5 mV)", 45.5),
    ("Group 3 (90.0 mV)", 90.0),
    ("Group 4 (180.0 mV)", 180.0),
    ("Group 5 (360.0 mV)", 360.0)
]

print("=========================================================================================================================")
print("=== UNINTERPRETED MULTI-WINDOW EQUILIBRATION AUDIT (SETTLED_STD ACROSS 4 SUCCESSIVE 50k-CYCLE WINDOWS) ===")
print("=========================================================================================================================")
print(f"{'Group Name':<20} | {'Noise':<8} | {'N':<3} | {'Mean W1 (100k-150k)':<19} | {'Mean W2 (150k-200k)':<19} | {'Mean W3 (200k-250k)':<19} | {'Mean W4 (250k-300k)':<19}")
print("-" * 125)

for grp_label, noise_val in groups_info:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    n_runs = len(grp_runs)
    
    w1_vals = [r["std_w1"] for r in grp_runs]
    w2_vals = [r["std_w2"] for r in grp_runs]
    w3_vals = [r["std_w3"] for r in grp_runs]
    w4_vals = [r["std_w4"] for r in grp_runs]
    
    m_w1 = np.mean(w1_vals); sd_w1 = np.std(w1_vals, ddof=1 if n_runs>1 else 0)
    m_w2 = np.mean(w2_vals); sd_w2 = np.std(w2_vals, ddof=1 if n_runs>1 else 0)
    m_w3 = np.mean(w3_vals); sd_w3 = np.std(w3_vals, ddof=1 if n_runs>1 else 0)
    m_w4 = np.mean(w4_vals); sd_w4 = np.std(w4_vals, ddof=1 if n_runs>1 else 0)
    
    print(f"{grp_label:<20} | {noise_val:<6.1f}mV | {n_runs:<3} | {m_w1:.3f} +/- {sd_w1:.3f} LSBs | {m_w2:.3f} +/- {sd_w2:.3f} LSBs | {m_w3:.3f} +/- {sd_w3:.3f} LSBs | {m_w4:.3f} +/- {sd_w4:.3f} LSBs")

print("=========================================================================================================================\n")

print("DETAILED PER-GROUP WINDOW EQUILIBRATION DYNAMICS:")

for grp_label, noise_val in groups_info:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    w1_vals = [r["std_w1"] for r in grp_runs]
    w2_vals = [r["std_w2"] for r in grp_runs]
    w3_vals = [r["std_w3"] for r in grp_runs]
    w4_vals = [r["std_w4"] for r in grp_runs]
    
    print(f"\n* {grp_label} (N={len(grp_runs)}):")
    print(f"  - W1 (100k-150k): {np.mean(w1_vals):.3f} +/- {np.std(w1_vals, ddof=1):.3f} LSBs -> {np.round(w1_vals, 3).tolist()}")
    print(f"  - W2 (150k-200k): {np.mean(w2_vals):.3f} +/- {np.std(w2_vals, ddof=1):.3f} LSBs -> {np.round(w2_vals, 3).tolist()}")
    print(f"  - W3 (200k-250k): {np.mean(w3_vals):.3f} +/- {np.std(w3_vals, ddof=1):.3f} LSBs -> {np.round(w3_vals, 3).tolist()}")
    print(f"  - W4 (250k-300k): {np.mean(w4_vals):.3f} +/- {np.std(w4_vals, ddof=1):.3f} LSBs -> {np.round(w4_vals, 3).tolist()}")

# Save CSV
out_csv = "p1_65run_multiwindow_equilibration_results.csv"
header = ["group", "seed", "sigma_n_mV", "M_target", "crossing_cycle", "crossing_time_us", "std_w1_100k_150k", "std_w2_150k_200k", "std_w3_200k_250k", "std_w4_250k_300k"]
data_rows = [[r["group"], r["seed"], r["sigma_n_mV"], r["M_target"], r["crossing_cycle"], r["crossing_time_us"], r["std_w1"], r["std_w2"], r["std_w3"], r["std_w4"]] for r in results]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved multi-window equilibration results CSV to '{out_csv}'.")
