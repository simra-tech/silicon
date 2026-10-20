// R1_CTRL: register file (R1_REGISTER_MAP.md revision 0.2), read multiplexer
// and the calibration CRC checker.
// Revision 0.2: host-written configuration words are latch words (r1_cword,
// see r1_lib.v); only registers with self-clearing bits (CTRL, OSC_CFG.MEAS)
// and the RAW_COS snapshot are flip-flops. A write takes effect one tick later
// than in revision 0.1 (the gated latch opens in the cycle after the write
// pulse). Only the bits listed in the map are stored; other bits read 0.
// Calibration CRC: CRC-8, polynomial 0x07, initial 0xFF, no reflection, no final
// XOR, over registers 0x10..0x17 in address order, high byte first. A byte-serial
// engine walks the 16 bytes continuously; CAL_VALID = (result == CAL_CRC) at the
// end of a pass; any write to 0x10..0x18 clears CAL_VALID until the next
// complete pass.
// SPDX-License-Identifier: Apache-2.0

module r1_regs #(
    parameter [15:0] CHIP_ID = 16'h5202
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        wr,
    input  wire [6:0]  addr,
    input  wire [15:0] wdata,
    input  wire        rd,             // read strobe (side effects)
    output reg  [15:0] rdata,
    // status inputs
    input  wire [15:0] status,
    input  wire [12:0] fault_cause,
    input  wire [15:0] osc_count,
    input  wire [17:0] pos,
    input  wire [15:0] turns,
    input  wire [15:0] velocity,
    input  wire [11:0] amplitude,
    input  wire [11:0] raw_sin,
    input  wire [11:0] raw_cos,
    input  wire [17:0] meas_angle,
    input  wire [11:0] i_a, i_b,
    input  wire [13:0] temp,
    input  wire [15:0] e_a, e_b,
    input  wire [7:0]  biss_frames,
    input  wire [3:0]  biss_cc_err, spi_err, pos_ovr, late_cnt,   // saturating
    input  wire [7:0]  id_byte,        // BiSS ID ROM byte for addr 0x40..0x47, 0x78..0x7F
    input  wire [15:0] cmp_cal_a,      // CMP_CAL_A / _B read values (r1_cmpcal)
    input  wire [15:0] cmp_cal_b,
    // configuration outputs
    output wire [12:0] fault_mask,
    output reg         clr_pulse,
    output reg         gate_en,
    output reg         wdt_en,
    output reg         cal_run,        // pulse: CTRL.CMP_CAL written 1
    output wire [4:0]  st_len,
    output wire        mt_en, ssi_mode, gray, as_mode, test_pos_en, force_ne, force_nw, lat_half,
    output wire [17:0] test_pos,
    output wire [11:0] timeout_ticks,
    output wire [4:0]  osc_trim,
    output reg         osc_arm,        // pulse: OSC_CFG.MEAS written 1
    output wire [15:0] osc_win,
    output wire [15:0] wdt_period,
    output wire [15:0] ana_ctrl,
    output wire [7:0]  extrap,
    output wire [15:0] amp_lim,
    output wire [15:0] ovs_lim,
    output wire [11:0] ofs_sin, ofs_cos,
    output wire [15:0] gain, ph_sin, ph_icos,
    output wire [15:0] h3,
    output wire [15:0] zero_ofs,
    output wire [9:0]  pos_cfg,
    output wire [7:0]  cal_crc,
    output reg         cal_valid,
    output wire [15:0] period, duty_a, duty_b, duty_c, phase_a, phase_b, phase_c,
    output wire [7:0]  dead,
    output wire [15:0] sched,
    output wire [13:0] ot_lim,
    output wire [11:0] i2t_cfg,
    output wire [15:0] i2t_lim,
    output wire [11:0] i_zero,
    output wire [3:0]  t2f_win,
    output wire [13:0] cmp_thr_a,      // [5:0] THR_OC_A, [13:8] THR_NEG_A
    output wire [13:0] cmp_thr_b,
    output wire [15:0] az_start,
    output wire [13:0] az_cfg,         // [7:0] AZ_LEN, [13:8] THR_ZERO
    output wire        cmp_cal_wr_a,   // host write of CMP_CAL_A / _B (data = wdata)
    output wire        cmp_cal_wr_b,
    output wire [181:0] adc_w          // 13 x 14-bit ADC weights, w[i] at [14*i +: 14]
);
    // ---------------- latch configuration words ----------------
    r1_cword #(.W(13), .A(7'h03)) u_03 (clk, rst_n, wr, addr, wdata[12:0], fault_mask);
    wire [14:0] bus_cfg;
    r1_cword #(.W(15), .RV(15'h40B2), .A(7'h05)) u_05 (clk, rst_n, wr, addr, {wdata[14:9], 1'b0, wdata[7:0]}, bus_cfg);  // bit 8 reserved (0.1 AS_MODE)
    assign st_len = bus_cfg[4:0];  assign mt_en = bus_cfg[5];      assign ssi_mode = bus_cfg[6];
    assign gray = bus_cfg[7];      assign as_mode = bus_cfg[8];    assign test_pos_en = bus_cfg[9];
    assign force_ne = bus_cfg[10]; assign force_nw = bus_cfg[11];
    assign test_pos[17:16] = bus_cfg[13:12];  assign lat_half = bus_cfg[14];
    r1_cword #(.W(16), .A(7'h06)) u_06 (clk, rst_n, wr, addr, wdata, test_pos[15:0]);
    r1_cword #(.W(12), .RV(12'd600), .A(7'h07)) u_07 (clk, rst_n, wr, addr, wdata[11:0], timeout_ticks);
    r1_cword #(.W(5),  .RV(5'd22),  .A(7'h08)) u_08 (clk, rst_n, wr, addr, wdata[4:0], osc_trim);
    r1_cword #(.W(16), .A(7'h0A)) u_0a (clk, rst_n, wr, addr, wdata, osc_win);
    r1_cword #(.W(16), .RV(16'hFFFF), .A(7'h0B)) u_0b (clk, rst_n, wr, addr, wdata, wdt_period);
    r1_cword #(.W(16), .A(7'h0C)) u_0c (clk, rst_n, wr, addr, wdata, ana_ctrl);
    r1_cword #(.W(8),  .A(7'h0D)) u_0d (clk, rst_n, wr, addr, wdata[7:0], extrap);
    r1_cword #(.W(16), .RV(16'h7C08), .A(7'h0E)) u_0e (clk, rst_n, wr, addr, wdata, amp_lim);
    r1_cword #(.W(16), .RV(16'h4000), .A(7'h0F)) u_0f (clk, rst_n, wr, addr, wdata, ovs_lim);
    r1_cword #(.W(12), .A(7'h10)) u_10 (clk, rst_n, wr, addr, wdata[11:0], ofs_sin);
    r1_cword #(.W(12), .A(7'h11)) u_11 (clk, rst_n, wr, addr, wdata[11:0], ofs_cos);
    r1_cword #(.W(16), .RV(16'h4000), .A(7'h12)) u_12 (clk, rst_n, wr, addr, wdata, gain);
    r1_cword #(.W(16), .A(7'h13)) u_13 (clk, rst_n, wr, addr, wdata, ph_sin);
    r1_cword #(.W(16), .RV(16'h4000), .A(7'h14)) u_14 (clk, rst_n, wr, addr, wdata, ph_icos);
    r1_cword #(.W(16), .A(7'h15)) u_15 (clk, rst_n, wr, addr, wdata, h3);
    r1_cword #(.W(16), .A(7'h16)) u_16 (clk, rst_n, wr, addr, wdata, zero_ofs);
    r1_cword #(.W(10), .RV(10'h164), .A(7'h17)) u_17 (clk, rst_n, wr, addr, wdata[9:0], pos_cfg);
    r1_cword #(.W(8),  .A(7'h18)) u_18 (clk, rst_n, wr, addr, wdata[7:0], cal_crc);
    r1_cword #(.W(16), .A(7'h20)) u_20 (clk, rst_n, wr, addr, wdata, period);
    r1_cword #(.W(16), .A(7'h21)) u_21 (clk, rst_n, wr, addr, wdata, duty_a);
    r1_cword #(.W(16), .A(7'h22)) u_22 (clk, rst_n, wr, addr, wdata, duty_b);
    r1_cword #(.W(16), .A(7'h23)) u_23 (clk, rst_n, wr, addr, wdata, duty_c);
    r1_cword #(.W(16), .A(7'h24)) u_24 (clk, rst_n, wr, addr, wdata, phase_a);
    r1_cword #(.W(16), .A(7'h25)) u_25 (clk, rst_n, wr, addr, wdata, phase_b);
    r1_cword #(.W(16), .A(7'h26)) u_26 (clk, rst_n, wr, addr, wdata, phase_c);
    r1_cword #(.W(8),  .RV(8'd15), .A(7'h27)) u_27 (clk, rst_n, wr, addr, wdata[7:0], dead);
    r1_cword #(.W(16), .RV(16'h201E), .A(7'h28)) u_28 (clk, rst_n, wr, addr, wdata, sched);
    r1_cword #(.W(14), .RV(14'h3FFF), .A(7'h2C)) u_2c (clk, rst_n, wr, addr, wdata[13:0], ot_lim);
    r1_cword #(.W(12), .A(7'h2D)) u_2d (clk, rst_n, wr, addr, wdata[11:0], i2t_cfg);
    r1_cword #(.W(16), .RV(16'hFFFF), .A(7'h2E)) u_2e (clk, rst_n, wr, addr, wdata, i2t_lim);
    r1_cword #(.W(12), .A(7'h2F)) u_2f (clk, rst_n, wr, addr, wdata[11:0], i_zero);
    r1_cword #(.W(4),  .RV(4'd15), .A(7'h34)) u_34 (clk, rst_n, wr, addr, wdata[3:0], t2f_win);
    wire [11:0] thr_w = {wdata[13:8], wdata[5:0]};
    wire [11:0] thr_a, thr_b;
    r1_cword #(.W(12), .RV(12'hFFF), .A(7'h36)) u_36 (clk, rst_n, wr, addr, thr_w, thr_a);
    r1_cword #(.W(12), .RV(12'hFFF), .A(7'h37)) u_37 (clk, rst_n, wr, addr, thr_w, thr_b);
    assign cmp_thr_a = {thr_a[11:6], 2'b00, thr_a[5:0]};
    assign cmp_thr_b = {thr_b[11:6], 2'b00, thr_b[5:0]};
    r1_cword #(.W(16), .A(7'h38)) u_38 (clk, rst_n, wr, addr, wdata, az_start);
    r1_cword #(.W(14), .RV(14'h2000), .A(7'h39)) u_39 (clk, rst_n, wr, addr, wdata[13:0], az_cfg);
    assign cmp_cal_wr_a = wr && (addr == 7'h3A);
    assign cmp_cal_wr_b = wr && (addr == 7'h3B);

    // ADC weights (D12): 0x50 + i, 14 bit, units of 1/4 LSB; reset = binary
    // (w[i] = 4 * 2^i for i = 0..11) and w[12] = 4 * 64 for the redundant decision
    genvar gi;
    generate
        for (gi = 0; gi < 13; gi = gi + 1) begin : g_w
            localparam [13:0] WRV = (gi < 12) ? (14'd4 << gi) : 14'd256;
            r1_cword #(.W(14), .RV(WRV), .A(7'h50 + gi)) u_w (clk, rst_n, wr, addr, wdata[13:0], adc_w[14*gi +: 14]);
        end
    endgenerate

    // ---------------- flip-flop registers ----------------
    reg [11:0] raw_cos_hold;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clr_pulse <= 1'b0; osc_arm <= 1'b0; cal_run <= 1'b0; gate_en <= 1'b0; wdt_en <= 1'b0;
            raw_cos_hold <= 12'h800;
        end else begin
            clr_pulse <= 1'b0;
            osc_arm   <= 1'b0;
            cal_run   <= 1'b0;
            if (rd && addr == 7'h1D) raw_cos_hold <= raw_cos;     // pair snapshot
            if (wr && addr == 7'h04) begin
                clr_pulse <= wdata[0]; gate_en <= wdata[1]; wdt_en <= wdata[2]; cal_run <= wdata[3];
            end
            if (wr && addr == 7'h08) osc_arm <= wdata[8];
        end
    end

    // ---------------- calibration CRC ----------------
    reg [3:0] cbyte;
    reg [7:0] crc;
    reg       dirty;
    reg [7:0] cb;
    always @(*) begin
        case (cbyte)
            4'd0:  cb = {4'd0, ofs_sin[11:8]};  4'd1:  cb = ofs_sin[7:0];
            4'd2:  cb = {4'd0, ofs_cos[11:8]};  4'd3:  cb = ofs_cos[7:0];
            4'd4:  cb = gain[15:8];             4'd5:  cb = gain[7:0];
            4'd6:  cb = ph_sin[15:8];           4'd7:  cb = ph_sin[7:0];
            4'd8:  cb = ph_icos[15:8];          4'd9:  cb = ph_icos[7:0];
            4'd10: cb = h3[15:8];               4'd11: cb = h3[7:0];
            4'd12: cb = zero_ofs[15:8];         4'd13: cb = zero_ofs[7:0];
            4'd14: cb = {6'd0, pos_cfg[9:8]};   default: cb = pos_cfg[7:0];
        endcase
    end
    function [7:0] crc8_byte;
        input [7:0] c, d;
        integer i;
        reg [7:0] r;
        begin
            r = c ^ d;
            for (i = 0; i < 8; i = i + 1) r = r[7] ? ({r[6:0], 1'b0} ^ 8'h07) : {r[6:0], 1'b0};
            crc8_byte = r;
        end
    endfunction
    wire [7:0] crc_n = crc8_byte((cbyte == 4'd0) ? 8'hFF : crc, cb);
    // the latch word changes in the tick after the write pulse; a write marks the
    // pass dirty in both ticks so no pass mixes old and new values
    reg  cal_wr_d;
    wire cal_wr = wr && (addr >= 7'h10) && (addr <= 7'h18);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cbyte <= 4'd0; crc <= 8'hFF; dirty <= 1'b1; cal_valid <= 1'b0; cal_wr_d <= 1'b0;
        end else begin
            crc      <= crc_n;
            cbyte    <= cbyte + 4'd1;
            cal_wr_d <= cal_wr;
            if (cal_wr || cal_wr_d) begin
                dirty <= 1'b1; cal_valid <= 1'b0;
            end else if (cbyte == 4'd15) begin
                if (dirty) dirty <= 1'b0;                  // a full clean pass is needed
                else cal_valid <= (crc_n == cal_crc);
            end
        end
    end

    // ---------------- read multiplexer ----------------
    always @(*) begin
        case (addr)
            7'h00: rdata = CHIP_ID;
            7'h01: rdata = status;
            7'h02: rdata = {3'd0, fault_cause};
            7'h03: rdata = {3'd0, fault_mask};
            7'h04: rdata = {13'd0, wdt_en, gate_en, 1'b0};
            7'h05: rdata = {1'b0, bus_cfg};
            7'h06: rdata = test_pos[15:0];
            7'h07: rdata = {4'd0, timeout_ticks};
            7'h08: rdata = {11'd0, osc_trim};
            7'h09: rdata = osc_count;
            7'h0A: rdata = osc_win;
            7'h0B: rdata = wdt_period;
            7'h0C: rdata = ana_ctrl;
            7'h0D: rdata = {8'd0, extrap};
            7'h0E: rdata = amp_lim;
            7'h0F: rdata = ovs_lim;
            7'h10: rdata = {4'd0, ofs_sin};
            7'h11: rdata = {4'd0, ofs_cos};
            7'h12: rdata = gain;
            7'h13: rdata = ph_sin;
            7'h14: rdata = ph_icos;
            7'h15: rdata = h3;
            7'h16: rdata = zero_ofs;
            7'h17: rdata = {6'd0, pos_cfg};
            7'h18: rdata = {8'd0, cal_crc};
            7'h19: rdata = pos[17:2];
            7'h1A: rdata = turns;
            7'h1B: rdata = velocity;
            7'h1C: rdata = {4'd0, amplitude};
            7'h1D: rdata = {4'd0, raw_sin};
            7'h1E: rdata = {4'd0, raw_cos_hold};
            7'h1F: rdata = meas_angle[17:2];
            7'h20: rdata = period;
            7'h21: rdata = duty_a;
            7'h22: rdata = duty_b;
            7'h23: rdata = duty_c;
            7'h24: rdata = phase_a;
            7'h25: rdata = phase_b;
            7'h26: rdata = phase_c;
            7'h27: rdata = {8'd0, dead};
            7'h28: rdata = sched;
            7'h29: rdata = {4'd0, i_a};
            7'h2A: rdata = {4'd0, i_b};
            7'h2B: rdata = {2'd0, temp};
            7'h2C: rdata = {2'd0, ot_lim};
            7'h2D: rdata = {4'd0, i2t_cfg};
            7'h2E: rdata = i2t_lim;
            7'h2F: rdata = {4'd0, i_zero};
            7'h30: rdata = e_a;
            7'h31: rdata = e_b;
            7'h32: rdata = {4'd0, biss_cc_err, biss_frames};
            7'h33: rdata = {4'd0, pos_ovr, 4'd0, spi_err};
            7'h34: rdata = {12'd0, t2f_win};
            7'h35: rdata = {12'd0, late_cnt};
            7'h36: rdata = {2'd0, cmp_thr_a};
            7'h37: rdata = {2'd0, cmp_thr_b};
            7'h38: rdata = az_start;
            7'h39: rdata = {2'd0, az_cfg};
            7'h3A: rdata = cmp_cal_a;
            7'h3B: rdata = cmp_cal_b;
            default: begin
                if (addr[6:4] == 3'b101 && addr[3:0] <= 4'd12)
                    rdata = {2'd0, adc_w[14*addr[3:0] +: 14]};
                else
                    rdata = addr[6] ? {8'd0, id_byte} : 16'd0;
            end
        endcase
    end
endmodule
