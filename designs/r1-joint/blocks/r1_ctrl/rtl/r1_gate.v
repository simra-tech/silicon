// R1_CTRL / r1_gate logic: PWM counter, three low-side gate channels with dead
// time, centre-of-on-time current sample strobes, and the scheduler that shares
// the single SAR ADC (4:1 mux: SIN, COS track-and-holds, ISA, ISB).
//
// PWM: up-counter 0..PERIOD-1 (f_PWM = f_clk / PERIOD). Channel x is on while
//   DEAD <= rel_x < DUTY_x - DEAD,  rel_x = (cnt - PHASE_x) mod PERIOD,
// i.e. the ideal on-window [PHASE_x, PHASE_x + DUTY_x) shrunk by DEAD at both
// edges (dead time against the complementary high side driven by the
// controller). The window centre stays at PHASE_x + DUTY_x/2. DUTY/PHASE/PERIOD
// are shadowed and take effect at the counter wrap.
// Strobes: channel A and B request a current conversion at the window centre
// when the shrunk window is at least 2 ticks long.
// Scheduler: a sin/cos pair (hold, convert SIN, convert COS) starts every
// PAIR_TICKS unless a current strobe is due within GUARD ticks; current
// conversions start at the strobe tick (or as soon as the ADC is free; late
// starts are counted).
// Gate outputs: registered PWM AND gate_ok (registered, from r1_safe) AND the
// EN/STO_IN pad level (asynchronous, so EN low forces the gates low at once).
// SPDX-License-Identifier: Apache-2.0

module r1_gate (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] period,
    input  wire [15:0] duty_a, duty_b, duty_c,
    input  wire [15:0] phase_a, phase_b, phase_c,
    input  wire [7:0]  dead,
    input  wire [7:0]  pair_ticks,
    input  wire [7:0]  guard,
    input  wire        gate_ok,        // clk domain: enabled and no fault
    input  wire        en_pad,         // EN/STO_IN pad level (asynchronous)
    output wire        gate_a, gate_b, gate_c,
    output reg         pwm_wrap,       // pulse at the start of each PWM period
    // ADC
    output reg         adc_hold,       // sin/cos track-and-holds hold while high
    output reg         adc_start,      // pulse: start a conversion of adc_mux
    output reg  [1:0]  adc_mux,        // 0 SIN, 1 COS, 2 ISA, 3 ISB
    input  wire        adc_done,       // pulse: adc_data valid
    input  wire [11:0] adc_data,
    // results
    output reg         smp_sh,         // pulse at the hold instant
    output reg         smp_valid,
    output reg  [11:0] sin_code,
    output reg  [11:0] cos_code,
    output reg         ia_stb, ib_stb,
    output reg  [11:0] i_a, i_b,
    output reg  [7:0]  late_cnt
);
    // ---------------- PWM ----------------
    reg [15:0] cnt, p_s, da_s, db_s, dc_s, pa_s, pb_s, pc_s;
    reg [15:0] sa, sb;                 // strobe ticks
    reg        va, vb;                 // strobe valid
    reg        pwm_a, pwm_b, pwm_c;
    wire       wrap = (cnt + 16'd1 >= p_s);

    function [15:0] rel;               // (c - p) mod per
        input [15:0] c, p, per;
        begin rel = (c >= p) ? (c - p) : (c + per - p); end
    endfunction
    function on_win;
        input [15:0] r, d; input [7:0] dt;
        begin on_win = (r >= {8'd0, dt}) && ({1'b0, r} + {9'd0, dt} < {1'b0, d}); end
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

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 16'd0; p_s <= 16'd0; da_s <= 16'd0; db_s <= 16'd0; dc_s <= 16'd0;
            pa_s <= 16'd0; pb_s <= 16'd0; pc_s <= 16'd0; sa <= 16'd0; sb <= 16'd0;
            va <= 1'b0; vb <= 1'b0; pwm_a <= 1'b0; pwm_b <= 1'b0; pwm_c <= 1'b0; pwm_wrap <= 1'b0;
        end else begin
            pwm_wrap <= 1'b0;
            if (p_s == 16'd0 || wrap) begin
                cnt  <= 16'd0;
                p_s  <= period;
                da_s <= duty_a; db_s <= duty_b; dc_s <= duty_c;
                pa_s <= phase_a; pb_s <= phase_b; pc_s <= phase_c;
                sa   <= centre(phase_a, duty_a, period);
                sb   <= centre(phase_b, duty_b, period);
                va   <= ({1'b0, duty_a} >= min_d) && (phase_a < period) && (duty_a <= period);
                vb   <= ({1'b0, duty_b} >= min_d) && (phase_b < period) && (duty_b <= period);
                pwm_wrap <= (period != 16'd0);
            end else begin
                cnt <= cnt + 16'd1;
            end
            pwm_a <= (p_s != 16'd0) && on_win(ra, da_s, dead);
            pwm_b <= (p_s != 16'd0) && on_win(rb, db_s, dead);
            pwm_c <= (p_s != 16'd0) && on_win(rc, dc_s, dead);
        end
    end
    assign gate_a = pwm_a & gate_ok & en_pad;
    assign gate_b = pwm_b & gate_ok & en_pad;
    assign gate_c = pwm_c & gate_ok & en_pad;

    // strobe and guard (strobe ticks are compared with the counter value that
    // pwm_x is computed from, so the strobe sits at the window centre)
    wire stb_a = va && (p_s != 16'd0) && (cnt == sa);
    wire stb_b = vb && (p_s != 16'd0) && (cnt == sb);
    wire [15:0] ta = rel(sa, cnt, p_s);          // ticks until the strobe
    wire [15:0] tb = rel(sb, cnt, p_s);
    wire soon = (va && (p_s != 16'd0) && ta <= {8'd0, guard}) ||
                (vb && (p_s != 16'd0) && tb <= {8'd0, guard});

    // ---------------- ADC scheduler ----------------
    localparam A_IDLE = 2'd0, A_SIN = 2'd1, A_COS = 2'd2, A_CUR = 2'd3;
    reg [1:0] ast;
    reg [7:0] ptim;
    reg       req_a, req_b;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ast <= A_IDLE; ptim <= 8'd0; req_a <= 1'b0; req_b <= 1'b0;
            adc_hold <= 1'b0; adc_start <= 1'b0; adc_mux <= 2'd0;
            smp_sh <= 1'b0; smp_valid <= 1'b0; sin_code <= 12'h800; cos_code <= 12'h800;
            ia_stb <= 1'b0; ib_stb <= 1'b0; i_a <= 12'd0; i_b <= 12'd0; late_cnt <= 8'd0;
        end else begin
            adc_start <= 1'b0; smp_sh <= 1'b0; smp_valid <= 1'b0; ia_stb <= 1'b0; ib_stb <= 1'b0;
            if (ptim != 8'hFF) ptim <= ptim + 8'd1;
            if (stb_a) req_a <= 1'b1;
            if (stb_b) req_b <= 1'b1;
            case (ast)
                A_IDLE: begin
                    if (req_a || stb_a) begin
                        adc_mux <= 2'd2; adc_start <= 1'b1; req_a <= 1'b0; ast <= A_CUR;
                        if (!stb_a && late_cnt != 8'hFF) late_cnt <= late_cnt + 8'd1;
                    end else if (req_b || stb_b) begin
                        adc_mux <= 2'd3; adc_start <= 1'b1; req_b <= 1'b0; ast <= A_CUR;
                        if (!stb_b && late_cnt != 8'hFF) late_cnt <= late_cnt + 8'd1;
                    end else if (ptim + 8'd1 >= pair_ticks && !soon && pair_ticks != 8'd0) begin
                        ptim <= 8'd0;
                        adc_hold <= 1'b1; smp_sh <= 1'b1;
                        adc_mux <= 2'd0; adc_start <= 1'b1; ast <= A_SIN;
                    end
                end
                A_SIN: if (adc_done) begin
                    sin_code <= adc_data; adc_mux <= 2'd1; adc_start <= 1'b1; ast <= A_COS;
                end
                A_COS: if (adc_done) begin
                    cos_code <= adc_data; adc_hold <= 1'b0; smp_valid <= 1'b1; ast <= A_IDLE;
                end
                A_CUR: if (adc_done) begin
                    if (adc_mux == 2'd2) begin i_a <= adc_data; ia_stb <= 1'b1; end
                    else                 begin i_b <= adc_data; ib_stb <= 1'b1; end
                    ast <= A_IDLE;
                end
            endcase
        end
    end
endmodule
