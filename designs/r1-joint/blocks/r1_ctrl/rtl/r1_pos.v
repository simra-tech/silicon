// R1_CTRL / r1_pos: encoder position path.
//   sin/cos pair (12-bit offset-binary codes) -> offset, gain-ratio and phase
//   correction (Heydemann form) -> iterative CORDIC vectoring (18 iterations, 2 per tick,
//   18-bit x/y, 18-bit angle) -> 3rd-harmonic angle correction -> type-II
//   tracking loop running as an NCO on every clk tick -> extrapolated
//   position, turn counter, velocity, amplitude and flags.
// One 18 x 17 signed multiplier is shared by all steps, including (revision
// 0.2) the loop gains 2^-KP and 2^-KI, which revision 0.1 formed with two
// 40-bit barrel shifters. Revision 0.3 (D18): two CORDIC iterations per tick,
// a pair is processed in 19 clk cycles after smp_valid; the frame generator
// (r1_gate) spaces pairs by PAIR_TICKS (default 22) and starts a pair not
// before smp_valid of the previous pair (one NCO snapshot; smp_sh in the tick
// of smp_valid belongs to the next pair). A pair that arrives while busy is dropped and flagged
// (overrun).
// Revision 0.2 trims: the correction intermediates (offset-corrected samples,
// sine * gain, phase-corrected sine) are held in the CORDIC x/y registers; the
// raw codes are read from r1_gate (no copy here); meas_angle is the corrected
// angle register itself; KI is limited to 8..23 (values outside are clamped);
// the CORDIC datapath is 18 bits with 4 fractional bits (revision 0.1: 20 bits,
// 5 fractional bits), inputs saturated at +-49151 so that the CORDIC gain
// (2.33 x with the diagonal) stays inside 18 bits.
// Revision 0.8 (PLAN.md D22): per-channel gain. The cosine channel is multiplied by
// COS_GAIN (Q2.14) in the IDLE tick in which the pair is accepted (the shared
// multiplier is free there), so the pair latency is unchanged (19 ticks); GAIN is
// now SIN_GAIN (the sine channel gain, Q2.14, same arithmetic as before). Both
// channels: code' = sat((code - OFS) * GAIN), 4 fractional bits, +-131071, then the
// CORDIC input limit +-49151. With COS_GAIN = 1.0 (0x4000) the result is
// bit-identical to revision 0.7.
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
    input  wire [15:0] gain,            // Q2.14, SIN_GAIN, multiplies the sine channel
    input  wire [15:0] cos_gain,        // 0.8: Q2.14, COS_GAIN, multiplies the cosine channel
    input  wire [15:0] ph_sin,          // Q1.15 signed, sin(alpha)
    input  wire [15:0] ph_icos,         // Q2.14, 1/cos(alpha)
    input  wire [7:0]  h3_amp,          // 16-bit angle LSB
    input  wire [7:0]  h3_ph,           // 1/256 turn
    input  wire [15:0] zero_ofs,        // 16-bit angle LSB
    input  wire        dir,
    input  wire [3:0]  kp_sh,           // loop proportional gain 2^-kp
    input  wire [4:0]  ki_sh,           // loop integral gain 2^-ki per tick (8..23)
    input  wire [7:0]  extrap,          // extrapolation, clk ticks
    input  wire [7:0]  amp_lo,          // amplitude thresholds, 16 ADC LSB units
    input  wire [7:0]  amp_hi,
    input  wire [15:0] ovs_lim,         // |velocity| limit, VELOCITY units
    // outputs
    output reg  [17:0] pos_out,         // 16.2 bit angle, extrapolated, after zero/dir
    output reg  [15:0] turns,
    output wire [15:0] velocity,        // signed, 2^-5 LSB16 per tick
    output reg  [11:0] amplitude,       // ADC LSB
    output wire [17:0] meas_angle,      // corrected measured angle of the last pair (18 bit)
    output reg         meas_stb,        // pulse when meas_angle updates
    output reg         amp_low,
    output reg         amp_high,
    output wire        overspeed,
    output reg         track_err,
    output reg         overrun,         // pulse
    output reg         pos_valid
);
    // ---------------- shared multiplier ----------------
    reg  signed [17:0] mul_a;
    reg  signed [16:0] mul_b;
    wire signed [34:0] prod = mul_a * mul_b;

    // ---------------- state ----------------
    localparam S_IDLE = 4'd0, S_M1 = 4'd1, S_M2 = 4'd2, S_M3 = 4'd3, S_C0 = 4'd4,
               S_CI = 4'd5, S_P1 = 4'd6, S_P2 = 4'd7, S_L1 = 4'd8, S_L2 = 4'd9, S_L3 = 4'd10;
    reg [3:0]  st;
    reg [4:0]  it;

    // cx, cy also hold the correction intermediates:
    //   IDLE -> M1: cx = sine - offset (ADC LSB), cy = (cosine - offset) * COS_GAIN (4 fractional bits, 0.8)
    //   M1 -> M2:   cx = sine * gain (4 fractional bits)
    //   M2 -> M3:   cx = cx - cy * sin(alpha), saturated
    reg signed [17:0] cx, cy;           // CORDIC x, y (4 fractional bits)
    reg        [17:0] cz;               // CORDIC angle, 2^18 = one turn
    reg        [17:0] th_m;             // corrected measured angle
    reg        [17:0] snap_a, snap_b;   // NCO angle at the track-and-hold instant
    reg signed [35:0] theta;            // NCO angle, 16.20 (wraps)
    reg signed [31:0] omega;            // 2^-20 LSB16 per tick
    reg signed [23:0] ext;              // omega * extrap, 2^-8 LSB16
    reg [1:0]  lo_cnt, hi_cnt;
    reg [4:0]  lock_cnt;
    reg        sh_pend;
    assign meas_angle = th_m;

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

    // CORDIC input range (the gain 1.647 x sqrt(2) keeps 49151 inside 18 bits)
    function signed [17:0] satin;
        input signed [21:0] v;
        begin
            if (v > 22'sd49151)       satin = 18'sd49151;
            else if (v < -22'sd49151) satin = -18'sd49151;
            else                      satin = v[17:0];
        end
    endfunction

    function signed [17:0] sat18;
        input signed [34:0] v;
        begin
            if (v > 35'sd131071)       sat18 = 18'sd131071;
            else if (v < -35'sd131071) sat18 = -18'sd131071;
            else                       sat18 = v[17:0];
        end
    endfunction

    // ---------------- sine LUT for the 3rd-harmonic correction ----------------
    wire [7:0] h3_idx = cz[15:8] + h3_ph;            // 4*theta + phase, 1/256 turn
    wire signed [7:0] h3_sin;
    r1_sinlut u_lut (.idx(h3_idx), .val(h3_sin));

    // ---------------- loop error and gains ----------------
    wire signed [17:0] e18 = th_m - snap_b;                                // wrap to signed
    wire [17:0] abs_e = e18[17] ? -e18 : e18;
    wire        amp_bad = (amplitude[11:4] < amp_lo);
    wire        snap    = (abs_e > 18'd32768);
    // KP: corr = e * 2^(18 - KP) = (e * 2^(15 - KP)) << 3; snap: KP = 0; amp_bad: 0
    wire [3:0]  kp_eff  = snap ? 4'd0 : kp_sh;
    wire [16:0] kp_mul  = amp_bad ? 17'd0 : (17'd1 << (4'd15 - kp_eff));
    // KI: ki_term = e * 2^(18 - KI) = (e * 2^(23 - KI)) >>> 5, KI clamped to 8..23
    wire [4:0]  ki_eff  = (ki_sh < 5'd8) ? 5'd8 : (ki_sh > 5'd23) ? 5'd23 : ki_sh;
    wire [16:0] ki_mul  = 17'd1 << (5'd23 - ki_eff);

    // offset-corrected codes (ADC LSB)
    wire signed [11:0] s12 = {~sin_code[11], sin_code[10:0]};
    wire signed [11:0] c12 = {~cos_code[11], cos_code[10:0]};
    wire signed [12:0] ds_n = {s12[11], s12} - {ofs_sin[11], ofs_sin};
    wire signed [12:0] dc_n = {c12[11], c12} - {ofs_cos[11], ofs_cos};

    // ---------------- multiplier operand mux ----------------
    always @(*) begin
        mul_a = 20'sd0;
        mul_b = 17'sd0;
        case (st)
            S_IDLE: begin mul_a = {{5{dc_n[12]}}, dc_n}; mul_b = {1'b0, cos_gain}; end   // 0.8 (D22)
            S_M1: begin mul_a = cx;                mul_b = {1'b0, gain}; end
            S_M2: begin mul_a = cy;                mul_b = {ph_sin[15], ph_sin}; end
            S_M3: begin mul_a = cx;                mul_b = {1'b0, ph_icos}; end
            S_P1: begin mul_a = cx;                mul_b = 17'sd19898; end   // 1/K, Q0.15
            S_P2: begin mul_a = {{10{h3_sin[7]}}, h3_sin}; mul_b = {9'd0, h3_amp}; end
            S_L1: begin mul_a = e18;               mul_b = kp_mul; end
            S_L2: begin mul_a = e18;               mul_b = ki_mul; end
            S_L3: begin mul_a = sat18({{3{omega[31]}}, omega} >>> 13); mul_b = {9'd0, extrap}; end
            default: ;
        endcase
    end

    // derived values
    wire signed [34:0] p_sh10 = prod >>> 10;
    wire signed [34:0] p_sh15 = prod >>> 15;           // 0.8: cy has 4 fractional bits (0.7: cy in LSB, >>> 11)
    wire signed [34:0] p_sh14 = prod >>> 14;
    wire signed [21:0] d_full = {{4{cx[17]}}, cx} - $signed(p_sh15[21:0]);
    wire signed [21:0] y4 = (p_sh14 > 35'sd2097151) ? 22'sd2097151 :
                            (p_sh14 < -35'sd2097151) ? -22'sd2097151 : p_sh14[21:0];
    wire signed [21:0] x4 = {{4{cy[17]}}, cy};          // 0.8: cy = cosine * COS_GAIN, 4 fractional bits
    wire signed [17:0] x5 = satin(x4);
    wire signed [17:0] y5 = satin(y4);
    // Revision 0.3 (D18): two CORDIC iterations per tick (it, it+1), so a pair takes <= 22 ticks.
    wire signed [17:0] cx_sh = cx >>> it;
    wire signed [17:0] cy_sh = cy >>> it;
    wire        cd1 = !cy[17];
    wire signed [17:0] cx1 = cd1 ? cx + cy_sh : cx - cy_sh;
    wire signed [17:0] cy1 = cd1 ? cy - cx_sh : cy + cx_sh;
    wire [17:0] cz1 = cd1 ? cz + atan_rom(it) : cz - atan_rom(it);
    wire [4:0]  it1 = it + 5'd1;
    wire signed [17:0] cx1_sh = cx1 >>> it1;
    wire signed [17:0] cy1_sh = cy1 >>> it1;
    wire        cd2 = !cy1[17];
    wire [34:0] amp_full = prod >>> 19;                                   // ADC LSB
    wire signed [34:0] h3_corr = prod >>> 5;                              // 18-bit angle units
    wire [17:0] th_c = cz - h3_corr[17:0];
    wire signed [35:0] corr = {prod[32:0], 3'b000};                       // 2^-20 LSB16
    wire signed [34:0] ki_full = prod >>> 5;
    wire signed [31:0] ki_term = ki_full[31:0];

    // ---------------- sequencer ----------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= S_IDLE; it <= 5'd0;
            cx <= 18'sd0; cy <= 18'sd0; cz <= 18'd0; th_m <= 18'd0;
            snap_a <= 18'd0; snap_b <= 18'd0; sh_pend <= 1'b0;
            theta <= 36'sd0; omega <= 32'sd0; ext <= 24'sd0;
            amplitude <= 12'd0; meas_stb <= 1'b0;
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
                theta <= theta + {{4{omega[31]}}, omega} + corr;
            else
                theta <= theta + {{4{omega[31]}}, omega};

            case (st)
                S_IDLE: if (smp_valid) begin
                    cx <= {{5{ds_n[12]}}, ds_n};
                    cy <= sat18(p_sh10);                     // 0.8: (cosine - offset) * COS_GAIN
                    snap_b <= snap_a;   // 0.3: a hold in the same tick belongs to the next pair (D18 frame)
                    if (!smp_sh) sh_pend <= 1'b0;
                    st <= S_M1;
                end
                S_M1: begin cx <= sat18(p_sh10); st <= S_M2; end
                S_M2: begin
                    cx <= (d_full > 22'sd131071) ? 18'sd131071 :
                          (d_full < -22'sd131071) ? -18'sd131071 : d_full[17:0];
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
                    cx <= cd2 ? cx1 + cy1_sh : cx1 - cy1_sh;
                    cy <= cd2 ? cy1 - cx1_sh : cy1 + cx1_sh;
                    cz <= cd2 ? cz1 + atan_rom(it1) : cz1 - atan_rom(it1);
                    it <= it + 5'd2;
                    if (it == 5'd16) st <= S_P1;
                end
                S_P1: begin
                    amplitude <= (amp_full > 35'd4095) ? 12'hFFF : amp_full[11:0];
                    st <= S_P2;
                end
                S_P2: begin
                    th_m <= th_c;
                    meas_stb <= 1'b1;
                    st <= S_L1;
                end
                S_L1: begin
                    // acquisition aids: while the amplitude is too low the loop holds
                    // (no correction, zero velocity in S_L2); when |e| > 45 deg the
                    // angle snaps to the measurement (gain 1) and the integrator keeps
                    // its normal update
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
                    if (amp_bad) omega <= 32'sd0;
                    else         omega <= omega + ki_term;
                    st <= S_L3;
                end
                S_L3: begin
                    ext <= {prod[22:0], 1'b0};                   // (omega >>> 13) * 2 * extrap
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
