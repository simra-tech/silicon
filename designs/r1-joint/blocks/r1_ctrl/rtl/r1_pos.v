// R1_CTRL / r1_pos: encoder position path.
//   sin/cos pair (12-bit offset-binary codes) -> offset, gain-ratio and phase
//   correction (Heydemann form) -> iterative CORDIC vectoring (18 iterations,
//   20-bit x/y, 18-bit angle) -> 3rd-harmonic angle correction -> type-II
//   tracking loop running as an NCO on every clk tick -> extrapolated
//   position, turn counter, velocity, amplitude and flags.
// One 20 x 17 signed multiplier is shared by all steps. A pair is processed in
// 27 clk cycles after smp_valid; the sample scheduler (r1_gate) spaces pairs
// by PAIR_TICKS (default 30). A pair that arrives while busy is dropped and
// flagged (overrun).
// Number formats: R1_REGISTER_MAP.md section 5.
// SPDX-License-Identifier: Apache-2.0

module r1_pos (
    input  wire        clk,
    input  wire        rst_n,
    // sample interface (from the scheduler / ADC)
    input  wire        smp_sh,          // pulse: track-and-holds take the pair now
    input  wire        smp_valid,       // pulse: sin_code / cos_code valid
    input  wire [11:0] sin_code,        // offset binary, mid-scale 0x800
    input  wire [11:0] cos_code,
    // calibration and configuration (registers)
    input  wire [11:0] ofs_sin,         // signed, ADC LSB
    input  wire [11:0] ofs_cos,
    input  wire [15:0] gain,            // Q2.14, multiplies the sine channel
    input  wire [15:0] ph_sin,          // Q1.15 signed, sin(alpha)
    input  wire [15:0] ph_icos,         // Q2.14, 1/cos(alpha)
    input  wire [7:0]  h3_amp,          // 16-bit angle LSB
    input  wire [7:0]  h3_ph,           // 1/256 turn
    input  wire [15:0] zero_ofs,        // 16-bit angle LSB
    input  wire        dir,
    input  wire [3:0]  kp_sh,           // loop proportional gain 2^-kp
    input  wire [4:0]  ki_sh,           // loop integral gain 2^-ki per tick
    input  wire [7:0]  extrap,          // extrapolation, clk ticks
    input  wire [7:0]  amp_lo,          // amplitude thresholds, 16 ADC LSB units
    input  wire [7:0]  amp_hi,
    input  wire [15:0] ovs_lim,         // |velocity| limit, VELOCITY units
    // outputs
    output reg  [17:0] pos_out,         // 16.2 bit angle, extrapolated, after zero/dir
    output reg  [15:0] turns,
    output wire [15:0] velocity,        // signed, 2^-5 LSB16 per tick
    output reg  [11:0] amplitude,       // ADC LSB
    output reg  [11:0] raw_sin,
    output reg  [11:0] raw_cos,
    output reg  [17:0] meas_angle,      // corrected measured angle of the last pair (18 bit)
    output reg         meas_stb,        // pulse when meas_angle updates
    output reg         amp_low,
    output reg         amp_high,
    output wire        overspeed,
    output reg         track_err,
    output reg         overrun,         // pulse
    output reg         pos_valid
);
    // ---------------- shared multiplier ----------------
    reg  signed [19:0] mul_a;
    reg  signed [16:0] mul_b;
    wire signed [36:0] prod = mul_a * mul_b;

    // ---------------- state ----------------
    localparam S_IDLE = 4'd0, S_M1 = 4'd1, S_M2 = 4'd2, S_M3 = 4'd3, S_C0 = 4'd4,
               S_CI = 4'd5, S_P1 = 4'd6, S_P2 = 4'd7, S_L1 = 4'd8, S_L2 = 4'd9;
    reg [3:0]  st;
    reg [4:0]  it;

    reg signed [12:0] ds, dc;           // offset-corrected samples
    reg signed [20:0] sg;               // sine * gain, 4 fractional bits
    reg signed [19:0] dd;               // sg - x*sin(alpha), saturated
    reg signed [19:0] cx, cy;           // CORDIC x, y (5 fractional bits)
    reg        [17:0] cz;               // CORDIC angle, 2^18 = one turn
    reg        [17:0] th_m;             // corrected measured angle
    reg        [17:0] snap_a, snap_b;   // NCO angle at the track-and-hold instant
    reg signed [35:0] theta;            // NCO angle, 16.20 (wraps)
    reg signed [31:0] omega;            // 2^-20 LSB16 per tick
    reg signed [27:0] ext;              // omega * extrap, 2^-8 LSB16
    reg [1:0]  lo_cnt, hi_cnt;
    reg [4:0]  lock_cnt;
    reg        sh_pend;

    // arctan table, 2^18 = one turn
    function [17:0] atan_rom;
        input [4:0] i;
        begin
            case (i)
                5'd0:  atan_rom = 18'd32768;  5'd1:  atan_rom = 18'd19344;
                5'd2:  atan_rom = 18'd10221;  5'd3:  atan_rom = 18'd5188;
                5'd4:  atan_rom = 18'd2604;   5'd5:  atan_rom = 18'd1303;
                5'd6:  atan_rom = 18'd652;    5'd7:  atan_rom = 18'd326;
                5'd8:  atan_rom = 18'd163;    5'd9:  atan_rom = 18'd81;
                5'd10: atan_rom = 18'd41;     5'd11: atan_rom = 18'd20;
                5'd12: atan_rom = 18'd10;     5'd13: atan_rom = 18'd5;
                5'd14: atan_rom = 18'd3;      5'd15: atan_rom = 18'd1;
                5'd16: atan_rom = 18'd1;      default: atan_rom = 18'd0;
            endcase
        end
    endfunction

    // saturate a 24-bit signed value to 18 bits (CORDIC input range)
    function signed [19:0] sat18;
        input signed [23:0] v;
        begin
            if (v > 24'sd131071)       sat18 = 20'sd131071;
            else if (v < -24'sd131071) sat18 = -20'sd131071;
            else                       sat18 = v[19:0];
        end
    endfunction

    function signed [19:0] sat20;
        input signed [39:0] v;
        begin
            if (v > 40'sd524287)       sat20 = 20'sd524287;
            else if (v < -40'sd524287) sat20 = -20'sd524287;
            else                       sat20 = v[19:0];
        end
    endfunction

    // ---------------- sine LUT for the 3rd-harmonic correction ----------------
    wire [7:0] h3_idx = th_m[15:8] + h3_ph;          // 4*theta + phase, 1/256 turn
    wire signed [7:0] h3_sin;
    r1_sinlut u_lut (.idx(h3_idx), .val(h3_sin));

    // ---------------- multiplier operand mux ----------------
    always @(*) begin
        mul_a = 20'sd0;
        mul_b = 17'sd0;
        case (st)
            S_M1: begin mul_a = {{7{ds[12]}}, ds}; mul_b = {1'b0, gain}; end
            S_M2: begin mul_a = {{7{dc[12]}}, dc}; mul_b = {ph_sin[15], ph_sin}; end
            S_M3: begin mul_a = dd;                mul_b = {1'b0, ph_icos}; end
            S_P1: begin mul_a = cx;                mul_b = 17'sd19898; end   // 1/K, Q0.15
            S_P2: begin mul_a = {{12{h3_sin[7]}}, h3_sin}; mul_b = {9'd0, h3_amp}; end
            S_L2: begin mul_a = sat20({{8{omega[31]}}, omega} >>> 12); mul_b = {9'd0, extrap}; end
            default: ;
        endcase
    end

    // derived values
    wire signed [11:0] s12 = {~sin_code[11], sin_code[10:0]};
    wire signed [11:0] c12 = {~cos_code[11], cos_code[10:0]};
    wire signed [36:0] p_sh10 = prod >>> 10;
    wire signed [36:0] p_sh11 = prod >>> 11;
    wire signed [36:0] p_sh14 = prod >>> 14;
    wire signed [21:0] d_full = sg - $signed(p_sh11[21:0]);
    wire signed [21:0] y4 = (p_sh14 > 37'sd2097151) ? 22'sd2097151 :
                            (p_sh14 < -37'sd2097151) ? -22'sd2097151 : p_sh14[21:0];
    wire signed [21:0] x4 = {{5{dc[12]}}, dc, 4'b0};
    wire signed [23:0] x4w = {{2{x4[21]}}, x4};
    wire signed [23:0] y4w = {{2{y4[21]}}, y4};
    wire signed [19:0] x5 = sat18(x4w <<< 1);
    wire signed [19:0] y5 = sat18(y4w <<< 1);
    wire signed [19:0] cx_sh = cx >>> it;
    wire signed [19:0] cy_sh = cy >>> it;
    wire [36:0] amp_full = prod >>> 20;                                   // ADC LSB
    wire signed [36:0] h3_corr = prod >>> 5;                              // 18-bit angle units
    wire [17:0] th_c = cz - h3_corr[17:0];
    wire signed [17:0] e18 = th_m - snap_b;                                // wrap to signed
    wire signed [39:0] e_sc = {{22{e18[17]}}, e18} <<< 18;                // 2^-20 LSB16
    wire signed [39:0] kp_term = e_sc >>> kp_sh;
    wire signed [39:0] ki_term = e_sc >>> ki_sh;
    wire [17:0] abs_e = e18[17] ? -e18 : e18;
    wire        amp_bad = (amplitude[11:4] < amp_lo);
    wire        snap    = (abs_e > 18'd32768);
    wire signed [39:0] corr = amp_bad ? 40'sd0 : snap ? e_sc : kp_term;

    // ---------------- sequencer ----------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= S_IDLE; it <= 5'd0;
            ds <= 13'sd0; dc <= 13'sd0; sg <= 21'sd0; dd <= 20'sd0;
            cx <= 20'sd0; cy <= 20'sd0; cz <= 18'd0; th_m <= 18'd0;
            snap_a <= 18'd0; snap_b <= 18'd0; sh_pend <= 1'b0;
            theta <= 36'sd0; omega <= 32'sd0; ext <= 28'sd0;
            amplitude <= 12'd0; raw_sin <= 12'h800; raw_cos <= 12'h800;
            meas_angle <= 18'd0; meas_stb <= 1'b0;
            amp_low <= 1'b0; amp_high <= 1'b0; track_err <= 1'b0; overrun <= 1'b0;
            lo_cnt <= 2'd0; hi_cnt <= 2'd0; lock_cnt <= 5'd0; pos_valid <= 1'b0;
        end else begin
            meas_stb <= 1'b0;
            overrun  <= 1'b0;
            // snapshot of the NCO at the hold instant; a snapshot taken while the
            // previous pair is still in process receives that pair's loop correction
            // in S_L1, so each pair is compared with an estimate that includes all
            // earlier corrections (no one-pair loop delay)
            if (smp_sh) begin
                snap_a  <= theta[35:18] + ((st == S_L1) ? corr[35:18] : 18'd0);
                sh_pend <= (st != S_L1);
            end else if (st == S_L1 && sh_pend) begin
                snap_a  <= snap_a + corr[35:18];
                sh_pend <= 1'b0;
            end
            // NCO: every tick; the loop correction is added in S_L1
            if (st == S_L1)
                theta <= theta + {{4{omega[31]}}, omega} + corr[35:0];
            else
                theta <= theta + {{4{omega[31]}}, omega};

            case (st)
                S_IDLE: if (smp_valid) begin
                    ds <= {s12[11], s12} - {ofs_sin[11], ofs_sin};
                    dc <= {c12[11], c12} - {ofs_cos[11], ofs_cos};
                    raw_sin <= sin_code; raw_cos <= cos_code;
                    snap_b <= smp_sh ? theta[35:18] : snap_a;
                    if (!smp_sh) sh_pend <= 1'b0;
                    st <= S_M1;
                end
                S_M1: begin sg <= p_sh10[20:0]; st <= S_M2; end
                S_M2: begin
                    dd <= (d_full > 22'sd524287) ? 20'sd524287 :
                          (d_full < -22'sd524287) ? -20'sd524287 : d_full[19:0];
                    st <= S_M3;
                end
                S_M3: begin
                    // quadrant pre-rotation so the vectoring converges from any angle
                    if (x5 < 0) begin
                        if (y5 >= 0) begin cx <= y5;  cy <= -x5; cz <= 18'h10000; end
                        else         begin cx <= -y5; cy <= x5;  cz <= 18'h30000; end
                    end else begin
                        cx <= x5; cy <= y5; cz <= 18'h00000;
                    end
                    it <= 5'd0;
                    st <= S_CI;
                end
                S_CI: begin
                    if (!cy[19]) begin
                        cx <= cx + cy_sh; cy <= cy - cx_sh; cz <= cz + atan_rom(it);
                    end else begin
                        cx <= cx - cy_sh; cy <= cy + cx_sh; cz <= cz - atan_rom(it);
                    end
                    it <= it + 5'd1;
                    if (it == 5'd17) st <= S_P1;
                end
                S_P1: begin
                    amplitude <= (amp_full > 37'd4095) ? 12'hFFF : amp_full[11:0];
                    th_m <= cz;                    // LUT index uses cz via th_m next cycle
                    st <= S_P2;
                end
                S_P2: begin
                    th_m <= th_c;
                    meas_angle <= th_c;
                    meas_stb <= 1'b1;
                    st <= S_L1;
                end
                S_L1: begin
                    // acquisition aids: while the amplitude is too low the loop holds
                    // with zero velocity (no integrator run-away on noise); when
                    // |e| > 45 deg the angle snaps to the measurement (gain 1) and the
                    // integrator keeps its normal update
                    if (amp_bad) omega <= 32'sd0;
                    else         omega <= omega + ki_term[31:0];
                    track_err <= (abs_e > 18'd32768);
                    // amplitude flags: 4 consecutive samples
                    if (amplitude[11:4] < amp_lo) begin
                        if (lo_cnt != 2'd3) lo_cnt <= lo_cnt + 2'd1; else amp_low <= 1'b1;
                    end else begin lo_cnt <= 2'd0; amp_low <= 1'b0; end
                    if (amplitude[11:4] > amp_hi) begin
                        if (hi_cnt != 2'd3) hi_cnt <= hi_cnt + 2'd1; else amp_high <= 1'b1;
                    end else begin hi_cnt <= 2'd0; amp_high <= 1'b0; end
                    // lock: 16 consecutive samples with |e| < 11.25 deg and amplitude in range
                    if ((abs_e > 18'd8192) || amp_low || amp_high) begin
                        lock_cnt <= 5'd0; pos_valid <= 1'b0;
                    end else if (lock_cnt != 5'd16) lock_cnt <= lock_cnt + 5'd1;
                    else pos_valid <= 1'b1;
                    st <= S_L2;
                end
                S_L2: begin
                    ext <= prod[27:0];
                    st <= S_IDLE;
                end
                default: st <= S_IDLE;
            endcase
            if (smp_valid && st != S_IDLE) overrun <= 1'b1;
        end
    end

    // ---------------- output stage: extrapolated position, turns ----------------
    wire [23:0] p24  = theta[35:12] + ext[23:0];
    wire [17:0] p18  = p24[23:6];
    wire [17:0] p18d = dir ? (18'd0 - p18) : p18;
    wire [17:0] pnew = p18d - {zero_ofs, 2'b00};
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pos_out <= 18'd0;
            turns   <= 16'd0;
        end else begin
            pos_out <= pnew;
            if (pos_out[17:16] == 2'b11 && pnew[17:16] == 2'b00) turns <= turns + 16'd1;
            else if (pos_out[17:16] == 2'b00 && pnew[17:16] == 2'b11) turns <= turns - 16'd1;
        end
    end

    // velocity, 2^-5 LSB16 per tick, saturated; sign follows dir
    wire signed [31:0] w15 = omega >>> 15;
    wire signed [15:0] w16 = (w15 > 32'sd32767) ? 16'sd32767 :
                             (w15 < -32'sd32767) ? -16'sd32767 : w15[15:0];
    assign velocity = dir ? -w16 : w16;
    wire [15:0] abs_v = w16[15] ? -w16 : w16;
    assign overspeed = (abs_v > ovs_lim);
endmodule
