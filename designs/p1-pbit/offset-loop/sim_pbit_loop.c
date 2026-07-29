#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>

static inline uint64_t pcg32_random_r(uint64_t *state, uint64_t inc) {
    uint64_t oldstate = *state;
    *state = oldstate * 6364136223846793005ULL + (inc | 1ULL);
    uint32_t xorshifted = ((oldstate >> 18u) ^ oldstate) >> 27u;
    uint32_t rot = oldstate >> 59u;
    return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
}

static inline double pcg_rand_double(uint64_t *state, uint64_t inc) {
    uint64_t r1 = pcg32_random_r(state, inc);
    uint64_t r2 = pcg32_random_r(state, inc);
    uint64_t combined = (r1 << 32) | r2;
    return (combined >> 11) * (1.0 / 9007199254740992.0);
}

static double rand_gaussian_pcg(uint64_t *state, uint64_t inc, double mean, double stddev) {
    double u1, u2;
    do {
        u1 = pcg_rand_double(state, inc);
    } while (u1 <= 1e-15);
    
    u2 = pcg_rand_double(state, inc);
    double z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
    return mean + z0 * stddev;
}

// Function to export raw C trajectory dac_history array directly to Python
long long run_pbit_export_trajectory(int seed_val, int n_sub_val, double sigma_n_val, long long *out_crossing, int *out_dac_array) {
    uint64_t pcg_state = (uint64_t)seed_val * 6364136223846793005ULL + 1442695040888963407ULL;
    uint64_t pcg_inc = (((uint64_t)seed_val + 1000000ULL) << 1u) | 1u;
    
    double delta_V_fine = 0.6118e-6;
    double A_op = 314.7;
    double V_in_step = 10.0e-3;
    
    int target_dac = 131072 - (int)round(V_in_step / delta_V_fine);
    int start_dac = target_dac - 254;
    
    int curr_dac_code = start_dac;
    long long accumulator_val = 0;
    
    long long crossing_cycle = -1;
    long long k = 0;
    long long cap_k = 15000000LL;
    
    double r_n1 = 0.008980;
    double prev_noise = 0.0;
    
    while (k < cap_k) {
        double v_res_in = V_in_step - (double)(131072 - curr_dac_code) * delta_V_fine;
        double v_res_amp = v_res_in * A_op;
        
        double white_k = rand_gaussian_pcg(&pcg_state, pcg_inc, 0.0, sigma_n_val);
        double latch_noise = r_n1 * prev_noise + sqrt(1.0 - r_n1 * r_n1) * white_k;
        prev_noise = latch_noise;
        
        double v_latch = v_res_amp + latch_noise;
        
        int b_k = (v_latch > 0.0) ? 1 : 0;
        accumulator_val += (1 - 2 * b_k);
        curr_dac_code = start_dac + (int)(accumulator_val / n_sub_val);
        out_dac_array[k] = curr_dac_code;
        
        if (crossing_cycle < 0 && curr_dac_code >= target_dac) {
            crossing_cycle = k;
        }
        
        k++;
        if (crossing_cycle >= 0 && k >= (163 * crossing_cycle)) {
            break;
        }
    }
    
    *out_crossing = crossing_cycle;
    return k;
}

// Compute std of settled dither loop
double run_pbit_seed(int seed_val, int n_sub_val, double sigma_n_val, long long *out_crossing) {
    uint64_t pcg_state = (uint64_t)seed_val * 6364136223846793005ULL + 1442695040888963407ULL;
    uint64_t pcg_inc = (((uint64_t)seed_val + 1000000ULL) << 1u) | 1u;
    
    double delta_V_fine = 0.6118e-6;
    double A_op = 314.7;
    double V_in_step = 10.0e-3;
    
    int target_dac = 131072 - (int)round(V_in_step / delta_V_fine);
    int start_dac = target_dac - 254;
    
    int curr_dac_code = start_dac;
    long long accumulator_val = 0;
    
    long long crossing_cycle = -1;
    long long k = 0;
    long long cap_k = 15000000LL;
    
    int *dac_history = (int*)malloc(sizeof(int) * cap_k);
    if (!dac_history) {
        *out_crossing = -1;
        return -1.0;
    }
    
    double r_n1 = 0.008980;
    double prev_noise = 0.0;
    
    while (k < cap_k) {
        double v_res_in = V_in_step - (double)(131072 - curr_dac_code) * delta_V_fine;
        double v_res_amp = v_res_in * A_op;
        
        double white_k = rand_gaussian_pcg(&pcg_state, pcg_inc, 0.0, sigma_n_val);
        double latch_noise = r_n1 * prev_noise + sqrt(1.0 - r_n1 * r_n1) * white_k;
        prev_noise = latch_noise;
        
        double v_latch = v_res_amp + latch_noise;
        
        int b_k = (v_latch > 0.0) ? 1 : 0;
        accumulator_val += (1 - 2 * b_k);
        curr_dac_code = start_dac + (int)(accumulator_val / n_sub_val);
        dac_history[k] = curr_dac_code;
        
        if (crossing_cycle < 0 && curr_dac_code >= target_dac) {
            crossing_cycle = k;
        }
        
        k++;
        if (crossing_cycle >= 0 && k >= (163 * crossing_cycle)) {
            break;
        }
    }
    
    *out_crossing = crossing_cycle;
    
    long long w_start = 2 * crossing_cycle;
    long long w_end = 162 * crossing_cycle;
    long long count = w_end - w_start;
    
    if (crossing_cycle < 0 || w_end > k) {
        free(dac_history);
        return -1.0;
    }
    
    double shift_sum = 0.0;
    double shift_sum_sq = 0.0;
    double target_ref = (double)target_dac;
    
    for (long long i = w_start; i < w_end; i++) {
        double dx = (double)dac_history[i] - target_ref;
        shift_sum += dx;
        shift_sum_sq += dx * dx;
    }
    
    double dx_mean = shift_sum / (double)count;
    double var_shifted = (shift_sum_sq / (double)count) - (dx_mean * dx_mean);
    
    free(dac_history);
    return sqrt(var_shifted);
}
