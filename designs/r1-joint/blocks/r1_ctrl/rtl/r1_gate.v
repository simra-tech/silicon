// R1_CTRL / r1_gate logic (revision 0.3): PWM counter, three low-side gate
// channels with dead time, the current-pair sample strobe, the isense
// auto-zero window, and the frame generator of the two-slice SAR ADC
// (INTERFACES.md "ADC -> ctrl", D18: slice A = SIN or ISA, slice B = COS or
// ISB, both slices convert in parallel; {SIN, COS} on adc_hold, {ISA, ISB} on
// is_smp; per conversion 14 raw decisions per slice, corrected by one r1_adcw
// per slice with its own 14 weights).
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
// Frame generator (revision 0.3, D18): an encoder frame (adc_hold, adc_sel = 0,
// one adc_start for both slices) starts every PAIR_TICKS (reset 22) unless the
// current strobe is due within GUARD ticks. The current frame (is_smp,
// adc_sel = 1) starts at the strobe tick (or as soon as both slices are free;
// late starts are counted) and replaces one encoder frame; the frame grid
// restarts at the current frame, so for a PWM period of N x PAIR_TICKS the
// encoder gap is 2 x PAIR_TICKS once per period. The holds are released when
// both slices have returned adc_valid. The corrected codes arrive 4 ticks after
// adc_valid (r1_adcw). A new encoder frame does not start while the codes of the
// previous encoder pair are still in r1_adcw (sc_pend): r1_pos keeps one NCO
// snapshot per pair (taken at smp_sh), so smp_valid of pair n must not come after
// smp_sh of pair n+1 (the same tick is allowed). The encoder frame is therefore
// max(PAIR_TICKS, conversion + 5 ticks), with the conversion counted from the
// adc_start pulse to the later adc_valid pulse: 22 ticks for <= 17 ticks.
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
    output reg          adc_start,      // pulse: both slices start a conversion of adc_sel
    output reg          adc_sel,        // 0 encoder {SIN, COS}, 1 current {ISA, ISB}
    input  wire         adc_valid_a,    // pulse: adc_raw_a valid (slice A)
    input  wire [13:0]  adc_raw_a,
    input  wire         adc_valid_b,    // pulse: adc_raw_b valid (slice B)
    input  wire [13:0]  adc_raw_b,
    input  wire [195:0] adc_wa,         // slice A weights
    input  wire [195:0] adc_wb,         // slice B weights
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

    // ---------------- ADC weight correction (one per slice) ----------------
    wire        cva, cvb;
    wire [11:0] codea, codeb;
    r1_adcw u_wa (.clk(clk), .rst_n(rst_n), .valid(adc_valid_a), .raw(adc_raw_a), .w(adc_wa),
                  .code_valid(cva), .code(codea));
    r1_adcw u_wb (.clk(clk), .rst_n(rst_n), .valid(adc_valid_b), .raw(adc_raw_b), .w(adc_wb),
                  .code_valid(cvb), .code(codeb));

    // ---------------- frame generator ----------------
    reg        conv;                   // a frame is converting (holds closed)
    reg        got_a, got_b;           // adc_valid seen per slice in this frame
    reg [7:0]  ptim;
    reg        req;
    reg        tag_a;                  // frame type of the codes in r1_adcw (slice A sets the pair type)
    reg [11:0] ca, cb;                 // first-arrived code until its partner is done
    reg        pa_r, pb_r;
    reg        sc_pend;                // encoder codes not yet out of r1_adcw
    wire       nga = got_a | adc_valid_a, ngb = got_b | adc_valid_b;
    wire       nra = pa_r | cva,  nrb = pb_r | cvb;
    wire [11:0] nca = cva ? codea : ca, ncb = cvb ? codeb : cb;
    wire       enc_done = nra && nrb && !tag_a;  // encoder pair leaves r1_adcw in this tick

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            conv <= 1'b0; got_a <= 1'b0; got_b <= 1'b0; ptim <= 8'd0; req <= 1'b0; tag_a <= 1'b0;
            ca <= 12'h800; cb <= 12'h800; pa_r <= 1'b0; pb_r <= 1'b0; sc_pend <= 1'b0;
            adc_hold <= 1'b0; is_smp <= 1'b0; adc_start <= 1'b0; adc_sel <= 1'b0;
            smp_sh <= 1'b0; smp_valid <= 1'b0; sin_code <= 12'h800; cos_code <= 12'h800;
            i_a <= 12'd0; i_b <= 12'd0; late_cnt <= 4'd0;
        end else begin
            adc_start <= 1'b0; smp_sh <= 1'b0; smp_valid <= 1'b0;
            if (ptim != 8'hFF) ptim <= ptim + 8'd1;
            if (stb) req <= 1'b1;
            if (adc_valid_a) tag_a <= adc_sel;
            // corrected codes: the pair is complete when both slices have a code
            if (nra && nrb) begin
                pa_r <= 1'b0; pb_r <= 1'b0;
                if (!tag_a) begin sin_code <= nca; cos_code <= ncb; smp_valid <= 1'b1; sc_pend <= 1'b0; end   // a start below overrides
                else        begin i_a <= nca; i_b <= ncb; end
            end else begin
                pa_r <= nra; pb_r <= nrb; ca <= nca; cb <= ncb;
            end
            if (!conv) begin
                if (req || stb) begin                              // current frame (D18: replaces an encoder frame)
                    is_smp <= 1'b1; adc_sel <= 1'b1; adc_start <= 1'b1; req <= 1'b0; conv <= 1'b1;
                    ptim <= 8'd0;
                    if (!stb && late_cnt != 4'hF) late_cnt <= late_cnt + 4'd1;
                end else if (ptim + 8'd1 >= pair_ticks && !soon && pair_ticks != 8'd0 && (!sc_pend || enc_done)) begin
                    ptim <= 8'd0; sc_pend <= 1'b1;
                    adc_hold <= 1'b1; smp_sh <= 1'b1;
                    adc_sel <= 1'b0; adc_start <= 1'b1; conv <= 1'b1;
                end
                got_a <= 1'b0; got_b <= 1'b0;
            end else if (nga && ngb) begin                         // both slices done: release the holds
                adc_hold <= 1'b0; is_smp <= 1'b0; conv <= 1'b0; got_a <= 1'b0; got_b <= 1'b0;
            end else begin
                got_a <= nga; got_b <= ngb;
            end
        end
    end
endmodule
