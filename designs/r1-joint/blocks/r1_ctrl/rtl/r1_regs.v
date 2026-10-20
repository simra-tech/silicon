// R1_CTRL: register file (R1_REGISTER_MAP.md draft 0.1), read multiplexer and
// the calibration CRC checker. Only the bits listed in the map are stored;
// other bits read 0.
// Calibration CRC: CRC-8, polynomial 0x07, initial 0xFF, no reflection, no final
// XOR, over registers 0x10..0x17 in address order, high byte first. A byte-serial
// engine walks the 16 bytes continuously; CAL_VALID = (result == CAL_CRC) at the
// end of a pass; any write to 0x10..0x18 clears CAL_VALID until the next
// complete pass.
// SPDX-License-Identifier: Apache-2.0

module r1_regs #(
    parameter [15:0] CHIP_ID = 16'h5210
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
    input  wire [15:0] temp,
    input  wire [15:0] e_a, e_b,
    input  wire [7:0]  biss_frames, biss_cc_err, spi_err, pos_ovr, late_cnt,
    input  wire [7:0]  id_byte,        // BiSS ID ROM byte for addr 0x40..0x7F
    // configuration outputs
    output reg  [12:0] fault_mask,
    output reg         clr_pulse,
    output reg         gate_en,
    output reg         wdt_en,
    output reg  [4:0]  st_len,
    output reg         mt_en, ssi_mode, gray, as_mode, test_pos_en, force_ne, force_nw,
    output reg  [17:0] test_pos,
    output reg  [15:0] timeout_ticks,
    output reg  [4:0]  osc_trim,
    output reg         osc_arm,        // pulse: OSC_CFG.MEAS written 1
    output reg  [15:0] osc_win,
    output reg  [15:0] wdt_period,
    output reg  [15:0] ana_ctrl,
    output reg  [7:0]  extrap,
    output reg  [15:0] amp_lim,
    output reg  [15:0] ovs_lim,
    output reg  [11:0] ofs_sin, ofs_cos,
    output reg  [15:0] gain, ph_sin, ph_icos,
    output reg  [15:0] h3,
    output reg  [15:0] zero_ofs,
    output reg  [9:0]  pos_cfg,
    output reg  [7:0]  cal_crc,
    output reg         cal_valid,
    output reg  [15:0] period, duty_a, duty_b, duty_c, phase_a, phase_b, phase_c,
    output reg  [7:0]  dead,
    output reg  [15:0] sched,
    output reg  [15:0] ot_lim,
    output reg  [15:0] i2t_cfg,
    output reg  [15:0] i2t_lim,
    output reg  [11:0] i_zero,
    output reg  [3:0]  t2f_win
);
    reg [11:0] raw_cos_hold;

    // ---------------- writes ----------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_mask <= 13'd0; clr_pulse <= 1'b0; osc_arm <= 1'b0; gate_en <= 1'b0; wdt_en <= 1'b0;
            st_len <= 5'd18; mt_en <= 1'b1; ssi_mode <= 1'b0; gray <= 1'b1; as_mode <= 1'b0;
            test_pos_en <= 1'b0; force_ne <= 1'b0; force_nw <= 1'b0; test_pos <= 18'd0;
            timeout_ticks <= 16'd600; osc_trim <= 5'd16; osc_win <= 16'd0; wdt_period <= 16'hFFFF;
            ana_ctrl <= 16'd0; extrap <= 8'd0; amp_lim <= 16'h7C08; ovs_lim <= 16'h4000;
            ofs_sin <= 12'd0; ofs_cos <= 12'd0; gain <= 16'h4000; ph_sin <= 16'd0; ph_icos <= 16'h4000;
            h3 <= 16'd0; zero_ofs <= 16'd0; pos_cfg <= {5'd11, 4'd2, 1'b0}; cal_crc <= 8'd0;
            period <= 16'd0; duty_a <= 16'd0; duty_b <= 16'd0; duty_c <= 16'd0;
            phase_a <= 16'd0; phase_b <= 16'd0; phase_c <= 16'd0; dead <= 8'd15;
            sched <= {8'd32, 8'd30}; ot_lim <= 16'hFFFF; i2t_cfg <= 16'h0000; i2t_lim <= 16'hFFFF;
            i_zero <= 12'd0; t2f_win <= 4'd15; raw_cos_hold <= 12'h800;
        end else begin
            clr_pulse <= 1'b0;
            osc_arm   <= 1'b0;
            if (rd && addr == 7'h1D) raw_cos_hold <= raw_cos;     // pair snapshot
            if (wr) case (addr)
                7'h03: fault_mask <= wdata[12:0];
                7'h04: begin clr_pulse <= wdata[0]; gate_en <= wdata[1]; wdt_en <= wdata[2]; end
                7'h05: begin st_len <= wdata[4:0]; mt_en <= wdata[5]; ssi_mode <= wdata[6]; gray <= wdata[7];
                             as_mode <= wdata[8]; test_pos_en <= wdata[9]; force_ne <= wdata[10];
                             force_nw <= wdata[11]; test_pos[17:16] <= wdata[13:12]; end
                7'h06: test_pos[15:0] <= wdata;
                7'h07: timeout_ticks <= wdata;
                7'h08: begin osc_trim <= wdata[4:0]; osc_arm <= wdata[8]; end
                7'h0A: osc_win <= wdata;
                7'h0B: wdt_period <= wdata;
                7'h0C: ana_ctrl <= wdata;
                7'h0D: extrap <= wdata[7:0];
                7'h0E: amp_lim <= wdata;
                7'h0F: ovs_lim <= wdata;
                7'h10: ofs_sin <= wdata[11:0];
                7'h11: ofs_cos <= wdata[11:0];
                7'h12: gain <= wdata;
                7'h13: ph_sin <= wdata;
                7'h14: ph_icos <= wdata;
                7'h15: h3 <= wdata;
                7'h16: zero_ofs <= wdata;
                7'h17: pos_cfg <= wdata[9:0];
                7'h18: cal_crc <= wdata[7:0];
                7'h20: period <= wdata;
                7'h21: duty_a <= wdata;
                7'h22: duty_b <= wdata;
                7'h23: duty_c <= wdata;
                7'h24: phase_a <= wdata;
                7'h25: phase_b <= wdata;
                7'h26: phase_c <= wdata;
                7'h27: dead <= wdata[7:0];
                7'h28: sched <= wdata;
                7'h2C: ot_lim <= wdata;
                7'h2D: i2t_cfg <= wdata;
                7'h2E: i2t_lim <= wdata;
                7'h2F: i_zero <= wdata[11:0];
                7'h34: t2f_win <= wdata[3:0];
                default: ;
            endcase
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
    wire cal_wr = wr && (addr >= 7'h10) && (addr <= 7'h18);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cbyte <= 4'd0; crc <= 8'hFF; dirty <= 1'b1; cal_valid <= 1'b0;
        end else begin
            crc   <= crc_n;
            cbyte <= cbyte + 4'd1;
            if (cal_wr) begin
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
            7'h05: rdata = {2'd0, test_pos[17:16], force_nw, force_ne, test_pos_en, as_mode,
                            gray, ssi_mode, mt_en, st_len};
            7'h06: rdata = test_pos[15:0];
            7'h07: rdata = timeout_ticks;
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
            7'h2B: rdata = temp;
            7'h2C: rdata = ot_lim;
            7'h2D: rdata = i2t_cfg;
            7'h2E: rdata = i2t_lim;
            7'h2F: rdata = {4'd0, i_zero};
            7'h30: rdata = e_a;
            7'h31: rdata = e_b;
            7'h32: rdata = {biss_cc_err, biss_frames};
            7'h33: rdata = {pos_ovr, spi_err};
            7'h34: rdata = {12'd0, t2f_win};
            7'h35: rdata = {8'd0, late_cnt};
            default: rdata = addr[6] ? {8'd0, id_byte} : 16'd0;
        endcase
    end
endmodule
