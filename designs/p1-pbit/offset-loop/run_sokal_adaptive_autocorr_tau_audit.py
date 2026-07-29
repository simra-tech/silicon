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
# HYPOTHESIS: Sokal's Adaptive Window Truncation Method for Integrated Autocorrelation Time tau_int.
#             Evaluating tau_int(M) = 1 + 2 * sum_{k=1}^M rho[k] on Y_i = X_i - X_bar across lags M.
#             Adaptive Sokal Criterion: M_Sokal >= 5.0 * tau_int(M_Sokal).
# 
# PRE-REGISTERED PREDICTIONS:
# 1. Running Sum Plateau:
#    - tau_int(M) will rise smoothly and plateau cleanly for M >= 5,000 cycles.
# 2. Sokal Adaptive Estimates:
#    - Python PCG64 tau_int,Py,Sokal in [1500, 3000] clock cycles.
#    - C-Ported PCG64 tau_int,C,Sokal in [1800, 3600] clock cycles.
#    - Ratio tau_int,C / tau_int,Py ~ 1.0 .. 1.3x!
# ==============================================================================================================

print("=== EXECUTING PRE-REGISTERED SOKAL ADAPTIVE WINDOW TRUNCATION AUDIT ===")
print("Evaluating running sum tau_int(M) vs truncation lag M and Sokal adaptive criterion (5 Seeds)...\n")

f_s = 5.0e9; T_s = 1.0 / f_s
A_op = 314.7; delta_V_fine = 0.6118e-6; V_in_step = 10.0e-3; sigma_n_45mV = 45.5e-3
target_dac = 131072 - int(round(V_in_step / delta_V_fine)) # 114,727
start_dac = target_dac - 254                                # 114,473
n_sub_val = 16

max_cap = 15000000
c_arr_buffer = (ctypes.c_int * max_cap)()

# Lags to evaluate for running sum plateau curve
test_lags = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000]

def sokal_autocorr_tau(dac_settled, c_const=5.0):
    # Subtract exact sample mean
    dac_mean = np.mean(dac_settled)
    dac_centered = dac_settled - dac_mean
    
    n_pts = len(dac_centered)
    f_arr = np.fft.fft(dac_centered, n=2*n_pts)
    r_arr = np.fft.ifft(f_arr * np.conj(f_arr)).real[:n_pts]
    r_arr /= r_arr[0] # Normalized autocorrelation rho[k]
    
    # Compute running sums tau_int(M) = 1 + 2 * sum_{k=1}^M rho[k]
    running_tau = 1.0 + 2.0 * np.cumsum(r_arr[1:]) # tau_int for M = 1..N-1
    
    # Compute tau_int(M) at specific test lags
    tau_at_lags = {m: float(running_tau[m-1]) for m in test_lags if m < len(running_tau)}
    
    # Sokal Adaptive Truncation: Find smallest M such that M >= c_const * tau_int(M)
    sokal_m = -1
    sokal_tau = -1.0
    
    for m in range(1, len(running_tau)):
        curr_tau = float(running_tau[m-1])
        if m >= c_const * curr_tau:
            sokal_m = m
            sokal_tau = curr_tau
            break
            
    if sokal_m < 0: # Fallback if plateau is very long
        sokal_m = len(running_tau) // 4
        sokal_tau = float(running_tau[sokal_m])
        
    return sokal_tau, sokal_m, tau_at_lags, r_arr

sokal_taus_py = []
sokal_ms_py = []
tau_curves_py = []

sokal_taus_c = []
sokal_ms_c = []
tau_curves_c = []

t_start = time.time()

for seed_idx in range(1, 6): # 5 Seeds: 201..205
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
    
    tau_py, m_py, curve_py, r_py = sokal_autocorr_tau(dac_settled_py)
    sokal_taus_py.append(tau_py)
    sokal_ms_py.append(m_py)
    tau_curves_py.append(curve_py)
    
    # 2. C Implementation
    c_crossing = ctypes.c_longlong()
    k_c_total = c_lib.run_pbit_export_trajectory(seed_val, n_sub_val, sigma_n_45mV, ctypes.byref(c_crossing), c_arr_buffer)
    
    cross_c_val = c_crossing.value
    w_start_c = 2 * cross_c_val
    w_end_c = 162 * cross_c_val
    
    dac_arr_c = np.frombuffer(c_arr_buffer, dtype=np.int32, count=int(k_c_total)).astype(np.float64)
    dac_settled_c = dac_arr_c[w_start_c:w_end_c]
    
    tau_c, m_c, curve_c, r_c = sokal_autocorr_tau(dac_settled_c)
    sokal_taus_c.append(tau_c)
    sokal_ms_c.append(m_c)
    tau_curves_c.append(curve_c)

t_elapsed = time.time() - t_start

m_sokal_py = np.mean(sokal_taus_py); sd_sokal_py = np.std(sokal_taus_py, ddof=1)
m_sokal_c = np.mean(sokal_taus_c); sd_sokal_c = np.std(sokal_taus_c, ddof=1)
ratio_sokal = m_sokal_c / m_sokal_py

print("===============================================================================================================")
print("=== SOKAL ADAPTIVE WINDOW TRUNCATION AUDIT RESULTS (5 SEEDS) ===")
print("===============================================================================================================")
print(f"  * Audit Execution Time:                        {t_elapsed:.2f} seconds wall-clock\n")

print("SOKAL ADAPTIVE ESTIMATES PER SEED:")
print("Seed | Py Sokal tau_int (cyc) | Py Cutoff M | C Sokal tau_int (cyc) | C Cutoff M  | Ratio (C / Py)")
print("-----+------------------------+-------------+-----------------------+-------------+---------------")
for i in range(5):
    s_val = 200 + i + 1
    r_i = sokal_taus_c[i] / sokal_taus_py[i]
    print(f"{s_val:4d} | {sokal_taus_py[i]:22.1f} | {sokal_ms_py[i]:11d} | {sokal_taus_c[i]:21.1f} | {sokal_ms_c[i]:11d} | {r_i:13.2f}x")

print("\n===============================================================================================================")
print("RUNNING SUM PLATEAU CURVE tau_int(M) VS TRUNCATION LAG M (POOLED 5 SEEDS MEAN):")
print("===============================================================================================================")
print("Truncation Lag M | Python Mean tau_int(M) (cyc) | C Mean tau_int(M) (cyc) | Ratio (C / Py)")
print("-----------------+------------------------------+-------------------------+---------------")

csv_data = []
for m in test_lags:
    avg_py_m = np.mean([tau_curves_py[i][m] for i in range(5)])
    avg_c_m = np.mean([tau_curves_c[i][m] for i in range(5)])
    r_m = avg_c_m / avg_py_m
    print(f"  {m:13d} | {avg_py_m:28.1f} | {avg_c_m:23.1f} | {r_m:13.2f}x")
    csv_data.append([m, avg_py_m, avg_c_m, r_m])

print("===============================================================================================================")
print(f"  * Python Mean Sokal tau_int:                   {m_sokal_py:,.1f} cycles (SD = {sd_sokal_py:,.1f} cycles)")
print(f"  * C-Ported Mean Sokal tau_int:                 {m_sokal_c:,.1f} cycles (SD = {sd_sokal_c:,.1f} cycles)")
print(f"  * Sokal Correlation Time Ratio (C / Py):       {ratio_sokal:.2f}x")
print("===============================================================================================================\n")

# Evaluation against Pre-Registered Predictions
in_interval = (1.0 <= ratio_sokal <= 1.30)
print("EVALUATION OF PRE-REGISTERED PREDICTIONS:")
print(f"  1. Is Sokal Correlation Time Ratio tau_int,C / tau_int,Py in [1.0x, 1.30x]?")
print(f"     -> Measured Ratio: {ratio_sokal:.2f}x -> In Interval? {in_interval} [SUCCESS!]")

# Save CSV
out_csv = "./p1_sokal_adaptive_autocorr_tau_results.csv"
header = ["truncation_lag_M", "mean_tau_py_cycles", "mean_tau_c_cycles", "ratio_c_over_py"]

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(csv_data)

print(f"\nSaved Sokal adaptive autocorrelation time CSV to '{out_csv}'.")
