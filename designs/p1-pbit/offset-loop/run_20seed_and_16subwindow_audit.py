import os, sys, time, csv, ctypes
import numpy as np

# Load C shared library with trajectory export
lib_path = './sim_pbit_loop.so'
c_lib = ctypes.CDLL(lib_path)

c_lib.run_pbit_export_trajectory.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_double,
    ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_int)
]
c_lib.run_pbit_export_trajectory.restype = ctypes.c_longlong

# ==============================================================================================================
# PRE-REGISTERED HYPOTHESIS PREDICTIONS (WRITTEN BEFORE RUNNING):
# 
# HYPOTHESIS 1: 20-Seed Equivalence Campaign (Python PCG64 vs C-Ported PCG64).
# HYPOTHESIS 2: 16-Disjoint-Subwindow Within-Trajectory Scatter Decomposition.
# 
# PRE-REGISTERED PREDICTIONS:
# 1. 20-Seed Campaign:
#    - Group means will match to < 0.5% (Py ~ 3.076 Fine LSBs vs C ~ 3.063 Fine LSBs).
#    - Relative scatter CV_C across 20 seeds will contract toward Bartlett prediction ~2.5%.
# 2. 16-Disjoint-Subwindow Within-Trajectory Scatter:
#    - Within-trajectory relative scatter CV_within across 16 sub-windows of a SINGLE trajectory will land
#      right on top of the Bartlett theoretical prediction (~2.3%..2.8%) in BOTH Python and C!
#    - This isolates the residual scatter 100% into seed-to-seed walk-in trajectory variation!
# ==============================================================================================================

print("=== EXECUTING TASK 1: 20-SEED EQUIVALENCE CAMPAIGN AND TASK 2: 16-SUBWINDOW DECOMPOSITION ===")
print("Running 20 Seeds in Python (PCG64) vs C (PCG64) and slicing settled windows into 16 disjoint sub-windows...\n")

f_s = 5.0e9; T_s = 1.0 / f_s
A_op = 314.7; delta_V_fine = 0.6118e-6; V_in_step = 10.0e-3; sigma_n_45mV = 45.5e-3
target_dac = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac = target_dac - 254                                # 114,473
n_sub_val = 16

stds_py_20 = []; stds_c_20 = []
cv_within_py_20 = []; cv_within_c_20 = []

max_cap = 15000000
c_arr_buffer = (ctypes.c_int * max_cap)()

t_start = time.time()

for seed_idx in range(1, 21): # 20 Seeds: 201..220
    seed_val = 200 + seed_idx
    
    # 1. Python Implementation
    rng_py = np.random.default_rng(seed=seed_val)
    block_size = 1000000
    noise_block_py = rng_py.normal(0.0, sigma_n_45mV, size=block_size)
    block_ptr_py = 0
    
    dac_history_py = []
    accumulator_val_py = 0
    curr_dac_code_py = start_dac
    k_py = 0
    crossing_cycle_py = -1
    
    r_n1 = 0.008980
    prev_noise_py = 0.0
    
    while True:
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
        dac_history_py.append(curr_dac_code_py)
        
        if crossing_cycle_py < 0 and curr_dac_code_py >= target_dac:
            crossing_cycle_py = k_py
            
        k_py += 1
        if crossing_cycle_py >= 0 and k_py >= (163 * crossing_cycle_py):
            break
            
    dac_arr_py = np.array(dac_history_py, dtype=np.float64)
    w_start_py = 2 * crossing_cycle_py
    w_end_py = 162 * crossing_cycle_py
    dac_settled_py = dac_arr_py[w_start_py:w_end_py]
    
    std_py_full = float(np.std(dac_settled_py))
    stds_py_20.append(std_py_full)
    
    # TASK 2: Slice Python settled window into 16 disjoint sub-windows
    sub_len_py = len(dac_settled_py) // 16
    sub_stds_py = [float(np.std(dac_settled_py[j*sub_len_py : (j+1)*sub_len_py])) for j in range(16)]
    cv_within_py = float(np.std(sub_stds_py, ddof=1) / np.mean(sub_stds_py))
    cv_within_py_20.append(cv_within_py)
    
    # 2. C Implementation via ctypes
    c_crossing = ctypes.c_longlong()
    k_c_total = c_lib.run_pbit_export_trajectory(seed_val, n_sub_val, sigma_n_45mV, ctypes.byref(c_crossing), c_arr_buffer)
    
    cross_c_val = c_crossing.value
    w_start_c = 2 * cross_c_val
    w_end_c = 162 * cross_c_val
    
    dac_arr_c = np.frombuffer(c_arr_buffer, dtype=np.int32, count=int(k_c_total)).astype(np.float64)
    dac_settled_c = dac_arr_c[w_start_c:w_end_c]
    
    std_c_full = float(np.std(dac_settled_c))
    stds_c_20.append(std_c_full)
    
    # TASK 2: Slice C settled window into 16 disjoint sub-windows
    sub_len_c = len(dac_settled_c) // 16
    sub_stds_c = [float(np.std(dac_settled_c[j*sub_len_c : (j+1)*sub_len_c])) for j in range(16)]
    cv_within_c = float(np.std(sub_stds_c, ddof=1) / np.mean(sub_stds_c))
    cv_within_c_20.append(cv_within_c)

t_elapsed = time.time() - t_start

# Compute Task 1 Statistics (Across 20 Seeds)
m_py_20 = np.mean(stds_py_20); sd_py_20 = np.std(stds_py_20, ddof=1); cv_between_py = sd_py_20 / m_py_20
m_c_20 = np.mean(stds_c_20); sd_c_20 = np.std(stds_c_20, ddof=1); cv_between_c = sd_c_20 / m_c_20
f_ratio_20 = (sd_c_20**2) / (sd_py_20**2)

# Compute Task 2 Statistics (Within-Trajectory 16 Sub-Windows Mean)
m_cv_within_py = np.mean(cv_within_py_20)
m_cv_within_c = np.mean(cv_within_c_20)

print("===============================================================================================================")
print("=== TASK 1: 20-SEED EQUIVALENCE CAMPAIGN RESULTS ===")
print("===============================================================================================================")
print(f"  * Campaign Execution Time:                     {t_elapsed:.2f} seconds wall-clock")
print(f"  * Python Group Mean (20 Seeds):                {m_py_20:.4f} Fine LSBs (SD = {sd_py_20:.4f}, CV_between = {cv_between_py*100:.2f}%)")
print(f"  * C-Ported Group Mean (20 Seeds):              {m_c_20:.4f} Fine LSBs (SD = {sd_c_20:.4f}, CV_between = {cv_between_c*100:.2f}%)")
print(f"  * Group Mean Discrepancy (C minus Py):         {m_c_20 - m_py_20:+.4f} Fine LSBs ({((m_c_20 - m_py_20)/m_py_20)*100:+.2f}%)")
print(f"  * Variance Ratio (F = Var_C / Var_Py):         F = {f_ratio_20:.2f} (Critical F_0.01 = 3.03)")
print("===============================================================================================================\n")

print("===============================================================================================================")
print("=== TASK 2: 16-DISJOINT-SUBWINDOW WITHIN-TRAJECTORY SCATTER DECOMPOSITION ===")
print("===============================================================================================================")
print(f"  * Python Mean Within-Trajectory Scatter CV_within: {m_cv_within_py*100:.2f}%")
print(f"  * C-Ported Mean Within-Trajectory Scatter CV_within: {m_cv_within_c*100:.2f}%")
print(f"  * Bartlett Theoretical Sub-Window Prediction:      ~9.80% (for N_sub_window ~ 248,500 samples)")
print("===============================================================================================================\n")

print("PER-SEED SCATTER DECOMPOSITION TABLE:")
print("Seed | Py std_full | Py CV_within | C std_full | C CV_within")
print("-----+-------------+--------------+------------+------------")
for i in range(20):
    s_val = 200 + i + 1
    print(f"{s_val:4d} | {stds_py_20[i]:11.4f} | {cv_within_py_20[i]*100:11.2f}% | {stds_c_20[i]:10.4f} | {cv_within_c_20[i]*100:10.2f}%")

# Save CSV
out_csv = "./p1_20seed_and_16subwindow_results.csv"
header = ["seed", "std_full_py", "cv_within_py_pct", "std_full_c", "cv_within_c_pct"]
data_rows = [[200 + i + 1, stds_py_20[i], cv_within_py_20[i]*100.0, stds_c_20[i], cv_within_c_20[i]*100.0] for i in range(20)]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\nSaved 20-seed and 16-subwindow decomposition CSV to '{out_csv}'.")
