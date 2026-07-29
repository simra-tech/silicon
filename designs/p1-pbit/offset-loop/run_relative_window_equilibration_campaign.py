import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING RELATIVE CROSSING-ALIGNED EQUILIBRATION CAMPAIGN ===")
print("Observation Windows Defined Relative to Each Run's Own Null Crossing Cycle k_cross:")
print("  - R_W1: Cycles k_cross +  50,000 to k_cross + 100,000 (Guaranteed 50,000 cycles after crossing)")
print("  - R_W2: Cycles k_cross + 100,000 to k_cross + 150,000")
print("  - R_W3: Cycles k_cross + 150,000 to k_cross + 200,000")
print("  - R_W4: Cycles k_cross + 200,000 to k_cross + 250,000")
print("Ensuring Every Run Receives 4 Full 50,000-Cycle Post-Crossing Windows...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

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

relative_windows = [
    ("R_W1 (+50k..+100k)",  50000, 100000),
    ("R_W2 (+100k..+150k)", 100000, 150000),
    ("R_W3 (+150k..+200k)", 150000, 200000),
    ("R_W4 (+200k..+250k)", 200000, 250000)
]

for idx, r in enumerate(all_runs):
    group_name = r["group"]
    seed_val = r["seed"]
    sigma_n_amp = r["sigma_n"]
    
    # Explicit PRNG seeding per process run
    rng = np.random.default_rng(seed=seed_val)
    
    # First pass: Run until null crossing is found
    dac_history = []
    accumulator_val = 0
    curr_dac_code = start_dac_code
    
    k = 0
    crossing_cycle = -1
    
    # Simulation loop with dynamic extension
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
        
        # Stop condition: Must have crossed null AND have 250,000 post-crossing cycles!
        if crossing_cycle >= 0 and k >= (crossing_cycle + 250000):
            break
        
        # Safety fallback cap if crossing never occurs (e.g., 600,000 cycles)
        if k >= 600000:
            break
    
    dac_arr = np.array(dac_history, dtype=np.int32)
    
    # Save full trajectory on disk
    traj_key = f"run_{idx:02d}_group_{sigma_n_amp*1e3:.1f}mV_seed_{seed_val}"
    trajectory_dict[traj_key] = dac_arr
    
    # Evaluate settled_std over all 4 RELATIVE post-crossing windows
    r_stds = {}
    for rw_name, offset_start, offset_end in relative_windows:
        w_start = crossing_cycle + offset_start
        w_end = crossing_cycle + offset_end
        w_phase = dac_arr[w_start:w_end]
        r_stds[rw_name] = float(np.std(w_phase))
    
    res = {
        "run_idx": idx,
        "group": group_name,
        "seed": seed_val,
        "sigma_n_mV": sigma_n_amp * 1e3,
        "M_target": target_dac_code,
        "crossing_cycle": crossing_cycle,
        "total_cycles_run": len(dac_arr),
        "crossing_time_us": (crossing_cycle * T_s) * 1e6,
        "std_rw1": r_stds["R_W1 (+50k..+100k)"],
        "std_rw2": r_stds["R_W2 (+100k..+150k)"],
        "std_rw3": r_stds["R_W3 (+150k..+200k)"],
        "std_rw4": r_stds["R_W4 (+200k..+250k)"],
    }
    results.append(res)

# Save Trajectory NPZ File
npz_out = "p1_relative_aligned_trajectories.npz"
np.savez_compressed(npz_out, **trajectory_dict)
print(f"Preserved all 65 relative-aligned trajectories to '{npz_out}' ({os.path.getsize(npz_out)/1e6:.2f} MB).\n")

# Group Analysis across 4 Relative Post-Crossing Windows
groups_info = [
    ("Group 0 (11.5 mV)", 11.5),
    ("Group 1 (23.0 mV)", 23.0),
    ("Group 2 (45.5 mV)", 45.5),
    ("Group 3 (90.0 mV)", 90.0),
    ("Group 4 (180.0 mV)", 180.0),
    ("Group 5 (360.0 mV)", 360.0)
]

print("=========================================================================================================================")
print("=== UNCONFIDENTIAL RELATIVE CROSSING-ALIGNED EQUILIBRATION AUDIT (SETTLED_STD ACROSS 4 RELATIVE WINDOWS) ===")
print("=========================================================================================================================")
print(f"{'Group Name':<20} | {'Noise':<8} | {'N':<3} | {'Mean R_W1 (+50k..+100k)':<23} | {'Mean R_W2 (+100k..+150k)':<23} | {'Mean R_W3 (+150k..+200k)':<23} | {'Mean R_W4 (+200k..+250k)':<23}")
print("-" * 140)

for grp_label, noise_val in groups_info:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    n_runs = len(grp_runs)
    
    rw1_vals = [r["std_rw1"] for r in grp_runs]
    rw2_vals = [r["std_rw2"] for r in grp_runs]
    rw3_vals = [r["std_rw3"] for r in grp_runs]
    rw4_vals = [r["std_rw4"] for r in grp_runs]
    
    m_rw1 = np.mean(rw1_vals); sd_rw1 = np.std(rw1_vals, ddof=1 if n_runs>1 else 0)
    m_rw2 = np.mean(rw2_vals); sd_rw2 = np.std(rw2_vals, ddof=1 if n_runs>1 else 0)
    m_rw3 = np.mean(rw3_vals); sd_rw3 = np.std(rw3_vals, ddof=1 if n_runs>1 else 0)
    m_rw4 = np.mean(rw4_vals); sd_rw4 = np.std(rw4_vals, ddof=1 if n_runs>1 else 0)
    
    print(f"{grp_label:<20} | {noise_val:<6.1f}mV | {n_runs:<3} | {m_rw1:.3f} +/- {sd_rw1:.3f} LSBs | {m_rw2:.3f} +/- {sd_rw2:.3f} LSBs | {m_rw3:.3f} +/- {sd_rw3:.3f} LSBs | {m_rw4:.3f} +/- {sd_rw4:.3f} LSBs")

print("=========================================================================================================================\n")

print("DETAILED PER-GROUP RELATIVE WINDOW EQUILIBRATION DYNAMICS:")

for grp_label, noise_val in groups_info:
    grp_runs = [r for r in results if r["sigma_n_mV"] == noise_val]
    rw1_vals = [r["std_rw1"] for r in grp_runs]
    rw2_vals = [r["std_rw2"] for r in grp_runs]
    rw3_vals = [r["std_rw3"] for r in grp_runs]
    rw4_vals = [r["std_rw4"] for r in grp_runs]
    
    print(f"\n* {grp_label} (N={len(grp_runs)}):")
    print(f"  - R_W1 (+50k..+100k):   {np.mean(rw1_vals):.3f} +/- {np.std(rw1_vals, ddof=1):.3f} LSBs -> {np.round(rw1_vals, 3).tolist()}")
    print(f"  - R_W2 (+100k..+150k):  {np.mean(rw2_vals):.3f} +/- {np.std(rw2_vals, ddof=1):.3f} LSBs -> {np.round(rw2_vals, 3).tolist()}")
    print(f"  - R_W3 (+150k..+200k):  {np.mean(rw3_vals):.3f} +/- {np.std(rw3_vals, ddof=1):.3f} LSBs -> {np.round(rw3_vals, 3).tolist()}")
    print(f"  - R_W4 (+200k..+250k):  {np.mean(rw4_vals):.3f} +/- {np.std(rw4_vals, ddof=1):.3f} LSBs -> {np.round(rw4_vals, 3).tolist()}")

# Save CSV
out_csv = "p1_65run_relative_window_equilibration_results.csv"
header = ["group", "seed", "sigma_n_mV", "M_target", "crossing_cycle", "total_cycles_run", "crossing_time_us", "std_rw1_50k_100k", "std_rw2_100k_150k", "std_rw3_150k_200k", "std_rw4_200k_250k"]
data_rows = [[r["group"], r["seed"], r["sigma_n_mV"], r["M_target"], r["crossing_cycle"], r["total_cycles_run"], r["crossing_time_us"], r["std_rw1"], r["std_rw2"], r["std_rw3"], r["std_rw4"]] for r in results]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved relative-aligned window equilibration results CSV to '{out_csv}'.")
