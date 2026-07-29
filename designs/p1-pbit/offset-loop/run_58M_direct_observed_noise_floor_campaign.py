import os, sys, time, csv, ctypes
import numpy as np

# Load C shared library
lib_path = './sim_pbit_loop.so'
c_lib = ctypes.CDLL(lib_path)

c_lib.run_pbit_long_trajectory.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_double,
    ctypes.c_longlong, ctypes.POINTER(ctypes.c_int)
]
c_lib.run_pbit_long_trajectory.restype = ctypes.c_longlong

# ==============================================================================================================
# PRE-REGISTERED HYPOTHESIS PREDICTIONS (WRITTEN BEFORE RUNNING):
# 
# HYPOTHESIS: 58-Million Cycle Direct Observed Noise Floor Campaign.
#             One continuous 58,100,000 cycle trajectory per implementation (Seed 201).
#             K_start = 100,000 cycles walk-in settling.
#             20 disjoint non-overlapping windows of EXACTLY W_sub = 2,900,000 cycles each.
# 
# PRE-REGISTERED PREDICTIONS:
# 1. Direct Observed Floor CV_floor,observed:
#    - The direct observed noise floor CV_floor,observed will land between 2.2% and 2.9%
#      (SD_floor ~ 0.068 .. 0.089 Fine LSBs).
# 2. Deficit Significance:
#    - Python across-seed scatter (1.84% = 0.0566 LSBs) compared against this direct observed floor
#      will yield a deficit at less than 2-sigma (p > 0.05), proving any apparent Python deficit
#      is statistically un-established on 20 seeds!
# ==============================================================================================================

print("=== EXECUTING PRE-REGISTERED 58-MILLION CYCLE DIRECT OBSERVED NOISE FLOOR CAMPAIGN ===")
print("Generating 58,100,000 cycle continuous trajectories (Seed 201) in Python and C...")
print("Cutting into 20 disjoint windows of W_sub = 2,900,000 cycles each...\n")

f_s = 5.0e9; T_s = 1.0 / f_s
A_op = 314.7; delta_V_fine = 0.6118e-6; V_in_step = 10.0e-3; sigma_n_45mV = 45.5e-3
target_dac = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac = target_dac - 254                                # 114,473
n_sub_val = 16

seed_val = 201
k_start_offset = 100000
w_window_len = 2900000
num_disjoint_windows = 20
total_k_needed = k_start_offset + num_disjoint_windows * w_window_len # 58,100,000 cycles

t_start = time.time()

# 1. Python Implementation (58.1M Cycles)
print(f"  [1/2] Running Python PCG64 Ziggurat 58.1M cycle trajectory...")
rng_py = np.random.default_rng(seed=seed_val)
block_size = 5000000
noise_block_py = rng_py.normal(0.0, sigma_n_45mV, size=block_size)
block_ptr_py = 0

dac_history_py = np.empty(total_k_needed, dtype=np.int32)
accumulator_val_py = 0
curr_dac_code_py = start_dac

r_n1 = 0.008980
prev_noise_py = 0.0

for k_py in range(total_k_needed):
    v_res_in = V_in_step - (131072 - curr_dac_code_py) * delta_V_fine
    v_res_amp = v_res_in * A_op
    
    if block_ptr_py >= block_size:
        noise_block_py = rng_py.normal(0.0, sigma_n_45mV, size=block_size)
        block_ptr_py = 0
        
    white_k = noise_block_py[block_ptr_py]
    block_ptr_py += 1
    
    latch_noise = r_n1 * prev_noise_py + np.sqrt(1.0 - r_n1 * r_n1) * white_k
    prev_noise_py = latch_noise
    
    v_latch_diff = v_res_amp + latch_noise
    b_k = 1 if v_latch_diff > 0 else 0
    
    accumulator_val_py += (1 - 2 * b_k)
    curr_dac_code_py = start_dac + int(accumulator_val_py // n_sub_val)
    dac_history_py[k_py] = curr_dac_code_py

print("  [1/2] Python trajectory generation completed.")

# 2. C Implementation via ctypes (58.1M Cycles)
print(f"  [2/2] Running C PCG64 Box-Muller 58.1M cycle trajectory...")
c_arr_buffer = (ctypes.c_int * total_k_needed)()
c_lib.run_pbit_long_trajectory(seed_val, n_sub_val, sigma_n_45mV, total_k_needed, c_arr_buffer)
dac_history_c = np.frombuffer(c_arr_buffer, dtype=np.int32, count=total_k_needed)
print("  [2/2] C trajectory generation completed.")

t_elapsed = time.time() - t_start

# Compute 20 Disjoint Sub-Window Standard Deviations for Python and C
stds_py_20win = []
stds_c_20win = []

for j in range(num_disjoint_windows):
    w_start_j = k_start_offset + j * w_window_len
    w_end_j = w_start_j + w_window_len
    
    std_py_j = float(np.std(dac_history_py[w_start_j:w_end_j].astype(np.float64)))
    std_c_j = float(np.std(dac_history_c[w_start_j:w_end_j].astype(np.float64)))
    
    stds_py_20win.append(std_py_j)
    stds_c_20win.append(std_c_j)

# Compute Direct Observed Noise Floor Statistics
m_py_floor = float(np.mean(stds_py_20win))
sd_py_floor = float(np.std(stds_py_20win, ddof=1))
cv_py_floor = sd_py_floor / m_py_floor

m_c_floor = float(np.mean(stds_c_20win))
sd_c_floor = float(np.std(stds_c_20win, ddof=1))
cv_c_floor = sd_c_floor / m_c_floor

# Small-sample bias correction factor c4(20) = 0.9869
c4_20 = 0.9869
cv_py_floor_unbiased = cv_py_floor / c4_20
cv_c_floor_unbiased = cv_c_floor / c4_20

print("===============================================================================================================")
print("=== 58-MILLION CYCLE DIRECT OBSERVED NOISE FLOOR CAMPAIGN RESULTS ===")
print("===============================================================================================================")
print(f"  * Campaign Execution Time:                       {t_elapsed:.2f} seconds wall-clock\n")

print(f"  * Python Direct Observed Floor (CV_floor):       {cv_py_floor*100:.2f}% (Unbiased c4-corrected = {cv_py_floor_unbiased*100:.2f}%)")
print(f"    - Mean dither std across 20 windows:            {m_py_floor:.4f} Fine LSBs")
print(f"    - Standard deviation of std across 20 windows:  {sd_py_floor:.4f} Fine LSBs\n")

print(f"  * C-Ported Direct Observed Floor (CV_floor):     {cv_c_floor*100:.2f}% (Unbiased c4-corrected = {cv_c_floor_unbiased*100:.2f}%)")
print(f"    - Mean dither std across 20 windows:            {m_c_floor:.4f} Fine LSBs")
print(f"    - Standard deviation of std across 20 windows:  {sd_c_floor:.4f} Fine LSBs\n")

print("===============================================================================================================")
print("=== COMPARISON OF ACROSS-SEED SCATTER (20 SEEDS) VS DIRECT OBSERVED NOISE FLOOR ===")
print("===============================================================================================================")
# Fixed window across-seed scatter numbers from previous run:
# Py across-seed: SD = 0.0566 LSBs (CV = 1.84%)
# C across-seed:  SD = 0.0937 LSBs (CV = 3.05%)
cv_py_across_seed = 0.0184
cv_c_across_seed = 0.0305

ratio_py_vs_floor = cv_py_across_seed / cv_py_floor
ratio_c_vs_floor = cv_c_across_seed / cv_c_floor

# Chi-squared test for Python across-seed variance vs observed floor variance (df=19)
chi2_py = 19.0 * (cv_py_across_seed**2) / (cv_py_floor**2)

print(f"  * Python Across-Seed Scatter (CV = 1.84%) vs Direct Floor (CV = {cv_py_floor*100:.2f}%):")
print(f"    - Ratio (Across-Seed / Direct Floor):           {ratio_py_vs_floor:.2f}x")
print(f"    - Chi-Squared (df=19):                           chi2 = {chi2_py:.2f}")

print(f"\n  * C-Ported Across-Seed Scatter (CV = 3.05%) vs Direct Floor (CV = {cv_c_floor*100:.2f}%):")
print(f"    - Ratio (Across-Seed / Direct Floor):           {ratio_c_vs_floor:.2f}x")

print("===============================================================================================================\n")

print("20 DISJOINT WINDOWS DETAILED TABLE (W_sub = 2,900,000 cycles each):")
print("Window # | Window Range (cycles)    | Python dither std | C-Ported dither std | Delta (C - Py)")
print("---------+--------------------------+-------------------+--------------------+---------------")
for j in range(num_disjoint_windows):
    w_s = k_start_offset + j * w_window_len
    w_e = w_s + w_window_len
    d_j = stds_c_20win[j] - stds_py_20win[j]
    print(f"  {j+1:2d}     | [{w_s:10,d} : {w_e:10,d}] | {stds_py_20win[j]:17.4f} | {stds_c_20win[j]:18.4f} | {d_j:+14.4f}")

# Save CSV
out_csv = "./p1_58M_direct_observed_noise_floor_results.csv"
header = ["window_idx", "window_start", "window_end", "std_py_win", "std_c_win", "delta_c_minus_py"]
data_rows = [[j+1, k_start_offset + j*w_window_len, k_start_offset + (j+1)*w_window_len, stds_py_20win[j], stds_c_20win[j], stds_c_20win[j] - stds_py_20win[j]] for j in range(num_disjoint_windows)]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved 58M direct observed noise floor CSV to '{out_csv}'.")
