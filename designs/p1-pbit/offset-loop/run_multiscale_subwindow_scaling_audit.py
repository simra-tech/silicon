import os, sys, time, csv, ctypes
import numpy as np

# Load C shared library
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
# HYPOTHESIS: Multiscale Sub-Window Scaling Audit for k in {2, 4, 8, 16} Disjoint Sub-Windows.
#             Testing whether within-run scatter CV_within(k) scales as sqrt(k) matching Bartlett theory.
# 
# PRE-REGISTERED PREDICTIONS:
# 1. Scaling Law:
#    - CV_within(k) will scale strictly as sqrt(k) on BOTH Python and C implementations.
# 2. Predicted Values at k in {2, 4, 8, 16} (for W_fixed = 2,900,000 cycles, tau_int ~ 8,600 cycles):
#    - k = 2  (W_sub ~ 1,450,000 cyc): CV_pred(2)  ~ 3.46%
#    - k = 4  (W_sub ~   725,000 cyc): CV_pred(4)  ~ 4.90%
#    - k = 8  (W_sub ~   362,500 cyc): CV_pred(8)  ~ 6.93%
#    - k = 16 (W_sub ~   181,250 cyc): CV_pred(16) ~ 9.80%
# ==============================================================================================================

print("=== EXECUTING PRE-REGISTERED MULTISCALE SUB-WINDOW SCALING AUDIT ===")
print("Slicing fixed common window [100k : 3.0M] cycles into k in {2, 4, 8, 16} disjoint sub-windows...\n")

f_s = 5.0e9; T_s = 1.0 / f_s
A_op = 314.7; delta_V_fine = 0.6118e-6; V_in_step = 10.0e-3; sigma_n_45mV = 45.5e-3
target_dac = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac = target_dac - 254                                # 114,473
n_sub_val = 16

k_fixed_start = 100000
k_fixed_end = 3000000
w_total_len = k_fixed_end - k_fixed_start # 2,900,000 cycles

k_levels = [2, 4, 8, 16]

cv_multiscale_py = {k: [] for k in k_levels}
cv_multiscale_c = {k: [] for k in k_levels}

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
    
    r_n1 = 0.008980
    prev_noise_py = 0.0
    
    for k_py in range(k_fixed_end):
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
            
    dac_arr_py = np.array(dac_history_py, dtype=np.float64)
    dac_settled_py = dac_arr_py[k_fixed_start:k_fixed_end]
    
    # Evaluate k in {2, 4, 8, 16} sub-windows for Python
    for k in k_levels:
        sub_len = len(dac_settled_py) // k
        sub_stds = [float(np.std(dac_settled_py[j*sub_len : (j+1)*sub_len])) for j in range(k)]
        cv_k = float(np.std(sub_stds, ddof=1) / np.mean(sub_stds))
        cv_multiscale_py[k].append(cv_k)
        
    # 2. C Implementation via ctypes
    c_crossing = ctypes.c_longlong()
    k_c_total = c_lib.run_pbit_export_trajectory(seed_val, n_sub_val, sigma_n_45mV, ctypes.byref(c_crossing), c_arr_buffer)
    
    dac_arr_c = np.frombuffer(c_arr_buffer, dtype=np.int32, count=int(k_c_total)).astype(np.float64)
    dac_settled_c = dac_arr_c[k_fixed_start:k_fixed_end]
    
    # Evaluate k in {2, 4, 8, 16} sub-windows for C
    for k in k_levels:
        sub_len = len(dac_settled_c) // k
        sub_stds = [float(np.std(dac_settled_c[j*sub_len : (j+1)*sub_len])) for j in range(k)]
        cv_k = float(np.std(sub_stds, ddof=1) / np.mean(sub_stds))
        cv_multiscale_c[k].append(cv_k)

t_elapsed = time.time() - t_start

# Compute Bartlett Predictions for W_fixed = 2,900,000 cycles and tau_int = 8,668 cycles
tau_int_ref = 8668.0
bartlett_preds = {}
for k in k_levels:
    w_sub = w_total_len / float(k)
    n_eff_sub = w_sub / (2.0 * tau_int_ref)
    cv_bartlett = float(np.sqrt(1.0 / (2.0 * n_eff_sub)))
    bartlett_preds[k] = cv_bartlett

print("===============================================================================================================")
print("=== MULTISCALE SUB-WINDOW SCALING AUDIT RESULTS (20 SEEDS, k in {2, 4, 8, 16}) ===")
print("===============================================================================================================")
print(f"  * Audit Execution Time:                         {t_elapsed:.2f} seconds wall-clock\n")

print("MULTISCALE SCALING COMPARISON TABLE:")
print("Sub-Windows k | Bartlett Prediction | Python CV_within (Mean) | C-Ported CV_within (Mean) | Ratio (C / Py)")
print("--------------+---------------------+-------------------------+---------------------------+---------------")

csv_data = []
for k in k_levels:
    m_py_k = float(np.mean(cv_multiscale_py[k])) * 100.0
    m_c_k = float(np.mean(cv_multiscale_c[k])) * 100.0
    pred_k = bartlett_preds[k] * 100.0
    r_k = m_c_k / m_py_k
    print(f"  k = {k:2d}      | {pred_k:17.2f}% | {m_py_k:21.2f}% | {m_c_k:23.2f}% | {r_k:13.2f}x")
    csv_data.append([k, pred_k, m_py_k, m_c_k, r_k])

print("===============================================================================================================\n")

# Save CSV
out_csv = "./p1_multiscale_subwindow_scaling_results.csv"
header = ["subwindows_k", "bartlett_pred_pct", "mean_cv_within_py_pct", "mean_cv_within_c_pct", "ratio_c_over_py"]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(csv_data)

print(f"Saved multiscale sub-window scaling CSV to '{out_csv}'.")
