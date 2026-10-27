// R1_CTRL: register file (R1_REGISTER_MAP.md revision 0.3), read multiplexer
// and the calibration CRC checker.
// Revision 0.2: host-written configuration words are latch words (r1_cword,
// see r1_lib.v); only registers with self-clearing bits (CTRL, OSC_CFG.MEAS)
// and the RAW_COS snapshot are flip-flops. A write takes effect one tick later
// than in revision 0.1 (the gated latch opens in the cycle after the write
// pulse). Only the bits listed in the map are stored; other bits read 0.
// Calibration CRC (revision 0.3): CRC-8, polynomial 0x07, initial 0xFF, no
// reflection, no final XOR, over the 43 covered words as they read back, high
// byte first, in this order: 0x10..0x17 (position calibration), 0x36..0x3C
// (comparator thresholds, AZ_START, AZ_CFG, CMP_CAL_A/B, CMP_CAL_IDEAL),
// 0x50..0x5D (slice A ADC weights), 0x60..0x6D (slice B ADC weights, D18).
// A byte-serial engine walks the 86 bytes continuously; CAL_VALID = (result ==
// CAL_CRC) at the end of a pass. A write to a covered word or to CAL_CRC, and a
// comparator calibration search (cal_busy), clear CAL_VALID until the next
// complete pass (<= 2 x 86 ticks plus the SPI pauses).
// Revision 0.2 covered 0x10..0x17 only.
// Revision 0.7: CMP_THR_A/B reset 0x003F (THR_OC 63, THR_NEG 0: both cells at the
// least-sensitive code 63, r1_top finding R4); AZ_EXT (0x3E) comparator mask after
// az_win, reset 120 ticks (INTERFACES.md "vref_b disturbance"); OSC_TRIM lock
// (PLAN.md D13 amendment): a write that changes OSC_TRIM to a code below 18 is ignored
// unless TRIM_UNLK is set. TRIM_UNLK is set by an SPI read of OSC_COUNT that returns a
// completed count inside OSC_WIN (osc_meas_ok, from the top level) and cleared by every
// accepted write that changes OSC_TRIM.
// Revision 0.8 (PLAN.md D22): COS_GAIN (0x3F, Q2.14, reset 0x4000 = 1.0), the cosine
// channel gain (GAIN 0x12 is now named SIN_GAIN; OFS_SIN/OFS_COS are named SIN_OFS/COS_OFS);
// COS_GAIN is CRC-covered as the 44th word, after 0x6D. Raw-code capture for the host
// calibration: RAW_SIN_MIN/MAX (0x5E/0x5F), RAW_COS_MIN/MAX (0x6E/0x6F), the minimum and
// maximum of the weight-corrected encoder codes (the RAW_SIN/RAW_COS values) of every
// encoder pair (smp_valid); a write of any value to any of the four clears all four
// (MIN 0xFFF, MAX 0x000, = reset; MIN > MAX means no pair since the clear).
// SPDX-License-Identifier: Apache-2.0

module r1_regs #(
    parameter [15:0] CHIP_ID = 16'h5208
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        wr,
    input  wire [6:0]  addr,
    input  wire [15:0] wdata,
    input  wire        rd,             // read strobe (side effects)
    input  wire        rd_sel,         // SPI owns the read multiplexer (r1_spi)
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
    input  wire        smp_valid,      // 0.8: raw_sin / raw_cos hold a new encoder pair in this tick
    input  wire [17:0] meas_angle,
    input  wire [11:0] i_a, i_b,
    input  wire [13:0] temp,
    input  wire [15:0] e_a, e_b,
    input  wire [7:0]  biss_frames,
    input  wire [3:0]  biss_cc_err, spi_err, pos_ovr, late_cnt,   // saturating
    input  wire [7:0]  id_byte,        // BiSS ID ROM byte for addr 0x40..0x47, 0x78..0x7F
    input  wire [15:0] cmp_cal_a,      // CMP_CAL_A / _B read values (r1_cmpcal)
    input  wire [15:0] cmp_cal_b,
    input  wire        cal_busy,       // comparator calibration search running (r1_cmpcal)
    input  wire        osc_meas_ok,    // 0.7: OSC_DONE, OSC_WIN != 0 and the count inside OSC_WIN
    output reg         trim_unlk,      // 0.7: STATUS.TRIM_UNLK, codes below 18 accepted
    output wire [7:0]  az_ext,         // 0.7: AZ_EXT, comparator mask ticks after az_win
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
    output wire [3:0]  adc_disc,       // ADC_CFG[3:0]: conversions to discard after ADC arm (0.5)
    output wire [7:0]  extrap,
    output wire [15:0] amp_lim,
    output wire [15:0] ovs_lim,
    output wire [11:0] ofs_sin, ofs_cos,
    output wire [15:0] gain, ph_sin, ph_icos,
    output wire [15:0] cos_gain,       // 0.8: COS_GAIN (0x3F)
    output wire [15:0] h3,
    output wire [15:0] zero_ofs,
    output wire [9:0]  pos_cfg,
    output wire [7:0]  cal_crc,
    output reg         cal_valid,
    output wire [12:0] period, duty_a, duty_b, duty_c, phase_a, phase_b, phase_c,
    output wire [7:0]  dead,
    output wire [15:0] sched,
    output wire [13:0] ot_lim,
    output wire [11:0] i2t_cfg,
    output wire [15:0] i2t_lim,
    output wire [11:0] i_zero,
    output wire [3:0]  t2f_win,
    output wire [13:0] cmp_thr_a,      // [5:0] THR_OC_A, [13:8] THR_NEG_A
    output wire [13:0] cmp_thr_b,
    output wire [12:0] az_start,
    output wire [15:0] az_cfg,         // [7:0] AZ_LEN, [13:8] THR_ZERO, [15:14] CAL_STEP
    output wire [6:0]  ideal_oc,       // CMP_CAL_IDEAL [6:0]
    output wire [6:0]  ideal_neg,      // CMP_CAL_IDEAL [14:8]
    output wire        cmp_cal_wr_a,   // host write of CMP_CAL_A / _B (data = wdata)
    output wire        cmp_cal_wr_b,
    output wire [195:0] adc_wa,        // slice A: 14 x 14-bit ADC weights, w[i] at [14*i +: 14] (D18)
    output wire [195:0] adc_wb         // slice B
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
    // 0.7: OSC_TRIM lock. A write is accepted if the code does not change, is 18 or above, or TRIM_UNLK is set.
    // A refused write rewrites the present code (data select, not a gated enable: run t13 gated the clock-gate
    // enable with trim_ok, which depends on the word's own outputs, and failed the clock-gating setup check).
    wire trim_chg = (wdata[4:0] != osc_trim);
    wire trim_ok  = !trim_chg || (wdata[4:0] >= 5'd18) || trim_unlk;
    wire [4:0] trim_d = trim_ok ? wdata[4:0] : osc_trim;
    r1_cword #(.W(5),  .RV(5'd22),  .A(7'h08)) u_08 (clk, rst_n, wr, addr, trim_d, osc_trim);
    r1_cword #(.W(16), .A(7'h0A)) u_0a (clk, rst_n, wr, addr, wdata, osc_win);
    r1_cword #(.W(16), .RV(16'hFFFF), .A(7'h0B)) u_0b (clk, rst_n, wr, addr, wdata, wdt_period);
    // 0.5: ANA_CTRL reset 0x0028 = T2F_EN 1, BIAS_EN 1 (bit meaning: register map 4.8)
    r1_cword #(.W(16), .RV(16'h0028), .A(7'h0C)) u_0c (clk, rst_n, wr, addr, wdata, ana_ctrl);
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
    r1_cword #(.W(13), .A(7'h20)) u_20 (clk, rst_n, wr, addr, wdata[12:0], period);
    r1_cword #(.W(13), .A(7'h21)) u_21 (clk, rst_n, wr, addr, wdata[12:0], duty_a);
    r1_cword #(.W(13), .A(7'h22)) u_22 (clk, rst_n, wr, addr, wdata[12:0], duty_b);
    r1_cword #(.W(13), .A(7'h23)) u_23 (clk, rst_n, wr, addr, wdata[12:0], duty_c);
    r1_cword #(.W(13), .A(7'h24)) u_24 (clk, rst_n, wr, addr, wdata[12:0], phase_a);
    r1_cword #(.W(13), .A(7'h25)) u_25 (clk, rst_n, wr, addr, wdata[12:0], phase_b);
    r1_cword #(.W(13), .A(7'h26)) u_26 (clk, rst_n, wr, addr, wdata[12:0], phase_c);
    r1_cword #(.W(8),  .RV(8'd15), .A(7'h27)) u_27 (clk, rst_n, wr, addr, wdata[7:0], dead);
    r1_cword #(.W(16), .RV(16'h1416), .A(7'h28)) u_28 (clk, rst_n, wr, addr, wdata, sched);
    r1_cword #(.W(14), .RV(14'h3FFF), .A(7'h2C)) u_2c (clk, rst_n, wr, addr, wdata[13:0], ot_lim);
    r1_cword #(.W(12), .A(7'h2D)) u_2d (clk, rst_n, wr, addr, wdata[11:0], i2t_cfg);
    r1_cword #(.W(16), .RV(16'hFFFF), .A(7'h2E)) u_2e (clk, rst_n, wr, addr, wdata, i2t_lim);
    r1_cword #(.W(12), .A(7'h2F)) u_2f (clk, rst_n, wr, addr, wdata[11:0], i_zero);
    r1_cword #(.W(4),  .RV(4'd15), .A(7'h34)) u_34 (clk, rst_n, wr, addr, wdata[3:0], t2f_win);
    wire [11:0] thr_w = {wdata[13:8], wdata[5:0]};
    wire [11:0] thr_a, thr_b;
    // 0.7: reset THR_NEG 0, THR_OC 63 = cell code 63 for both cells (was 0x3F3F: NEG cell code 0 tripped at zero current)
    r1_cword #(.W(12), .RV(12'h03F), .A(7'h36)) u_36 (clk, rst_n, wr, addr, thr_w, thr_a);
    r1_cword #(.W(12), .RV(12'h03F), .A(7'h37)) u_37 (clk, rst_n, wr, addr, thr_w, thr_b);
    assign cmp_thr_a = {thr_a[11:6], 2'b00, thr_a[5:0]};
    assign cmp_thr_b = {thr_b[11:6], 2'b00, thr_b[5:0]};
    r1_cword #(.W(13), .A(7'h38)) u_38 (clk, rst_n, wr, addr, wdata[12:0], az_start);
    // AZ_CFG reset: THR_ZERO 14 (r1_safe contract), CAL_STEP 1 (32 ticks)
    r1_cword #(.W(16), .RV(16'h4E00), .A(7'h39)) u_39 (clk, rst_n, wr, addr, wdata, az_cfg);
    // CMP_CAL_IDEAL: 2 x k_ideal (half codes), reset 72 (OC, 36.31) and 55 (NEG, 27.69)
    wire [13:0] ideal_w;
    r1_cword #(.W(14), .RV({7'd55, 7'd72}), .A(7'h3C)) u_3c (clk, rst_n, wr, addr, {wdata[14:8], wdata[6:0]}, ideal_w);
    assign ideal_oc = ideal_w[6:0];
    assign ideal_neg = ideal_w[13:7];
    // 0.5: ADC_CFG (0x3D), DISCARD in bits 3:0, reset 1; not covered by CAL_CRC
    r1_cword #(.W(4), .RV(4'd1), .A(7'h3D)) u_3d (clk, rst_n, wr, addr, wdata[3:0], adc_disc);
    // 0.7: AZ_EXT (0x3E), [7:0] comparator mask after az_win in ticks, reset 120 (4 us at 30 MHz); not covered by CAL_CRC
    r1_cword #(.W(8), .RV(8'd120), .A(7'h3E)) u_3e (clk, rst_n, wr, addr, wdata[7:0], az_ext);
    // 0.8: COS_GAIN (0x3F), Q2.14, reset 1.0; CRC-covered (word 43)
    r1_cword #(.W(16), .RV(16'h4000), .A(7'h3F)) u_3f (clk, rst_n, wr, addr, wdata, cos_gain);
    assign cmp_cal_wr_a = wr && (addr == 7'h3A);
    assign cmp_cal_wr_b = wr && (addr == 7'h3B);

    // ADC weights (D12, D18): slice A 0x50 + i, slice B 0x60 + i, i = 0..13
    // (decision i, raw[13] first), 14 bit, units of 1/4 LSB. Reset = nominal
    // r1_adc revision-3 weights x 4 (2032.4 .. 0.31 LSB; sum 16380 = 4095 LSB).
    localparam [195:0] WNOM = {14'd8130, 14'd4065, 14'd2032, 14'd1016, 14'd508, 14'd315, 14'd158,
                               14'd79,   14'd39,   14'd20,   14'd10,   14'd5,   14'd2,   14'd1};
    // Revision 0.4: stored width per weight = bit length of the nominal weight + 2 (4 x headroom
    // over the nominal value, so a 1/8-LSB unit still fits with 2 x spare), at most 14 bit:
    // W0..W13 = 3 4 5 6 7 8 9 10 11 11 12 13 14 14 bits. Higher bits read 0 and ignore writes.
    function integer wwid;
        input integer i;
        begin
            case (i)
                0: wwid = 3;   1: wwid = 4;   2: wwid = 5;   3: wwid = 6;
                4: wwid = 7;   5: wwid = 8;   6: wwid = 9;   7: wwid = 10;
                8: wwid = 11;  9: wwid = 11;  10: wwid = 12; 11: wwid = 13;
                default: wwid = 14;
            endcase
        end
    endfunction
    genvar gi;
    generate
        for (gi = 0; gi < 14; gi = gi + 1) begin : g_w
            localparam integer WW = wwid(gi);
            wire [WW-1:0] qa, qb;
            r1_cword #(.W(WW), .RV(WNOM[14*gi +: WW]), .A(7'h50 + gi)) u_wa (clk, rst_n, wr, addr, wdata[WW-1:0], qa);
            r1_cword #(.W(WW), .RV(WNOM[14*gi +: WW]), .A(7'h60 + gi)) u_wb (clk, rst_n, wr, addr, wdata[WW-1:0], qb);
            assign adc_wa[14*gi +: 14] = {{(14-WW){1'b0}}, qa};
            assign adc_wb[14*gi +: 14] = {{(14-WW){1'b0}}, qb};
        end
    endgenerate

    // ---------------- flip-flop registers ----------------
    reg [11:0] raw_cos_hold;
    reg        trim_wr_d;
    // 0.8: raw-code capture (D22); cleared by a write to 0x5E, 0x5F, 0x6E or 0x6F
    reg [11:0] sin_min, sin_max, cos_min, cos_max;
    wire       mm_clr = wr && ((addr[6:1] == 6'b101111) || (addr[6:1] == 6'b110111));   // 0x5E/0x5F, 0x6E/0x6F
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clr_pulse <= 1'b0; osc_arm <= 1'b0; cal_run <= 1'b0; gate_en <= 1'b0; wdt_en <= 1'b0;
            raw_cos_hold <= 12'h800; trim_unlk <= 1'b0; trim_wr_d <= 1'b0;
            sin_min <= 12'hFFF; sin_max <= 12'h000; cos_min <= 12'hFFF; cos_max <= 12'h000;
        end else begin
            if (mm_clr) begin
                sin_min <= 12'hFFF; sin_max <= 12'h000; cos_min <= 12'hFFF; cos_max <= 12'h000;
            end else if (smp_valid) begin
                if (raw_sin < sin_min) sin_min <= raw_sin;
                if (raw_sin > sin_max) sin_max <= raw_sin;
                if (raw_cos < cos_min) cos_min <= raw_cos;
                if (raw_cos > cos_max) cos_max <= raw_cos;
            end
            clr_pulse <= 1'b0;
            osc_arm   <= 1'b0;
            cal_run   <= 1'b0;
            if (rd && addr == 7'h1D) raw_cos_hold <= raw_cos;     // pair snapshot
            if (wr && addr == 7'h04) begin
                clr_pulse <= wdata[0]; gate_en <= wdata[1]; wdt_en <= wdata[2]; cal_run <= wdata[3];
            end
            if (wr && addr == 7'h08) osc_arm <= wdata[8];
            // 0.7: OSC_TRIM lock bit (set by the OSC_COUNT read path, consumed by a trim change one tick after
            // the write edge, so the word on its gated clock samples trim_d with the old TRIM_UNLK)
            trim_wr_d <= wr && addr == 7'h08 && trim_ok && trim_chg;
            if (trim_wr_d)                                trim_unlk <= 1'b0;
            else if (rd && addr == 7'h09 && osc_meas_ok)  trim_unlk <= 1'b1;
        end
    end

    // ---------------- calibration CRC ----------------
    // revision 0.3: the CRC engine reads the covered words through the read
    // multiplexer (maddr). The SPI owns it only in the two ticks in which it
    // decodes a frame (rd_sel); the engine then holds its position and state.
    reg  [5:0]  cw;                    // covered word 0..43 (0.8: 43 = COS_GAIN 0x3F)
    reg         chalf;                 // 0: high byte, 1: low byte
    reg  [7:0]  crc;
    reg         dirty;
    wire [6:0]  caddr = (cw < 6'd8)  ? 7'h10 + {1'd0, cw} :
                        (cw < 6'd15) ? 7'h36 + {1'd0, cw - 6'd8} :
                        (cw < 6'd29) ? 7'h50 + {1'd0, cw - 6'd15} :
                        (cw < 6'd43) ? 7'h60 + {1'd0, cw - 6'd29} : 7'h3F;
    wire [6:0]  maddr = rd_sel ? addr : caddr;
    wire [15:0] cv = rdata;
    wire [7:0] cb = chalf ? cv[7:0] : cv[15:8];
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
    wire       first = (cw == 6'd0) && !chalf;
    wire       last  = (cw == 6'd43) && chalf;
    wire [7:0] crc_n = crc8_byte(first ? 8'hFF : crc, cb);
    wire       adv   = !rd_sel;
    // the latch word changes in the tick after the write pulse; a write marks the
    // pass dirty in both ticks so no pass mixes old and new values
    reg  cal_wr_d, cal_busy_d;
    wire cal_wr = wr && (((addr >= 7'h10) && (addr <= 7'h18)) || ((addr >= 7'h36) && (addr <= 7'h3C)) ||
                         ((addr >= 7'h50) && (addr <= 7'h5D)) || ((addr >= 7'h60) && (addr <= 7'h6D)) || (addr == 7'h3F));
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cw <= 6'd0; chalf <= 1'b0; crc <= 8'hFF; dirty <= 1'b1; cal_valid <= 1'b0;
            cal_wr_d <= 1'b0; cal_busy_d <= 1'b0;
        end else begin
            if (adv) begin
                crc   <= crc_n;
                chalf <= ~chalf;
                if (chalf) cw <= last ? 6'd0 : cw + 6'd1;
            end
            cal_wr_d   <= cal_wr;
            cal_busy_d <= cal_busy;
            if (cal_wr || cal_wr_d || cal_busy || cal_busy_d) begin
                dirty <= 1'b1; cal_valid <= 1'b0;
            end else if (last && adv) begin
                if (dirty) dirty <= 1'b0;                  // a full clean pass is needed
                else cal_valid <= (crc_n == cal_crc);
            end
        end
    end

    // ---------------- read multiplexer ----------------
    // ADC weights (revision 0.4): one-hot AND-OR read, decode shared by both slices
    // (a 14-to-1 index per bit costs more than the AND-OR form)
    reg [13:0] w_or;
    reg        wsel_any;
    integer    wi;
    always @(*) begin
        w_or = 14'd0; wsel_any = 1'b0;
        for (wi = 0; wi < 14; wi = wi + 1) begin
            w_or     = w_or | ({14{maddr == 7'h50 + wi}} & adc_wa[14*wi +: 14])
                            | ({14{maddr == 7'h60 + wi}} & adc_wb[14*wi +: 14]);
            wsel_any = wsel_any | (maddr == 7'h50 + wi) | (maddr == 7'h60 + wi);
        end
    end
    always @(*) begin
        case (maddr)
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
            7'h20: rdata = {3'd0, period};
            7'h21: rdata = {3'd0, duty_a};
            7'h22: rdata = {3'd0, duty_b};
            7'h23: rdata = {3'd0, duty_c};
            7'h24: rdata = {3'd0, phase_a};
            7'h25: rdata = {3'd0, phase_b};
            7'h26: rdata = {3'd0, phase_c};
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
            7'h38: rdata = {3'd0, az_start};
            7'h39: rdata = az_cfg;
            7'h3A: rdata = cmp_cal_a;
            7'h3B: rdata = cmp_cal_b;
            7'h3C: rdata = {1'b0, ideal_neg, 1'b0, ideal_oc};
            7'h3D: rdata = {12'd0, adc_disc};
            7'h3E: rdata = {8'd0, az_ext};
            7'h3F: rdata = cos_gain;
            7'h5E: rdata = {4'd0, sin_min};
            7'h5F: rdata = {4'd0, sin_max};
            7'h6E: rdata = {4'd0, cos_min};
            7'h6F: rdata = {4'd0, cos_max};
            default: begin
                if (wsel_any) rdata = {2'd0, w_or};
                else          rdata = maddr[6] ? {8'd0, id_byte} : 16'd0;
            end
        endcase
    end
endmodule
