// R1_CTRL: digital macro of R1 (r1_pos, r1_bus, r1_gate logic, r1_safe FSM,
// register file). One synchronous domain on clk (r1_osc, 30 MHz nominal); the
// BiSS/SSI frame logic runs on MA and the SPI shift logic on SCLK (same pad),
// with the crossings described in r1_biss.v and r1_spi.v.
// Reset: por_n asynchronous assert, synchronous release. EN/STO_IN does not
// reset the core; it is a fault source and gates the outputs directly.
// Interface: R1_REGISTER_MAP.md sections 2 and 3.
// SPDX-License-Identifier: Apache-2.0

module r1_ctrl_top #(
    parameter [15:0] CHIP_ID    = 16'h5210,
    parameter [15:0] PROFILE_ID = 16'h0001,
    parameter [47:0] DEV_ID     = 48'h52_31_4A_46_45_30,
    parameter [31:0] DEV_SN     = 32'h0000_0000,
    parameter [15:0] MFR_ID     = 16'h0000
) (
    input  wire        clk,            // r1_osc
    input  wire        por_n,
    // pads (level-shifted to 1.2 V)
    input  wire        cs_n,
    input  wire        ma_sclk,
    input  wire        sdi,
    output wire        slo_sdo,
    input  wire        en_pad,
    output wire        fault_n,
    output wire        gate_a, gate_b, gate_c,
    // ADC (r1_adc)
    output wire        adc_hold,
    output wire        adc_start,
    output wire [1:0]  adc_mux,
    input  wire        adc_done,
    input  wire [11:0] adc_data,
    // analog r1_safe comparators, r1_t2f
    input  wire [3:0]  cmp,
    input  wire        t2f_clk,
    // analog control
    output wire [4:0]  osc_trim,
    output wire [15:0] ana_ctrl
);
    // ---------------- reset ----------------
    reg rs0, rs1;
    always @(posedge clk or negedge por_n) begin
        if (!por_n) begin rs0 <= 1'b0; rs1 <= 1'b0; end
        else        begin rs0 <= 1'b1; rs1 <= rs0; end
    end
    wire rst_n = rs1;

    // ---------------- register file ----------------
    wire        reg_wr, reg_rd;
    wire [6:0]  reg_addr;
    wire [15:0] reg_wdata, reg_rdata;
    wire [12:0] fault_mask, cause;
    wire        clr_pulse, gate_en, wdt_en, mt_en, ssi_mode, gray, as_mode, test_pos_en, force_ne, force_nw;
    wire [4:0]  st_len;
    wire [17:0] test_pos;
    wire [15:0] timeout_ticks, osc_win, wdt_period, amp_lim, ovs_lim, gain, ph_sin, ph_icos, h3,
                zero_ofs, period, duty_a, duty_b, duty_c, phase_a, phase_b, phase_c, sched, ot_lim,
                i2t_cfg, i2t_lim;
    wire [7:0]  extrap, cal_crc, dead;
    wire [11:0] ofs_sin, ofs_cos, i_zero;
    wire [9:0]  pos_cfg;
    wire        cal_valid;
    wire        osc_arm;
    reg         osc_done;
    wire [3:0]  t2f_win;

    // ---------------- position ----------------
    wire        smp_sh, smp_valid;
    wire [11:0] sin_code, cos_code, amplitude, raw_sin, raw_cos;
    wire [17:0] pos_out, meas_angle;
    wire [15:0] turns, velocity;
    wire        meas_stb, amp_low, amp_high, overspeed, track_err, pos_overrun, pos_valid;
    r1_pos u_pos (
        .clk(clk), .rst_n(rst_n), .smp_sh(smp_sh), .smp_valid(smp_valid),
        .sin_code(sin_code), .cos_code(cos_code),
        .ofs_sin(ofs_sin), .ofs_cos(ofs_cos), .gain(gain), .ph_sin(ph_sin), .ph_icos(ph_icos),
        .h3_amp(h3[7:0]), .h3_ph(h3[15:8]), .zero_ofs(zero_ofs), .dir(pos_cfg[0]),
        .kp_sh(pos_cfg[4:1]), .ki_sh(pos_cfg[9:5]), .extrap(extrap),
        .amp_lo(amp_lim[7:0]), .amp_hi(amp_lim[15:8]), .ovs_lim(ovs_lim),
        .pos_out(pos_out), .turns(turns), .velocity(velocity), .amplitude(amplitude),
        .raw_sin(raw_sin), .raw_cos(raw_cos), .meas_angle(meas_angle), .meas_stb(meas_stb),
        .amp_low(amp_low), .amp_high(amp_high), .overspeed(overspeed), .track_err(track_err),
        .overrun(pos_overrun), .pos_valid(pos_valid));
    reg [7:0] pos_ovr_cnt;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) pos_ovr_cnt <= 8'd0;
        else if (pos_overrun && pos_ovr_cnt != 8'hFF) pos_ovr_cnt <= pos_ovr_cnt + 8'd1;

    // ---------------- safety ----------------
    wire        fault, en_s;
    wire [15:0] temp, e_a, e_b;
    wire [11:0] i_a, i_b;
    wire        ia_stb, ib_stb, pwm_wrap;
    wire        biss_frame_end, spi_frame_ok;
    r1_safe u_safe (
        .clk(clk), .rst_n(rst_n), .cmp(cmp), .en_pad(en_pad), .t2f_clk(t2f_clk),
        .amp_flag(amp_low | amp_high), .ovs_flag(overspeed), .cal_valid(cal_valid),
        .wdt_kick(biss_frame_end | spi_frame_ok), .pwm_wrap(pwm_wrap), .i_a(i_a), .i_b(i_b),
        .mask(fault_mask), .clr(clr_pulse), .wdt_en(wdt_en), .wdt_period(wdt_period),
        .ot_lim(ot_lim), .t2f_win(t2f_win), .tau_sh(i2t_cfg[3:0]), .i2t_pre(i2t_cfg[7:4]),
        .cmp_filt(i2t_cfg[11:8]), .i2t_lim(i2t_lim), .i_zero(i_zero),
        .cause(cause), .fault(fault), .temp(temp), .e_a_hi(e_a), .e_b_hi(e_b), .en_s(en_s));
    assign fault_n = ~fault;

    reg gate_ok;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) gate_ok <= 1'b0;
        else        gate_ok <= gate_en & ~fault & en_s;

    // ---------------- gate and ADC scheduling ----------------
    wire [7:0] late_cnt;
    r1_gate u_gate (
        .clk(clk), .rst_n(rst_n), .period(period), .duty_a(duty_a), .duty_b(duty_b), .duty_c(duty_c),
        .phase_a(phase_a), .phase_b(phase_b), .phase_c(phase_c), .dead(dead),
        .pair_ticks(sched[7:0]), .guard(sched[15:8]), .gate_ok(gate_ok), .en_pad(en_pad),
        .gate_a(gate_a), .gate_b(gate_b), .gate_c(gate_c), .pwm_wrap(pwm_wrap),
        .adc_hold(adc_hold), .adc_start(adc_start), .adc_mux(adc_mux), .adc_done(adc_done),
        .adc_data(adc_data), .smp_sh(smp_sh), .smp_valid(smp_valid), .sin_code(sin_code),
        .cos_code(cos_code), .ia_stb(ia_stb), .ib_stb(ib_stb), .i_a(i_a), .i_b(i_b),
        .late_cnt(late_cnt));

    // ---------------- bus ----------------
    wire [15:0] osc_count;
    wire        clk_fault = (osc_win != 16'd0) && osc_done &&
                            ((osc_count[11:4] < osc_win[7:0]) || (osc_count[11:4] > osc_win[15:8]) ||
                             (osc_count[15:12] != 4'd0));
    wire [15:0] status = {5'd0, osc_done, gate_ok, en_s, fault, pos_valid, clk_fault, cal_valid,
                          track_err, overspeed, amp_high, amp_low};
    wire [17:0] frame_pos = test_pos_en ? test_pos : pos_out;
    wire        slo, sdo;
    wire [7:0]  biss_frames, biss_cc_err, spi_err;
    wire        lat_seen;
    r1_biss #(.PROFILE_ID(PROFILE_ID), .DEV_ID(DEV_ID), .DEV_SN(DEV_SN), .MFR_ID(MFR_ID)) u_biss (
        .clk(clk), .rst_n(rst_n), .ma(ma_sclk), .cs_n(cs_n), .slo(slo),
        .ssi_mode(ssi_mode), .gray(gray), .mt_en(mt_en), .st_len(st_len), .timeout_ticks(timeout_ticks),
        .pos(frame_pos), .turns(turns),
        .err(amp_low | amp_high | track_err | force_ne),
        .warn(fault | ~cal_valid | clk_fault | overspeed | force_nw),
        .null_val(~pos_valid & ~test_pos_en),
        .frame_end(biss_frame_end), .lat_seen(lat_seen), .cc_err_cnt(biss_cc_err), .frame_cnt(biss_frames));
    r1_spi u_spi (
        .clk(clk), .rst_n(rst_n), .sclk(ma_sclk), .cs_n(cs_n), .sdi(sdi), .sdo(sdo), .as_mode(as_mode),
        .reg_wr(reg_wr), .reg_addr(reg_addr), .reg_wdata(reg_wdata), .reg_rdata(reg_rdata), .reg_rd(reg_rd),
        .status8(status[7:0]), .pos(pos_out), .amplitude(amplitude), .amp_low(amp_low), .amp_high(amp_high),
        .frame_ok(spi_frame_ok), .err_cnt(spi_err));
    assign slo_sdo = cs_n ? slo : sdo;

    // OSC_COUNT: clk ticks over 16 rising edges of the MA/SCLK pad. Writing
    // OSC_CFG.MEAS arms one measurement: the window starts at the next 16-edge
    // boundary, the count of the following complete window is held until the
    // next arm (STATUS.OSC_DONE).
    reg [3:0]  pc;
    reg        p16_tog;
    always @(posedge ma_sclk or negedge rst_n) begin
        if (!rst_n) begin pc <= 4'd0; p16_tog <= 1'b0; end
        else begin pc <= pc + 4'd1; if (pc == 4'd15) p16_tog <= ~p16_tog; end
    end
    wire p16_s;
    r1_sync2 #(.W(1)) u_sp16 (.clk(clk), .rst_n(rst_n), .d(p16_tog), .q(p16_s));
    reg        p16_d;
    reg [1:0]  om;                     // 0 idle/done, 1 armed, 2 counting

    reg [15:0] oc_run, oc_q;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin p16_d <= 1'b0; om <= 2'd0; osc_done <= 1'b0; oc_run <= 16'd0; oc_q <= 16'd0; end
        else begin
            p16_d <= p16_s;
            if (osc_arm) begin om <= 2'd1; osc_done <= 1'b0; end
            else if (p16_s != p16_d) begin
                if (om == 2'd1) begin om <= 2'd2; oc_run <= 16'd1; end
                else if (om == 2'd2) begin om <= 2'd0; oc_q <= oc_run; osc_done <= 1'b1; end
            end else if (om == 2'd2 && oc_run != 16'hFFFF) oc_run <= oc_run + 16'd1;
        end
    end
    assign osc_count = oc_q;

    // ---------------- registers ----------------
    wire [7:0] id_byte;
    r1_idrom #(.PROFILE_ID(PROFILE_ID), .DEV_ID(DEV_ID), .DEV_SN(DEV_SN), .MFR_ID(MFR_ID))
        u_rom (.addr(reg_addr), .data(id_byte));
    r1_regs #(.CHIP_ID(CHIP_ID)) u_regs (
        .clk(clk), .rst_n(rst_n), .wr(reg_wr), .addr(reg_addr), .wdata(reg_wdata), .rd(reg_rd),
        .rdata(reg_rdata), .status(status), .fault_cause(cause), .osc_count(osc_count),
        .pos(pos_out), .turns(turns), .velocity(velocity), .amplitude(amplitude),
        .raw_sin(raw_sin), .raw_cos(raw_cos), .meas_angle(meas_angle), .i_a(i_a), .i_b(i_b),
        .temp(temp), .e_a(e_a), .e_b(e_b), .biss_frames(biss_frames), .biss_cc_err(biss_cc_err),
        .spi_err(spi_err), .pos_ovr(pos_ovr_cnt), .late_cnt(late_cnt), .id_byte(id_byte),
        .fault_mask(fault_mask), .clr_pulse(clr_pulse), .gate_en(gate_en), .wdt_en(wdt_en),
        .st_len(st_len), .mt_en(mt_en), .ssi_mode(ssi_mode), .gray(gray), .as_mode(as_mode),
        .test_pos_en(test_pos_en), .force_ne(force_ne), .force_nw(force_nw), .test_pos(test_pos),
        .timeout_ticks(timeout_ticks), .osc_trim(osc_trim), .osc_arm(osc_arm), .osc_win(osc_win), .wdt_period(wdt_period),
        .ana_ctrl(ana_ctrl), .extrap(extrap), .amp_lim(amp_lim), .ovs_lim(ovs_lim),
        .ofs_sin(ofs_sin), .ofs_cos(ofs_cos), .gain(gain), .ph_sin(ph_sin), .ph_icos(ph_icos),
        .h3(h3), .zero_ofs(zero_ofs), .pos_cfg(pos_cfg), .cal_crc(cal_crc), .cal_valid(cal_valid),
        .period(period), .duty_a(duty_a), .duty_b(duty_b), .duty_c(duty_c), .phase_a(phase_a),
        .phase_b(phase_b), .phase_c(phase_c), .dead(dead), .sched(sched), .ot_lim(ot_lim),
        .i2t_cfg(i2t_cfg), .i2t_lim(i2t_lim), .i_zero(i_zero), .t2f_win(t2f_win));
endmodule
