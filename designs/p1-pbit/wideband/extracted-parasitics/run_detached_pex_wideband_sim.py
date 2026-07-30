import os, sys, subprocess, time, numpy as np

log_file = "./pex_corr_progress.log"

# Clean previous log
if os.path.exists(log_file):
    os.remove(log_file)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(log_file, "a") as f:
        f.write(formatted + "\n")

log("=== Starting 7-Rate Sweep PEX Correlation Campaign (Linear Interpolation) ===")

published_ref = {
    1.0: +0.0071,
    1.5: +0.0071,
    2.0: +0.0071,
    2.5: +0.0071,
    3.0: +0.0071,
    4.0: +0.0071,
    5.0: +0.0071,
}

rates_ghz = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

# Total duration: 17.0 us across 17 chunks of 1.0 us
total_segments = 17
all_time_vectors = []
all_vdiff_vectors = []

# Check if previous segment numpy backup exists
npy_time_backup = "./pex_time_backup.npy"
npy_vdiff_backup = "./pex_vdiff_backup.npy"

if os.path.exists(npy_time_backup) and os.path.exists(npy_vdiff_backup):
    all_time_vectors = list(np.load(npy_time_backup, allow_pickle=True))
    all_vdiff_vectors = list(np.load(npy_vdiff_backup, allow_pickle=True))
    start_seg = len(all_vdiff_vectors) + 1
    log(f"Resuming campaign from Segment {start_seg} ({len(all_vdiff_vectors)} us completed).")
else:
    start_seg = 1

for seg in range(start_seg, total_segments + 1):
    log(f"--- Segment {seg}/{total_segments} (1.0 us chunk) ---")
    tb_spice = f"""* PEX Wideband Correlation Segment {seg}
.lib $PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib hbt_typ
.lib $PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ

.options rshunt = 1e12

VCC VCC 0 DC 2.5
VSS VSS 0 DC 0

VB1 VB1 0 DC 1.062 TRNOISE(1.0mV 2.0ps 0 0)
VB2 VB2 0 DC 1.062 TRNOISE(1.0mV 2.0ps 0 0)

RTAIL IE 0 100.0

.include ./p1_noise_gen_pex.spice

.control
tran 100p 1u 0 0.5p
wrdata ./pex_chunk.txt v(raw_noise_p)-v(raw_noise_n)
.endc
.end
"""
    chunk_cir = f"./tb_pex_chunk_{seg}.cir"
    with open(chunk_cir, "w") as f:
        f.write(tb_spice)
    
    t0 = time.time()
    res = subprocess.run(["ngspice", "-b", chunk_cir], capture_output=True, text=True)
    t1 = time.time()
    
    chunk_txt = "./pex_chunk.txt"
    if not os.path.exists(chunk_txt):
        log(f"FATAL: Segment {seg} output file '{chunk_txt}' not found!")
        sys.exit(1)
        
    data = np.loadtxt(chunk_txt)
    time_vec = data[:, 0] + (seg - 1) * 1.0e-6
    vdiff = data[:, 1]
    
    all_time_vectors.append(time_vec)
    all_vdiff_vectors.append(vdiff)
    
    np.save(npy_time_backup, np.array(all_time_vectors, dtype=object))
    np.save(npy_vdiff_backup, np.array(all_vdiff_vectors, dtype=object))
    
    os.remove(chunk_cir)
    os.remove(chunk_txt)
    
    # Concatenate continuous time and voltage series
    full_time = np.concatenate(all_time_vectors)
    full_vdiff = np.concatenate(all_vdiff_vectors)
    total_dur = full_time[-1] - full_time[0]
    
    log(f"Segment {seg} done in {t1 - t0:.1f} s. Cumulative time: {total_dur*1e6:.2f} us.")
    log(f"Current Multi-Rate Correlation Table ({total_dur*1e6:.2f} us total duration):")
    log(f"{'Nominal (GHz)':<12} | {'T_nom (ps)':<10} | {'T_achieved (ps)':<15} | {'Bits N':<10} | {'r_1 Extracted':<16} | {'SE (1/sqrt N)':<12} | {'Baseline r_1':<12} | {'Z-score':<8}")
    log("-" * 105)
    
    for f_ghz in rates_ghz:
        t_nom = 1.0e-9 / f_ghz
        t_grid = np.arange(full_time[0], full_time[-1], t_nom)
        v_interp = np.interp(t_grid, full_time, full_vdiff)
        
        t_achieved = (t_grid[1] - t_grid[0]) if len(t_grid) > 1 else t_nom
        N_bits = len(v_interp)
        
        v_bar = np.mean(v_interp)
        v_zero = v_interp - v_bar
        
        r0 = np.sum(v_zero ** 2)
        r1 = np.sum(v_zero[:-1] * v_zero[1:]) / r0 if r0 > 0 else 0.0
        se = 1.0 / np.sqrt(N_bits) if N_bits > 0 else 0.0
        
        z = (r1 - published_ref[f_ghz]) / se if se > 0 else 0.0
        log(f"{f_ghz:<12.1f} | {t_nom*1e12:<10.2f} | {t_achieved*1e12:<15.2f} | {N_bits:<10d} | {r1:<+16.6f} | +/- {se:<10.6f} | {published_ref[f_ghz]:<+12.4f} | {z:<+8.2f}")

log("=== FINAL 7-RATE SWEEP PEX CORRELATION CAMPAIGN COMPLETE ===")
