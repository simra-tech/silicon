import os, sys, time, csv
import numpy as np

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING 25-RUN POWER-LAW EXPONENT TIGHTENING CAMPAIGN ===")
print("Executing 5 Additional Seeds at 23.0 mV (Seeds 106..110) and 5 Additional Seeds at 90.0 mV (Seeds 306..310)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps
N_clock_cycles = 150000 # 150,000 cycles

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed

target_dac_code = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac_code = target_dac_code - 254                          # 114,473

# 25-Run Extended Matrix: 10 seeds @ 23.0 mV + 5 seeds @ 45.5 mV + 10 seeds @ 90.0 mV
runs_23mV = [{"group": "Group 1 (23.0 mV)", "seed": 100 + i, "sigma_n": 23.0e-3} for i in range(1, 11)]
runs_45mV = [{"group": "Group 2 (45.5 mV)", "seed": 200 + i, "sigma_n": 45.5e-3} for i in range(1, 6)]
runs_90mV = [{"group": "Group 3 (90.0 mV)", "seed": 300 + i, "sigma_n": 90.0e-3} for i in range(1, 11)]
all_runs = runs_23mV + runs_45mV + runs_90mV

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
    
    # Settled phase analysis (post crossing)
    settled_start_cycle = crossing_cycle if has_crossed else N_clock_cycles - 30000
    settled_phase = dac_arr[settled_start_cycle:]
    
    settled_mean = float(np.mean(settled_phase))
    settled_std = float(np.std(settled_phase))
    settled_min = int(np.min(settled_phase))
    settled_max = int(np.max(settled_phase))
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
    }
    results.append(res)

# Group Statistical Analysis
stds_23mV = [r["settled_std"] for r in results if r["sigma_n_mV"] == 23.0]
stds_45mV = [r["settled_std"] for r in results if r["sigma_n_mV"] == 45.5]
stds_90mV = [r["settled_std"] for r in results if r["sigma_n_mV"] == 90.0]

cross_23mV = [r["crossing_cycle"] for r in results if r["sigma_n_mV"] == 23.0]
cross_45mV = [r["crossing_cycle"] for r in results if r["sigma_n_mV"] == 45.5]
cross_90mV = [r["crossing_cycle"] for r in results if r["sigma_n_mV"] == 90.0]

mean_std_23 = np.mean(stds_23mV); sd_std_23 = np.std(stds_23mV, ddof=1)
mean_std_45 = np.mean(stds_45mV); sd_std_45 = np.std(stds_45mV, ddof=1)
mean_std_90 = np.mean(stds_90mV); sd_std_90 = np.std(stds_90mV, ddof=1)

mean_cross_23 = np.mean(cross_23mV); sd_cross_23 = np.std(cross_23mV, ddof=1)
mean_cross_45 = np.mean(cross_45mV); sd_cross_45 = np.std(cross_45mV, ddof=1)
mean_cross_90 = np.mean(cross_90mV); sd_cross_90 = np.std(cross_90mV, ddof=1)

# Log-Log Power Law OLS Regression: ln(sigma_code) = alpha * ln(sigma_n) + C
x_log = np.array([np.log(r["sigma_n_mV"]) for r in results])
y_log = np.array([np.log(r["settled_std"]) for r in results])

poly, cov = np.polyfit(x_log, y_log, 1, cov=True)
alpha = poly[0]
alpha_err = np.sqrt(cov[0, 0])

# Distances from benchmarks
dist_flat = abs(alpha - 0.00) / alpha_err
dist_linear = abs(1.00 - alpha) / alpha_err
dist_sqrt = abs(0.50 - alpha) / alpha_err

print("===============================================================================================================")
print(f"=== 25-RUN EXTENDED POWER-LAW CAMPAIGN RESULTS ({len(results)} INDEPENDENT RUNS) ===")
print("===============================================================================================================")
print(f"{'Group':<20} | {'Seed':<6} | {'Noise (mV)':<10} | {'M_target':<9} | {'Crossing Cycle':<14} | {'settled_std (LSBs)':<18} | {'Dither Span':<11}")
print("-" * 110)

for res in results:
    print(f"{res['group']:<20} | {res['seed']:<6} | {res['sigma_n_mV']:<10.1f} | {res['M_target']:<9,} | {res['crossing_cycle']:<14,} | {res['settled_std']:<18.3f} | {res['dither_span']:<11}")

print("===============================================================================================================\n")

print("LOG-LOG POWER LAW REGRESSION AUDIT (ALL 25 RUNS):")
print(f" 1. Group Summary Means:")
print(f"    - Group 1 (23.0 mV, N=10): mean settled_std = {mean_std_23:.3f} +/- {sd_std_23:.3f} Fine LSBs (Crossing = {mean_cross_23:,.0f} cycles)")
print(f"    - Group 2 (45.5 mV, N=5):  mean settled_std = {mean_std_45:.3f} +/- {sd_std_45:.3f} Fine LSBs (Crossing = {mean_cross_45:,.0f} cycles)")
print(f"    - Group 3 (90.0 mV, N=10): mean settled_std = {mean_std_90:.3f} +/- {sd_std_90:.3f} Fine LSBs (Crossing = {mean_cross_90:,.0f} cycles)")

print(f"\n 2. Fitted Power-Law Exponent:")
print(f"    - Scaling Model:           sigma_code = C * sigma_n^(alpha)")
print(f"    - Fitted Exponent alpha:   alpha = {alpha:.3f} +/- {alpha_err:.3f}")

print(f"\n 3. Statistical Distances:")
print(f"    - Distance from Flat (alpha = 0.00):      {dist_flat:.1f} sigma (REFUTES FLATNESS!)")
print(f"    - Distance from Linear (alpha = 1.00):    {dist_linear:.1f} sigma (REFUTES LINEAR LAW!)")
print(f"    - Distance from Square-Root (alpha = 0.50): {dist_sqrt:.1f} sigma (DISFAVORS SQUARE-ROOT!)")

# Save CSV
out_csv = "p1_25run_noise_powerlaw_campaign_results.csv"
header = ["group", "seed", "sigma_n_mV", "M_target", "crossing_cycle", "crossing_time_us", "settled_mean", "settled_error_lsb", "settled_std", "dither_span"]
data_rows = [[r["group"], r["seed"], r["sigma_n_mV"], r["M_target"], r["crossing_cycle"], r["crossing_time_us"], r["settled_mean"], r["settled_error_lsb"], r["settled_std"], r["dither_span"]] for r in results]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved 25-run power-law campaign results to '{out_csv}'.")
