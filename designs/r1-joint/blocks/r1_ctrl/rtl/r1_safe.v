// R1_CTRL / r1_safe digital part: fault sources, latch, clear rule, I2t winding
// model, T2F temperature counter, bus watchdog.
//
// Sources (FAULT bit): 0..3 comparator flags cmp[3:0] (analog r1_safe window
// comparators: OC_A, OC_B, SHORT_A, SHORT_B), 4 over-temperature, 5 amplitude
// low/high, 6 overspeed, 7 watchdog, 8 EN/STO_IN low, 9 I2T_A, 10 I2T_B,
// 11 calibration invalid (CAL_CRC mismatch), 12 power-on.
// An unmasked active source sets its FAULT bit; any FAULT bit holds FAULT_N low
// and the gates off. CTRL.CLR clears the bits whose source is inactive at that
// moment; bits 8 (EN), 11 (CAL) and 12 (POR) cannot be masked, so a clear only
// releases the gates while the calibration CRC matches.
// I2t (per channel, common parameters): every 2^PRESCALE PWM periods
//   i = |I_x - I_ZERO| >> 4 (8 bit);  E += ((i^2 << 8) - E) >> TAU_SHIFT
// (first-order thermal model, time constant 2^TAU_SHIFT updates); source active
// while E[23:8] >= I2T_LIM.
// SPDX-License-Identifier: Apache-2.0

module r1_safe (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [3:0]  cmp,            // comparator flags (asynchronous)
    input  wire        en_pad,         // EN/STO_IN (asynchronous)
    input  wire        t2f_clk,        // T2F oscillator (asynchronous, < f_clk / 4)
    input  wire        amp_flag,
    input  wire        ovs_flag,
    input  wire        cal_valid,
    input  wire        wdt_kick,
    input  wire        pwm_wrap,
    input  wire [11:0] i_a, i_b,
    // configuration
    input  wire [12:0] mask,
    input  wire        clr,            // pulse
    input  wire        wdt_en,
    input  wire [15:0] wdt_period,     // 1024-tick units
    input  wire [15:0] ot_lim,
    input  wire [3:0]  t2f_win,        // gate window 2^T2F_WIN ticks (minimum 2^8)
    input  wire [3:0]  tau_sh,
    input  wire [3:0]  i2t_pre,
    input  wire [3:0]  cmp_filt,       // comparator filter, consecutive ticks
    input  wire [15:0] i2t_lim,
    input  wire [11:0] i_zero,
    // outputs
    output reg  [12:0] cause,
    output wire        fault,
    output reg  [15:0] temp,
    output wire [15:0] e_a_hi, e_b_hi,
    output wire        en_s
);
    // ---------------- synchronisers ----------------
    wire [3:0] cmp_s;
    r1_sync2 #(.W(4)) u_scmp (.clk(clk), .rst_n(rst_n), .d(cmp), .q(cmp_s));
    r1_sync2 #(.W(1)) u_sen  (.clk(clk), .rst_n(rst_n), .d(en_pad), .q(en_s));
    wire t2f_s;
    r1_sync2 #(.W(1)) u_st2f (.clk(clk), .rst_n(rst_n), .d(t2f_clk), .q(t2f_s));

    // comparator filter: active after cmp_filt+1 consecutive high ticks
    reg [3:0] fc0, fc1, fc2, fc3;
    reg [3:0] cmp_act;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fc0 <= 4'd0; fc1 <= 4'd0; fc2 <= 4'd0; fc3 <= 4'd0; cmp_act <= 4'd0;
        end else begin
            fc0 <= cmp_s[0] ? ((fc0 == 4'hF) ? fc0 : fc0 + 4'd1) : 4'd0;
            fc1 <= cmp_s[1] ? ((fc1 == 4'hF) ? fc1 : fc1 + 4'd1) : 4'd0;
            fc2 <= cmp_s[2] ? ((fc2 == 4'hF) ? fc2 : fc2 + 4'd1) : 4'd0;
            fc3 <= cmp_s[3] ? ((fc3 == 4'hF) ? fc3 : fc3 + 4'd1) : 4'd0;
            cmp_act[0] <= cmp_s[0] && (fc0 >= cmp_filt);
            cmp_act[1] <= cmp_s[1] && (fc1 >= cmp_filt);
            cmp_act[2] <= cmp_s[2] && (fc2 >= cmp_filt);
            cmp_act[3] <= cmp_s[3] && (fc3 >= cmp_filt);
        end
    end

    // ---------------- T2F counter ----------------
    reg        t2f_d;
    reg [15:0] t2f_cnt;
    reg [19:0] win_cnt;
    wire [3:0] wsh = (t2f_win < 4'd8) ? 4'd8 : t2f_win;
    wire       win_end = (win_cnt >= ((20'd1 << wsh) - 20'd1));
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t2f_d <= 1'b0; t2f_cnt <= 16'd0; win_cnt <= 20'd0; temp <= 16'd0;
        end else begin
            t2f_d <= t2f_s;
            if (win_end) begin
                win_cnt <= 20'd0;
                temp    <= t2f_cnt;
                t2f_cnt <= {15'd0, t2f_s & ~t2f_d};
            end else begin
                win_cnt <= win_cnt + 20'd1;
                if (t2f_s & ~t2f_d && t2f_cnt != 16'hFFFF) t2f_cnt <= t2f_cnt + 16'd1;
            end
        end
    end
    wire ot_act = (temp >= ot_lim);

    // ---------------- watchdog ----------------
    reg [25:0] wdt_cnt;
    wire wdt_act = wdt_en && (wdt_cnt[25:10] >= wdt_period);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) wdt_cnt <= 26'd0;
        else if (!wdt_en || wdt_kick) wdt_cnt <= 26'd0;
        else if (!wdt_act) wdt_cnt <= wdt_cnt + 26'd1;
    end

    // ---------------- I2t ----------------
    reg [23:0] e_a, e_b;
    reg [15:0] pre_cnt;
    reg [1:0]  i2t_ph;
    wire [12:0] da = {1'b0, i_a} - {1'b0, i_zero};
    wire [12:0] db = {1'b0, i_b} - {1'b0, i_zero};
    wire [11:0] aa = da[12] ? -da[11:0] : da[11:0];
    wire [11:0] ab = db[12] ? -db[11:0] : db[11:0];
    wire [7:0]  m_in = (i2t_ph == 2'd1) ? aa[11:4] : ab[11:4];
    wire [15:0] sq = m_in * m_in;
    wire [23:0] e_cur = (i2t_ph == 2'd1) ? e_a : e_b;
    wire signed [25:0] diff = $signed({2'b00, sq, 8'd0}) - $signed({2'b00, e_cur});
    wire signed [25:0] step = diff >>> tau_sh;
    wire [25:0] e_new = {2'b00, e_cur} + step;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            e_a <= 24'd0; e_b <= 24'd0; pre_cnt <= 16'd0; i2t_ph <= 2'd0;
        end else begin
            case (i2t_ph)
                2'd0: if (pwm_wrap) begin
                    if (pre_cnt >= ((16'd1 << i2t_pre) - 16'd1)) begin
                        pre_cnt <= 16'd0; i2t_ph <= 2'd1;
                    end else pre_cnt <= pre_cnt + 16'd1;
                end
                2'd1: begin e_a <= e_new[23:0]; i2t_ph <= 2'd2; end
                2'd2: begin e_b <= e_new[23:0]; i2t_ph <= 2'd0; end
                default: i2t_ph <= 2'd0;
            endcase
        end
    end
    assign e_a_hi = e_a[23:8];
    assign e_b_hi = e_b[23:8];
    wire i2t_a_act = (e_a[23:8] >= i2t_lim);
    wire i2t_b_act = (e_b[23:8] >= i2t_lim);

    // ---------------- latch ----------------
    wire [12:0] src = {1'b0, ~cal_valid, i2t_b_act, i2t_a_act, ~en_s, wdt_act,
                       ovs_flag, amp_flag, ot_act, cmp_act};
    wire [12:0] eff_mask = mask & 13'b0_0110_1111_1111;   // EN, CAL, POR not maskable
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) cause <= 13'h1000;                     // POR
        else begin
            if (clr) cause <= (cause & src) | (src & ~eff_mask);
            else     cause <= cause | (src & ~eff_mask);
        end
    end
    assign fault = |cause;
endmodule
