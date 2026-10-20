// R1_CTRL / r1_gate logic (revision 0.2): PWM counter, three low-side gate
// channels with dead time, the current-pair sample strobe, the isense
// auto-zero window, and the scheduler that shares the single SAR ADC
// (INTERFACES.md: slice A = SIN or ISA, slice B = COS or ISB; {SIN, COS} pairs
// on adc_hold, {ISA, ISB} pairs on is_smp; per conversion 13 raw decisions,
// corrected by r1_adcw).
//
// PWM: up-counter 0..PERIOD-1 (f_PWM = f_clk / PERIOD). Channel x is on while
//   DEAD <= rel_x < DUTY_x - DEAD,  rel_x = (cnt - PHASE_x) mod PERIOD,
// i.e. the ideal on-window [PHASE_x, PHASE_x + DUTY_x) shrunk by DEAD at both
// edges. DUTY/PHASE/PERIOD are shadowed and take effect at the counter wrap.
// Current strobe (0.2): one strobe per period at the centre of the channel A
// window, when the shrunk window is at least 2 ticks long. Both isense outputs
// are sampled together (r1_adc samples ISA and ISB on one trk_cur edge), so
// channel B is sampled at the channel A centre; for a centred PWM pattern
// (PHASE_x = C - DUTY_x / 2) all windows share that centre.
// Auto-zero window: az_win is high for AZ_LEN ticks from cnt == AZ_START
// (AZ_LEN = 0: no window). The host places it where both low-side FETs are off.
// Scheduler: a sin/cos pair (hold, convert SIN, convert COS) starts every
// PAIR_TICKS unless the current strobe is due within GUARD ticks; the current
// pair starts at the strobe tick (or as soon as the ADC is free; late starts
// are counted). A conversion of channel n+1 starts at the adc_valid of channel n;
// the corrected code arrives 8 ticks after adc_valid. A new sin/cos pair does
// not start while the COS code of the previous pair is still in r1_adcw
// (sc_pend): r1_pos keeps one NCO snapshot per pair (taken at smp_sh), so
// smp_valid of pair n must come before smp_sh of pair n+1. The sin/cos pair
// period is therefore max(PAIR_TICKS, 2 conversions + 9 ticks).
// Gate outputs: registered PWM AND gate_ok (registered) AND the EN/STO_IN pad
// level (asynchronous, so EN low forces the gates low at once).
// SPDX-License-Identifier: Apache-2.0

module r1_gate (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [15:0]  period,
    input  wire [15:0]  duty_a, duty_b, duty_c,
    input  wire [15:0]  phase_a, phase_b, phase_c,
    input  wire [7:0]   dead,
    input  wire [7:0]   pair_ticks,
    input  wire [7:0]   guard,
    input  wire [15:0]  az_start,
    input  wire [7:0]   az_len,
    input  wire         gate_ok,        // clk domain: enabled and no fault
    input  wire         en_pad,         // EN/STO_IN pad level (asynchronous)
    output wire         gate_a, gate_b, gate_c,
    output reg          pwm_wrap,       // pulse at the start of each PWM period
    output reg          az_win,
    // ADC
    output reg          adc_hold,       // sin/cos track-and-holds hold while high
    output reg          is_smp,         // isense track-and-holds hold while high
    output reg          adc_start,      // pulse: start a conversion of adc_mux
    output reg  [1:0]   adc_mux,        // 0 SIN, 1 COS, 2 ISA, 3 ISB
    input  wire         adc_valid,      // pulse: adc_raw valid
    input  wire [12:0]  adc_raw,
    input  wire [181:0] adc_w,
    // results
    output reg          smp_sh,         // pulse at the hold instant
    output reg          smp_valid,
    output reg  [11:0]  sin_code,       // both updated together when the pair is complete
    output reg  [11:0]  cos_code,
    output reg  [11:0]  i_a, i_b,
    output reg  [3:0]   late_cnt        // saturating
);
    // ---------------- PWM ----------------
    reg  [15:0] cnt;
    wire [15:0] p_s, da_s, db_s, dc_s, pa_s, pb_s, pc_s;
    reg         pwm_a, pwm_b, pwm_c;
    wire        wrap = (cnt + 16'd1 >= p_s);

    function [15:0] rel;               // (c - p) mod per: one subtraction, add per on borrow
        input [15:0] c, p, per;
        reg [16:0] t;
        begin t = {1'b0, c} - {1'b0, p}; rel = t[16] ? (t[15:0] + per) : t[15:0]; end
    endfunction
    function on_win;                   // dt <= r < d - dt
        input [15:0] r, d; input [7:0] dt;
        reg [16:0] e;
        begin e = {1'b0, d} - {9'd0, dt}; on_win = (r >= {8'd0, dt}) && !e[16] && (r < e[15:0]); end
    endfunction
    function [15:0] centre;            // (ph + d/2) mod per
        input [15:0] ph, d, per;
        reg [16:0] t;
        begin t = {1'b0, ph} + {2'b0, d[15:1]}; centre = (t >= {1'b0, per}) ? (t[15:0] - per) : t[15:0]; end
    endfunction

    wire [15:0] ra = rel(cnt, pa_s, p_s);
    wire [15:0] rb = rel(cnt, pb_s, p_s);
    wire [15:0] rc = rel(cnt, pc_s, p_s);
    wire [16:0] min_d = {8'd0, dead, 1'b0} + 17'd2;
    reg  [7:0]  az_cnt;

    // shadow registers (revision 0.2: latch words): loaded in the tick of the
    // counter wrap (and continuously while PERIOD = 0), i.e. at the same clock
    // edge that sets cnt to 0, as the flip-flops of revision 0.1 did
    wire ld = (p_s == 16'd0) || wrap;
    wire g_sh;
    r1_cgate u_cgs (.clk(clk), .en(ld), .gclk(g_sh));
    r1_creg #(.W(16)) u_ps (.rst_n(rst_n), .gclk(g_sh), .d(period),  .q(p_s));
    r1_creg #(.W(16)) u_da (.rst_n(rst_n), .gclk(g_sh), .d(duty_a),  .q(da_s));
    r1_creg #(.W(16)) u_db (.rst_n(rst_n), .gclk(g_sh), .d(duty_b),  .q(db_s));
    r1_creg #(.W(16)) u_dc (.rst_n(rst_n), .gclk(g_sh), .d(duty_c),  .q(dc_s));
    r1_creg #(.W(16)) u_pa (.rst_n(rst_n), .gclk(g_sh), .d(phase_a), .q(pa_s));
    r1_creg #(.W(16)) u_pb (.rst_n(rst_n), .gclk(g_sh), .d(phase_b), .q(pb_s));
    r1_creg #(.W(16)) u_pc (.rst_n(rst_n), .gclk(g_sh), .d(phase_c), .q(pc_s));
    // strobe tick and valid, from the shadowed values (revision 0.2 after the
    // first hardening trial: a 17-bit shadow latch loaded from the unshadowed
    // words gave a latch-to-latch path with half a clock period, -3.3 ns at
    // 42 MHz; computed here it is a full-cycle path to the scheduler flops)
    wire [15:0] sa = centre(pa_s, da_s, p_s);
    wire        va = ({1'b0, da_s} >= min_d) && (pa_s < p_s) && (da_s <= p_s);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 16'd0; pwm_a <= 1'b0; pwm_b <= 1'b0; pwm_c <= 1'b0; pwm_wrap <= 1'b0;
            az_cnt <= 8'd0; az_win <= 1'b0;
        end else begin
            pwm_wrap <= 1'b0;
            if (ld) begin
                cnt  <= 16'd0;
                pwm_wrap <= (period != 16'd0);
            end else begin
                cnt <= cnt + 16'd1;
            end
            pwm_a <= (p_s != 16'd0) && on_win(ra, da_s, dead);
            pwm_b <= (p_s != 16'd0) && on_win(rb, db_s, dead);
            pwm_c <= (p_s != 16'd0) && on_win(rc, dc_s, dead);
            // auto-zero window (same counter value as the PWM decision)
            if (p_s != 16'd0 && cnt == az_start && az_len != 8'd0) az_cnt <= az_len;
            else if (az_cnt != 8'd0)                               az_cnt <= az_cnt - 8'd1;
            az_win <= (p_s != 16'd0 && cnt == az_start && az_len != 8'd0) || (az_cnt > 8'd1);
        end
    end
    assign gate_a = pwm_a & gate_ok & en_pad;
    assign gate_b = pwm_b & gate_ok & en_pad;
    assign gate_c = pwm_c & gate_ok & en_pad;

    // strobe and guard (the strobe tick is compared with the counter value that
    // pwm_x is computed from, so the strobe sits at the window centre)
    wire stb  = va && (p_s != 16'd0) && (cnt == sa);
    wire [15:0] ta = rel(sa, cnt, p_s);          // ticks until the strobe
    wire soon = va && (p_s != 16'd0) && ta <= {8'd0, guard};

    // ---------------- ADC weight correction ----------------
    wire        cv;
    wire [11:0] code;
    r1_adcw u_w (.clk(clk), .rst_n(rst_n), .valid(adc_valid), .raw(adc_raw), .w(adc_w),
                 .code_valid(cv), .code(code));

    // ---------------- ADC scheduler ----------------
    localparam A_IDLE = 2'd0, A_FIRST = 2'd1, A_SECOND = 2'd2;
    reg [1:0]  ast;
    reg [7:0]  ptim;
    reg        req;
    reg [1:0]  tag;                    // channel of the conversion in r1_adcw
    reg [11:0] first_code;             // SIN or ISA code until its pair partner is done
    reg        sc_pend;                // COS code of a sin/cos pair not yet out of r1_adcw

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ast <= A_IDLE; ptim <= 8'd0; req <= 1'b0; tag <= 2'd0; first_code <= 12'h800; sc_pend <= 1'b0;
            adc_hold <= 1'b0; is_smp <= 1'b0; adc_start <= 1'b0; adc_mux <= 2'd0;
            smp_sh <= 1'b0; smp_valid <= 1'b0; sin_code <= 12'h800; cos_code <= 12'h800;
            i_a <= 12'd0; i_b <= 12'd0; late_cnt <= 4'd0;
        end else begin
            adc_start <= 1'b0; smp_sh <= 1'b0; smp_valid <= 1'b0;
            if (ptim != 8'hFF) ptim <= ptim + 8'd1;
            if (stb) req <= 1'b1;
            case (ast)
                A_IDLE: begin
                    if (req || stb) begin
                        is_smp <= 1'b1; adc_mux <= 2'd2; adc_start <= 1'b1; req <= 1'b0; ast <= A_FIRST;
                        if (!stb && late_cnt != 4'hF) late_cnt <= late_cnt + 4'd1;
                    end else if (ptim + 8'd1 >= pair_ticks && !soon && pair_ticks != 8'd0 && !sc_pend) begin
                        ptim <= 8'd0;
                        adc_hold <= 1'b1; smp_sh <= 1'b1;
                        adc_mux <= 2'd0; adc_start <= 1'b1; ast <= A_FIRST;
                    end
                end
                A_FIRST: if (adc_valid) begin
                    tag <= adc_mux; adc_mux <= adc_mux + 2'd1; adc_start <= 1'b1; ast <= A_SECOND;
                end
                A_SECOND: if (adc_valid) begin
                    tag <= adc_mux; adc_hold <= 1'b0; is_smp <= 1'b0; ast <= A_IDLE;
                    if (adc_mux == 2'd1) sc_pend <= 1'b1;
                end
                default: ast <= A_IDLE;
            endcase
            // corrected codes
            if (cv) case (tag)
                2'd0: first_code <= code;
                2'd1: begin sin_code <= first_code; cos_code <= code; smp_valid <= 1'b1; sc_pend <= 1'b0; end
                2'd2: first_code <= code;
                default: begin i_a <= first_code; i_b <= code; end
            endcase
        end
    end
endmodule
