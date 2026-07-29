import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING TWO FIRST-PRINCIPLES PHYSICAL HYPOTHESIS TESTS ===")
print("Test 1: Sub-Count Accumulation Division Ratio Sweep (N_sub = 4 vs N_sub = 64 across 11.5, 23, 45.5, 90 mV)")
print("Test 2: Noise-to-Offset Ratio Sweep (V_step = 5, 10, 20, 40, 80 mV at fixed 180 mV noise)\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred

# ==============================================================================================================
# TEST 1: Sub-Count Division Sweep (N_sub = 4 and N_sub = 64 across 4 noise levels)
# ==============================================================================================================
print("--- RUNNING TEST 1: SUB-COUNT DIVISION RATIO SWEEP (N_sub = 4 & 64) ---")

noises_test1 = [11.5e-3, 23.0e-3, 45.5e-3, 90.0e-3]
n_sub_vals = [4, 64]
V_in_step_test1 = 10.0e-3

target_dac_code_10mV = 131072 - int(round(V_in_step_test1 / delta_V_fine)) # 114,727
start_dac_code_10mV = target_dac_code_10mV - 254

results_test1 = []

for n_sub in n_sub_vals:
    for sigma_n_amp in noises_test1:
        stds_run = []
        for seed_idx in range(1, 11): # 10 seeds per level
            seed_val = 1000 * n_sub + int(sigma_n_amp * 1000) + seed_idx
            rng = np.random.default_rng(seed=seed_val)
            
            dac_history = []
            accumulator_val = 0
            curr_dac_code = start_dac_code_10mV
            
            k = 0
            crossing_cycle = -1
            
            while True:
                v_res_in = V_in_step_test1 - (131072 - curr_dac_code) * delta_V_fine
                v_res_amp = v_res_in * A_op
                
                noise_k = rng.normal(0.0, sigma_n_amp)
                v_latch_diff = v_res_amp + noise_k
                
                b_k = 1 if v_latch_diff > 0 else 0
                accumulator_val += (1 - 2 * b_k)
                curr_dac_code = start_dac_code_10mV + int(accumulator_val // n_sub)
                dac_history.append(curr_dac_code)
                
                if crossing_cycle < 0 and curr_dac_code >= target_dac_code_10mV:
                    crossing_cycle = k
                
                k += 1
                if crossing_cycle >= 0 and k >= (crossing_cycle + 250000):
                    break
                if k >= 600000:
                    break
            
            dac_arr = np.array(dac_history, dtype=np.int32)
            
            # Evaluate settled_std over R_W2..R_W4 (crossing + 100k to crossing + 250k)
            w_stds = []
            for w in range(2, 5):
                w_start = crossing_cycle + w * 50000
                w_end = crossing_cycle + (w + 1) * 50000
                w_stds.append(float(np.std(dac_arr[w_start:w_end])))
            
            stds_run.append(float(np.mean(w_stds)))
        
        m_std = np.mean(stds_run)
        se_std = np.std(stds_run, ddof=1) / np.sqrt(10)
        results_test1.append({
            "n_sub": n_sub,
            "sigma_n_mV": sigma_n_amp * 1e3,
            "mean_std": m_std,
            "se_std": se_std,
            "individual_stds": stds_run
        })

# Fit Exponents for Test 1
for n_sub in n_sub_vals:
    sub_res = [r for r in results_test1 if r["n_sub"] == n_sub]
    x_log = np.log([r["sigma_n_mV"] for r in sub_res])
    y_log = np.log([r["mean_std"] for r in sub_res])
    w_log = 1.0 / (np.array([r["se_std"] for r in sub_res]) / [r["mean_std"] for r in sub_res])**2
    
    poly_w, cov_w = np.polyfit(x_log, y_log, 1, w=np.sqrt(w_log), cov=True)
    alpha_wls = poly_w[0]
    alpha_err = np.sqrt(cov_w[0, 0])
    
    print(f"  * N_sub = {n_sub:2d}: Group Means = {[round(r['mean_std'], 3) for r in sub_res]}")
    print(f"    -> Fitted Exponent alpha (N_sub={n_sub}): alpha = {alpha_wls:.3f} +/- {alpha_err:.3f}")

# ==============================================================================================================
# TEST 2: Noise-to-Offset Ratio Sweep (V_step = 5, 10, 20, 40, 80 mV at fixed 180 mV noise, N_sub = 16)
# ==============================================================================================================
print("\n--- RUNNING TEST 2: NOISE-TO-OFFSET RATIO SWEEP (V_step = 5..80 mV at 180 mV Noise) ---")

v_steps_test2 = [5.0e-3, 10.0e-3, 20.0e-3, 40.0e-3, 80.0e-3]
sigma_n_fixed = 180.0e-3
results_test2 = []

for v_step in v_steps_test2:
    stds_run = []
    target_dac = 131072 - int(round(v_step / delta_V_fine))
    start_dac = target_dac - 254
    
    for seed_idx in range(1, 11): # 10 seeds per level
        seed_val = 20000 + int(v_step * 10000) + seed_idx
        rng = np.random.default_rng(seed=seed_val)
        
        dac_history = []
        accumulator_val = 0
        curr_dac_code = start_dac
        
        k = 0
        crossing_cycle = -1
        
        # At 180 mV noise, run 8 relative windows (400,000 post-crossing cycles)
        while True:
            v_res_in = v_step - (131072 - curr_dac_code) * delta_V_fine
            v_res_amp = v_res_in * A_op
            
            noise_k = rng.normal(0.0, sigma_n_fixed)
            v_latch_diff = v_res_amp + noise_k
            
            b_k = 1 if v_latch_diff > 0 else 0
            accumulator_val += (1 - 2 * b_k)
            curr_dac_code = start_dac + int(accumulator_val // 16)
            dac_history.append(curr_dac_code)
            
            if crossing_cycle < 0 and curr_dac_code >= target_dac:
                crossing_cycle = k
            
            k += 1
            if crossing_cycle >= 0 and k >= (crossing_cycle + 450000):
                break
            if k >= 900000:
                break
        
        dac_arr = np.array(dac_history, dtype=np.int32)
        
        # Evaluate settled_std over R_W4..R_W8 (crossing + 200k to crossing + 450k)
        w_stds = []
        for w in range(4, 9):
            w_start = crossing_cycle + w * 50000
            w_end = crossing_cycle + (w + 1) * 50000
            w_stds.append(float(np.std(dac_arr[w_start:w_end])))
        
        stds_run.append(float(np.mean(w_stds)))
    
    m_std = np.mean(stds_run)
    se_std = np.std(stds_run, ddof=1) / np.sqrt(10)
    
    ratio = sigma_n_fixed / v_step
    print(f"  * V_step = {v_step*1e3:4.1f} mV (Noise/Offset Ratio = {ratio:5.1f}:1): mean settled_std = {m_std:.3f} +/- {se_std:.3f} Fine LSBs")
    results_test2.append({
        "v_step_mV": v_step * 1e3,
        "ratio_noise_offset": ratio,
        "mean_std": m_std,
        "se_std": se_std,
        "individual_stds": stds_run
    })

# Save CSVs
csv_test1 = "p1_hypothesis_test1_nsub_sweep_results.csv"
header1 = ["n_sub", "sigma_n_mV", "mean_std", "se_std"]
with open(csv_test1, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(header1)
    for r in results_test1: w.writerow([r["n_sub"], r["sigma_n_mV"], r["mean_std"], r["se_std"]])

csv_test2 = "p1_hypothesis_test2_offset_sweep_results.csv"
header2 = ["v_step_mV", "ratio_noise_offset", "mean_std", "se_std"]
with open(csv_test2, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(header2)
    for r in results_test2: w.writerow([r["v_step_mV"], r["ratio_noise_offset"], r["mean_std"], r["se_std"]])

print(f"\nSaved hypothesis test CSVs to '{csv_test1}' and '{csv_test2}'.")
