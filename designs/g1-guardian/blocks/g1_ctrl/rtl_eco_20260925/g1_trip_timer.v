// G1_CTRL: trip timer. Behaviour: G1_REGISTER_MAP.md section 5.
// Soft path: up/down accumulator in osc_clk cycles against a 16-bit window
//   (units of 256 osc_clk). cmp_soft is a level held by the comparator's latch.
// Hard path: N consecutive comparator decisions, clear on low. The hard
//   comparator decides once per cmp_clk period (cmp_clk = osc_clk/2, falling
//   edge), so it is sampled once per period: HARD_N is in cmp_clk samples.
// Inrush mask after reset release and after each retrigger re-enable.
// ECO 2026-09-25 (blocks/g1_ctrl/ECO_20260925.md, change 2): once a mask window
// has ended it stays ended (inrush_done) until the next re-enable or reset, so
// a live INRUSH write cannot re-open it.
// Latched or retrigger mode with hold time and give-up count.
// G1_GATE interface (blocks/g1_trip/INTERFACE.md): trip_d = latch state (level),
//   clr_d = 2-cycle clear pulse on every clear/re-enable, tripped = analog latch
//   state (asynchronous, synchronised here); an analog-side trip (fast path) is
//   adopted into the digital latch with cause "hard".
// Sense offset (INTERFACE.md, sense_ofs): signed, added to both DAC codes with
//   saturation at 0/255, after the digital hysteresis on the soft code.
// SPDX-License-Identifier: Apache-2.0

module g1_trip_timer (
    input  wire        clk,          // osc_clk
    input  wire        rst_n,        // async assert (EN low or POR), sync release
    input  wire        cmp_clk,      // osc_clk/2 as driven to G1_TRIP (phase reference)
    // comparator and latch inputs (asynchronous to clk, synchronised here)
    input  wire        cmp_soft,
    input  wire        cmp_hard,
    input  wire        tripped_a,    // G1_GATE latch state
    // configuration (quasi-static, from the register file)
    input  wire        soft_en,
    input  wire        hard_en,
    input  wire        retrig,
    input  wire        force_trip,
    input  wire [15:0] soft_time,    // window = soft_time * 256 cycles
    input  wire [1:0]  decay,        // 0: -1/cycle, 1: -1/4, 2: -1/16, 3: -1/64 cycles
    input  wire        hyst_en,
    input  wire        hyst_2,
    input  wire [7:0]  hard_n,       // consecutive cmp_clk samples (0 behaves as 1)
    input  wire [7:0]  inrush,       // mask = inrush * 512 cycles
    input  wire [7:0]  hold_time,    // hold = hold_time * 8192 cycles (0 behaves as 1)
    input  wire [7:0]  retry_max,    // 0xFF = unlimited
    input  wire [7:0]  dac_soft_code,
    input  wire [7:0]  dac_hard_code,
    input  wire [7:0]  sense_ofs,    // signed
    // commands (one-cycle pulses)
    input  wire        clear,
    input  wire        clr_trip_cnt,
    input  wire        clr_peak,
    // outputs
    output wire        trip,
    output reg  [1:0]  trip_cause,   // 0 none, 1 soft, 2 hard, 3 forced
    output wire        gate_en,
    output wire        fault_n,
    output wire        trip_d,       // to G1_GATE: set (level)
    output wire        clr_d,        // to G1_GATE: clear pulse, 2 cycles
    output wire        inrush_active,
    output wire        holding,
    output reg         gave_up,
    output wire        soft_armed,
    output wire        cmp_soft_s,
    output wire        cmp_hard_s,
    output wire        tripped_a_s,
    output reg  [7:0]  retry_cnt,
    output reg  [15:0] trip_cnt,
    output reg  [15:0] soft_peak,
    output wire [7:0]  dac_soft_out,
    output wire [7:0]  dac_hard_out
);

    g1_sync2 #(.W(3)) u_sync_in (
        .clk(clk), .rst_n(rst_n), .d({tripped_a, cmp_hard, cmp_soft}),
        .q({tripped_a_s, cmp_hard_s, cmp_soft_s}));

    reg tripped;
    assign trip    = tripped;
    assign trip_d  = tripped;
    assign gate_en = ~tripped;
    assign fault_n = ~tripped;
    assign holding = tripped & retrig & ~gave_up;

    // ---------------- inrush mask ----------------
    reg  [16:0] inrush_cnt;
    reg         inrush_done;       // mask window over; cleared only by re-enable or reset
    wire [16:0] inrush_lim = {inrush, 9'd0};
    assign inrush_active = ~inrush_done & (inrush_cnt < inrush_lim);

    // ---------------- soft path ----------------
    reg  [23:0] soft_cnt;
    reg  [5:0]  decay_pre;
    wire [23:0] soft_lim  = {soft_time, 8'd0};
    wire        soft_mask = ~soft_en | inrush_active | tripped;
    wire        decay_tick = (decay == 2'd0) ? 1'b1 :
                             (decay == 2'd1) ? (decay_pre[1:0] == 2'b11) :
                             (decay == 2'd2) ? (decay_pre[3:0] == 4'hF) :
                                               (decay_pre[5:0] == 6'h3F);
    wire        trip_soft = ~soft_mask & cmp_soft_s & (soft_cnt >= soft_lim);
    assign      soft_armed = (soft_cnt != 24'd0);

    // digital hysteresis: lower the soft DAC code while the accumulator is charged
    wire [7:0] hyst_step = hyst_2 ? 8'd2 : 8'd1;
    wire       hyst_on   = hyst_en & soft_armed;
    wire [7:0] soft_hyst = !hyst_on ? dac_soft_code :
                           (dac_soft_code > hyst_step) ? (dac_soft_code - hyst_step) : 8'd0;

    // sense offset: signed add, saturate at 0 and 255
    wire signed [9:0] ofs_ext   = {{2{sense_ofs[7]}}, sense_ofs};
    wire signed [9:0] soft_sum  = $signed({2'b00, soft_hyst})     + ofs_ext;
    wire signed [9:0] hard_sum  = $signed({2'b00, dac_hard_code}) + ofs_ext;
    assign dac_soft_out = soft_sum[9] ? 8'd0 : soft_sum[8] ? 8'hFF : soft_sum[7:0];
    assign dac_hard_out = hard_sum[9] ? 8'd0 : hard_sum[8] ? 8'hFF : hard_sum[7:0];

    // ---------------- hard path ----------------
    // cmp_clk falls at edge k; the decision is valid < 2 ns later; the two-flop
    // synchroniser presents it at edge k+2, i.e. during the cycle in which
    // cmp_clk (the flop driving the port) is again 0. Sample once per period there.
    wire       hard_sample = ~cmp_clk;
    reg  [7:0] hard_cnt;
    wire [7:0] hard_n_m1 = (hard_n == 8'd0) ? 8'd0 : (hard_n - 8'd1);
    wire       hard_mask = ~hard_en | inrush_active | tripped;
    wire       trip_hard = ~hard_mask & hard_sample & cmp_hard_s & (hard_cnt >= hard_n_m1);

    // ---------------- analog latch (G1_GATE) ----------------
    // Adopt an analog-side trip (fast path, or any set of the latch the digital
    // did not command) into the digital latch. Masked for a few cycles after every
    // clear pulse so the not-yet-synchronised old state cannot re-trip.
    reg  [2:0] clr_mask;
    reg  [1:0] clr_pulse;
    assign clr_d = (clr_pulse != 2'd0);
    wire   trip_ext = ~tripped & tripped_a_s & (clr_mask == 3'd0);

    // ---------------- latch / retrigger ----------------
    wire        trip_set  = ~tripped & (force_trip | trip_hard | trip_soft | trip_ext);
    reg  [20:0] hold_cnt;
    wire [7:0]  hold_eff  = (hold_time == 8'd0) ? 8'd1 : hold_time;
    wire [20:0] hold_lim  = {hold_eff, 13'd0};
    wire        hold_done = (hold_cnt >= hold_lim);
    wire        retries_left = (retry_max == 8'hFF) || (retry_cnt < retry_max);
    wire        reenable  = holding & hold_done;
    wire        latch_clr = clear | reenable;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            inrush_cnt <= 17'd0;
            inrush_done <= 1'b0;
            soft_cnt   <= 24'd0;
            decay_pre  <= 6'd0;
            hard_cnt   <= 8'd0;
            tripped    <= 1'b0;
            trip_cause <= 2'd0;
            hold_cnt   <= 21'd0;
            retry_cnt  <= 8'd0;
            gave_up    <= 1'b0;
            trip_cnt   <= 16'd0;
            soft_peak  <= 16'd0;
            clr_mask   <= 3'd0;
            clr_pulse  <= 2'd0;
        end else begin
            // inrush
            if (reenable) begin
                inrush_cnt  <= 17'd0;
                inrush_done <= 1'b0;
            end else if (inrush_active)
                inrush_cnt  <= inrush_cnt + 17'd1;
            else
                inrush_done <= 1'b1;

            // soft accumulator
            if (soft_mask) begin
                soft_cnt  <= 24'd0;
                decay_pre <= 6'd0;
            end else if (cmp_soft_s) begin
                if (soft_cnt != 24'hFFFFFF)
                    soft_cnt <= soft_cnt + 24'd1;
                decay_pre <= 6'd0;
            end else begin
                decay_pre <= decay_pre + 6'd1;
                if (soft_cnt != 24'd0 && decay_tick)
                    soft_cnt <= soft_cnt - 24'd1;
            end

            // soft peak telemetry (units of 256 cycles)
            if (clr_peak)
                soft_peak <= 16'd0;
            else if (soft_cnt[23:8] > soft_peak)
                soft_peak <= soft_cnt[23:8];

            // hard glitch filter, one count per comparator decision
            if (hard_mask)
                hard_cnt <= 8'd0;
            else if (hard_sample) begin
                if (~cmp_hard_s)
                    hard_cnt <= 8'd0;
                else if (hard_cnt != 8'hFF)
                    hard_cnt <= hard_cnt + 8'd1;
            end

            // clear pulse to the analog latch and the re-trip mask
            if (latch_clr) begin
                clr_pulse <= 2'd2;
                clr_mask  <= 3'd5;
            end else begin
                if (clr_pulse != 2'd0) clr_pulse <= clr_pulse - 2'd1;
                if (clr_mask  != 3'd0) clr_mask  <= clr_mask  - 3'd1;
            end

            // trip latch
            if (clear) begin
                tripped    <= 1'b0;
                trip_cause <= 2'd0;
                gave_up    <= 1'b0;
                retry_cnt  <= 8'd0;
                hold_cnt   <= 21'd0;
            end else if (trip_set) begin
                tripped    <= 1'b1;
                trip_cause <= force_trip ? 2'd3 : (trip_hard | trip_ext) ? 2'd2 : 2'd1;
                hold_cnt   <= 21'd0;
                if (retrig && !retries_left)
                    gave_up <= 1'b1;
            end else if (reenable) begin
                tripped    <= 1'b0;
                trip_cause <= 2'd0;
                hold_cnt   <= 21'd0;
                if (retry_cnt != 8'hFF)
                    retry_cnt <= retry_cnt + 8'd1;
            end else if (holding) begin
                hold_cnt <= hold_cnt + 21'd1;
            end else if (!tripped && !inrush_active && retry_cnt != 8'd0) begin
                // cool-down: a re-enable that survives one hold time resets the retry count
                if (hold_done) begin
                    retry_cnt <= 8'd0;
                    hold_cnt  <= 21'd0;
                end else begin
                    hold_cnt <= hold_cnt + 21'd1;
                end
            end

            // trip event counter, saturating
            if (clr_trip_cnt)
                trip_cnt <= 16'd0;
            else if (trip_set && trip_cnt != 16'hFFFF)
                trip_cnt <= trip_cnt + 16'd1;
        end
    end

endmodule
