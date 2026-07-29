import os, sys, time, csv
import numpy as np

# ==============================================================================================================
# PRE-REGISTERED PHYSICAL HYPOTHESIS PREDICTION (WRITTEN BEFORE EXECUTION):
# 
# HYPOTHESIS: Sub-Count Accumulation Divider Trade-Off (N_sub in {4, 16, 64} at 45.5 mV Noise, 10 Seeds Each)
# 
# PREDICTION:
# 1. Servo Convergence Time (N_cross) scales LINEARLY with sub-count division ratio (N_cross proportional to N_sub).
#    - N_sub = 4  will yield FASTEST crossing:  N_cross ~ 6,000..8,000 cycles (~1.2..1.6 us at 5.0 GS/s).
#    - N_sub = 16 will yield INTERMEDIATE:      N_cross ~ 23,500 cycles (~4.7 us).
#    - N_sub = 64 will yield SLOWEST:          N_cross ~ 90,000..100,000 cycles (~18..20 us).
# 
# 2. Settled Dither Band Precision (sigma_code) scales INVERSELY with sub-count filtering (sigma_code proportional to 1/sqrt(N_sub)).
#    - N_sub = 4  will yield LARGEST dither:   sigma_code ~ 5.5..6.0 Fine LSBs.
#    - N_sub = 16 will yield INTERMEDIATE:      sigma_code ~ 2.65 Fine LSBs.
#    - N_sub = 64 will yield SMALLEST dither:   sigma_code ~ 1.1..1.3 Fine LSBs.
# ==============================================================================================================

workspace_dir = '.'
run_dir = 'run'
os.makedirs(run_dir, exist_ok=True)

print("=== EXECUTING PRE-REGISTERED N_sub TRADE-CURVE CAMPAIGN AT 45.5 mV NOISE ===")
print("Testing N_sub in {4, 16, 64} at 45.5 mV Noise (10 Independent Seeds Each)...\n")

# Physical Constants & Parameters
f_s = 5.0e9             # 5.0 GS/s
T_s = 1.0 / f_s         # 200 ps

A_static = 6.29         # Static preamplifier gain: 6.29 V/V
A_op = 314.7            # Operational regenerative latch gain: 314.7 V/V
delta_V_fine = 0.6118e-6 # Trim DAC Fine LSB step: 0.6118 uV input-referred
V_in_step = 10.0e-3     # +10.0 mV offset fixed
sigma_n_45mV = 45.5e-3  # 45.5 mV noise fixed

target_dac = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac = target_dac - 254                                # 114,473

n_sub_list = [4, 16, 64]
results_trade = []

for n_sub in n_sub_list:
    crossings = []
    stds = []
    
    for seed_idx in range(1, 11): # 10 seeds each
        seed_val = 30000 + 100 * n_sub + seed_idx
        rng = np.random.default_rng(seed=seed_val)
        
        dac_history = []
        accumulator_val = 0
        curr_dac_code = start_dac
        
        k = 0
        crossing_cycle = -1
        
        # Ensure 250,000 post-crossing cycles
        while True:
            v_res_in = V_in_step - (131072 - curr_dac_code) * delta_V_fine
            v_res_amp = v_res_in * A_op
            
            noise_k = rng.normal(0.0, sigma_n_45mV)
            v_latch_diff = v_res_amp + noise_k
            
            b_k = 1 if v_latch_diff > 0 else 0
            accumulator_val += (1 - 2 * b_k)
            curr_dac_code = start_dac + int(accumulator_val // n_sub)
            dac_history.append(curr_dac_code)
            
            if crossing_cycle < 0 and curr_dac_code >= target_dac:
                crossing_cycle = k
            
            k += 1
            if crossing_cycle >= 0 and k >= (crossing_cycle + 250000):
                break
            if k >= 900000:
                break
        
        dac_arr = np.array(dac_history, dtype=np.int32)
        
        # Evaluate settled_std over R_W2..R_W4 (crossing + 100k to crossing + 250k)
        w_stds = []
        for w in range(2, 5):
            w_start = crossing_cycle + w * 50000
            w_end = crossing_cycle + (w + 1) * 50000
            w_stds.append(float(np.std(dac_arr[w_start:w_end])))
        
        crossings.append(crossing_cycle)
        stds.append(float(np.mean(w_stds)))
    
    m_cross = np.mean(crossings); se_cross = np.std(crossings, ddof=1) / np.sqrt(10)
    m_std = np.mean(stds); se_std = np.std(stds, ddof=1) / np.sqrt(10)
    
    results_trade.append({
        "n_sub": n_sub,
        "mean_cross_cycles": m_cross,
        "se_cross_cycles": se_cross,
        "mean_cross_time_us": (m_cross * T_s) * 1e6,
        "mean_settled_std": m_std,
        "se_settled_std": se_std,
        "all_crossings": crossings,
        "all_stds": stds
    })

print("===============================================================================================================")
print("=== PRE-REGISTERED N_sub TRADE-CURVE RESULTS (45.5 mV NOISE, 10 SEEDS EACH) ===")
print("===============================================================================================================")
print(f"{'N_sub Divider':<15} | {'Mean Crossing Cycles':<22} | {'Crossing Time (us)':<18} | {'Settled std (Fine LSBs)':<22}")
print("-" * 85)

for r in results_trade:
    print(f"N_sub = {r['n_sub']:<9} | {r['mean_cross_cycles']:>8,.0f} +/- {r['se_cross_cycles']:>6,.0f} cycles | {r['mean_cross_time_us']:>6.2f} us             | {r['mean_settled_std']:>6.3f} +/- {r['se_settled_std']:>5.3f} Fine LSBs")

print("===============================================================================================================\n")

# Verification of Prediction
print("EVALUATION OF PRE-REGISTERED PREDICTION:")
print(f"  * Speed Ratio (N_cross: 4 vs 16 vs 64):   {results_trade[0]['mean_cross_cycles']:.0f} -> {results_trade[1]['mean_cross_cycles']:.0f} -> {results_trade[2]['mean_cross_cycles']:.0f} cycles ({results_trade[0]['mean_cross_cycles']/results_trade[1]['mean_cross_cycles']:.2f}x : 1.00x : {results_trade[2]['mean_cross_cycles']/results_trade[1]['mean_cross_cycles']:.2f}x)")
print(f"  * Precision Ratio (std: 4 vs 16 vs 64):    {results_trade[0]['mean_settled_std']:.3f} -> {results_trade[1]['mean_settled_std']:.3f} -> {results_trade[2]['mean_settled_std']:.3f} LSBs ({results_trade[0]['mean_settled_std']/results_trade[1]['mean_settled_std']:.2f}x : 1.00x : {results_trade[2]['mean_settled_std']/results_trade[1]['mean_settled_std']:.2f}x)")

# Save CSV
out_csv = "p1_nsub_tradecurve_results.csv"
header = ["n_sub", "mean_cross_cycles", "se_cross_cycles", "mean_cross_time_us", "mean_settled_std", "se_settled_std"]
data_rows = [[r["n_sub"], r["mean_cross_cycles"], r["se_cross_cycles"], r["mean_cross_time_us"], r["mean_settled_std"], r["se_settled_std"]] for r in results_trade]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved trade-curve results CSV to '{out_csv}'.")
