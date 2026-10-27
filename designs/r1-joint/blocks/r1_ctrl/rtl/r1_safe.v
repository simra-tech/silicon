// R1_CTRL / r1_safe digital part: fault sources, latch, clear rule, I2t winding
// model, T2F temperature counter, bus watchdog.
//
// Sources (FAULT bit): 0..3 comparator flags cmp[3:0] (analog r1_safe window
// comparators, INTERFACES.md order: OC_A, NEG_A, OC_B, NEG_B), 4 over-temperature, 5 amplitude
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
// Revision 0.2: the comparator sources are blanked while cmp_blank is high
// (isense auto-zero window plus recovery, and the calibration search); the
// synchronised flags go to r1_cmpcal; the T2F window counter is 16 bits
// (window <= 2^15 ticks).
// Revision 0.7 (r1_top finding R3): the EN/STO_IN synchroniser u_sen resets to 1, the
// idle (enabled) level of the pad. With reset value 0 the fault latch saw ~en_s = 1 for
// two ticks after the reset release and latched STO with EN high. EN low at power-up
// still latches STO (en_s falls two ticks after the release). The combinational
// gate-off path from the pad (r1_gate) does not use en_s. Reset value of every
// synchroniser = idle level of its source: README revision 0.7, synchroniser table.
// SPDX-License-Identifier: Apache-2.0

module r1_safe (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [3:0]  cmp,            // comparator flags (asynchronous)
    input  wire        cmp_blank,      // comparator outputs not valid (AZ, recovery, calibration)
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
    input  wire [13:0] ot_lim,
    input  wire [3:0]  t2f_win,        // gate window 2^T2F_WIN ticks (minimum 2^8)
    input  wire [3:0]  tau_sh,
    input  wire [3:0]  i2t_pre,
    input  wire [3:0]  cmp_filt,       // comparator filter, consecutive ticks
    input  wire [15:0] i2t_lim,
    input  wire [11:0] i_zero,
    // outputs
    output reg  [12:0] cause,
    output wire        fault,
    output reg  [13:0] temp,          // T2F edges per window (<= 2^13 at f_t2f <= f_clk/4)
    output wire [15:0] e_a_hi, e_b_hi,
    output wire        en_s,
    output wire [3:0]  cmp_sync        // synchronised flags (to r1_cmpcal)
);
    // ---------------- synchronisers ----------------
    wire [3:0] cmp_s;
    r1_sync2 #(.W(4)) u_scmp (.clk(clk), .rst_n(rst_n), .d(cmp), .q(cmp_s));
    assign cmp_sync = cmp_s;
    wire [3:0] cmp_v = cmp_s & {4{~cmp_blank}};
    r1_sync2 #(.W(1), .RST_VAL(1)) u_sen  (.clk(clk), .rst_n(rst_n), .d(en_pad), .q(en_s));
    wire t2f_s;
    r1_sync2 #(.W(1)) u_st2f (.clk(clk), .rst_n(rst_n), .d(t2f_clk), .q(t2f_s));

    // comparator filter: active after cmp_filt+1 consecutive high ticks
    reg [3:0] fc0, fc1, fc2, fc3;
    reg [3:0] cmp_act;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fc0 <= 4'd0; fc1 <= 4'd0; fc2 <= 4'd0; fc3 <= 4'd0; cmp_act <= 4'd0;
        end else begin
            fc0 <= cmp_v[0] ? ((fc0 == 4'hF) ? fc0 : fc0 + 4'd1) : 4'd0;
            fc1 <= cmp_v[1] ? ((fc1 == 4'hF) ? fc1 : fc1 + 4'd1) : 4'd0;
            fc2 <= cmp_v[2] ? ((fc2 == 4'hF) ? fc2 : fc2 + 4'd1) : 4'd0;
            fc3 <= cmp_v[3] ? ((fc3 == 4'hF) ? fc3 : fc3 + 4'd1) : 4'd0;
            cmp_act[0] <= cmp_v[0] && (fc0 >= cmp_filt);
            cmp_act[1] <= cmp_v[1] && (fc1 >= cmp_filt);
            cmp_act[2] <= cmp_v[2] && (fc2 >= cmp_filt);
            cmp_act[3] <= cmp_v[3] && (fc3 >= cmp_filt);
        end
    end

    // ---------------- T2F counter ----------------
    // window (revision 0.2): free-running 16-bit counter, the window ends when
    // its low T2F_WIN bits are all 1 (no compare against a variable limit)
    reg        t2f_d;
    reg [13:0] t2f_cnt;
    reg [15:0] win_cnt;
    wire [3:0] wsh = (t2f_win < 4'd8) ? 4'd8 : t2f_win;
    wire [15:0] wmask = (16'd1 << wsh) - 16'd1;
    wire       win_end = ((win_cnt & wmask) == wmask);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t2f_d <= 1'b0; t2f_cnt <= 14'd0; win_cnt <= 16'd0; temp <= 14'd0;
        end else begin
            t2f_d <= t2f_s;
            win_cnt <= win_cnt + 16'd1;
            if (win_end) begin
                temp    <= t2f_cnt;
                t2f_cnt <= {13'd0, t2f_s & ~t2f_d};
            end else begin
                if (t2f_s & ~t2f_d && t2f_cnt != 14'h3FFF) t2f_cnt <= t2f_cnt + 14'd1;
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
    wire [15:0] pmask = (16'd1 << i2t_pre) - 16'd1;
    reg [1:0]  i2t_ph;
    // one shared |I - I_ZERO| path (revision 0.2), channel selected first
    wire [11:0] i_sel = (i2t_ph == 2'd1) ? i_a : i_b;
    wire [12:0] dsel = {1'b0, i_sel} - {1'b0, i_zero};
    wire [11:0] asel = dsel[12] ? -dsel[11:0] : dsel[11:0];
    wire [7:0]  m_in = asel[11:4];
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
                // every 2^PRESCALE PWM periods: free-running period counter, update
                // when its low PRESCALE bits are all 1 (revision 0.2, no variable compare)
                2'd0: if (pwm_wrap) begin
                    pre_cnt <= pre_cnt + 16'd1;
                    if ((pre_cnt & pmask) == pmask) i2t_ph <= 2'd1;
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
