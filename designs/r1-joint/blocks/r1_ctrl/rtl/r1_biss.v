// R1_CTRL / r1_bus: BiSS-C (Rev D2, point-to-point sensor slave) and SSI slave
// on the shared MA/SLO pads.
//
// Clock domains
//   ma   : frame shift logic, clocked by the MA pad (rising edge drives SLO).
//   clk  : timeout, latch handshake, frame data, control channel (CDM/CDS).
// Crossings
//   ma -> clk : lat_tog (toggle at LAT), ma_tog (toggle per MA rising edge) and
//               the MA level, each through r1_sync2.
//   clk -> ma : rdy_tog through a negedge/posedge pair of MA flops; frame data
//               (fw, nbits, cds) are held stable by the handshake (written by clk
//               before rdy_tog changes, read by ma after it sees the change).
//   clk -> ma reset : ma_rst_n (registered in clk, plus the CS_N pad and rst_n,
//               assert-only paths); released only while MA is quiet.
// Frame (BiSS): idle 1, LAT = first rising MA edge after a falling edge, ACK 0 at
// the next rising edge, busy 0 until the handshake completes, START 1, CDS, data
// MSB first ([MT16] ST nE nW), CRC-6 0x43 start 0 inverted, then 0 until the
// timeout ends, then 1. CDM = inverted MA level at the end of the timeout.
// Frame (SSI): first falling edge freezes the published word, data MSB first from
// the first rising edge, then 0 for the monoflop time (= TIMEOUT_TICKS), then 1.
// SPDX-License-Identifier: Apache-2.0

module r1_biss #(
    parameter [15:0] PROFILE_ID = 16'h0001,      // placeholder, see R1_REGISTER_MAP.md 6
    parameter [47:0] DEV_ID     = 48'h52_31_4A_46_45_30, // "R1JFE0"
    parameter [31:0] DEV_SN     = 32'h0000_0000,
    parameter [15:0] MFR_ID     = 16'h0000       // not assigned yet (spec open item 5)
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ma,             // MA/SCLK pad (level-shifted)
    input  wire        cs_n,           // CS_N pad: low = SPI owns the pads
    output wire        slo,
    // configuration (clk domain, quasi-static)
    input  wire        ssi_mode,
    input  wire        gray,
    input  wire        mt_en,
    input  wire [4:0]  st_len,         // 10..18 single-turn bits
    input  wire [15:0] timeout_ticks,
    // frame content (clk domain)
    input  wire [17:0] pos,            // extrapolated position, 16.2
    input  wire [15:0] turns,
    input  wire        err,            // -> nE = 0
    input  wire        warn,           // -> nW = 0
    input  wire        null_val,       // position invalid: data all 0, nE = 0
    // events (clk domain)
    output reg         frame_end,      // pulse at the end of a frame timeout
    output reg         lat_seen,       // pulse when a BiSS LAT has been captured
    output reg  [7:0]  cc_err_cnt,     // control-channel CRC / format errors
    output reg  [7:0]  frame_cnt
);
    // =====================================================================
    // clk domain: activity, timeout, arming, reset of the ma domain
    // =====================================================================
    wire ma_s, mtog_s, ltog_s;
    reg  ma_tog, lat_tog;               // ma domain, defined below
    r1_sync2 #(.W(1), .RST_VAL(1)) u_sma (.clk(clk), .rst_n(rst_n), .d(ma),      .q(ma_s));
    r1_sync2 #(.W(1))             u_smt (.clk(clk), .rst_n(rst_n), .d(ma_tog),  .q(mtog_s));
    r1_sync2 #(.W(1))             u_slt (.clk(clk), .rst_n(rst_n), .d(lat_tog), .q(ltog_s));
    wire cs_s;
    r1_sync2 #(.W(1), .RST_VAL(1)) u_scs (.clk(clk), .rst_n(rst_n), .d(cs_n), .q(cs_s));

    reg        ma_d, mtog_d, ltog_d;
    reg [15:0] idle_cnt;
    reg        armed, frame_act;
    reg [1:0]  to_rst;                  // reset pulse for the ma domain
    reg        cdm, cdm_stb;
    wire activity = (ma_s != ma_d) | (mtog_s != mtog_d);
    wire to_hit = (idle_cnt == timeout_ticks);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ma_d <= 1'b1; mtog_d <= 1'b0; idle_cnt <= 16'd0;
            armed <= 1'b0; frame_act <= 1'b0; to_rst <= 2'b00;
            cdm <= 1'b0; cdm_stb <= 1'b0; frame_end <= 1'b0; frame_cnt <= 8'd0;
        end else begin
            ma_d <= ma_s; mtog_d <= mtog_s;
            cdm_stb <= 1'b0; frame_end <= 1'b0;
            to_rst <= {to_rst[0], 1'b0};
            if (!cs_s) begin
                idle_cnt <= 16'd0; armed <= 1'b0; frame_act <= 1'b0;
            end else if (activity) begin
                idle_cnt <= 16'd0;
                if (armed) frame_act <= 1'b1;
            end else if (!to_hit) begin
                idle_cnt <= idle_cnt + 16'd1;
            end else begin
                // MA quiet for TIMEOUT_TICKS
                if (!armed) armed <= 1'b1;
                if (frame_act) begin
                    frame_act <= 1'b0;
                    to_rst    <= 2'b11;
                    cdm       <= ~ma_s;           // CDM is sent inverted on MA
                    cdm_stb   <= ~ssi_mode;
                    frame_end <= 1'b1;
                    frame_cnt <= frame_cnt + 8'd1;
                end
            end
        end
    end
    // assert-only combination: cs_n low (SPI) or rst_n low or not armed or timeout pulse
    wire ma_rst_n = rst_n & cs_n & armed & ~to_rst[1];

    // =====================================================================
    // clk domain: latch handshake and frame data
    // =====================================================================
    reg        rdy_tog;
    reg [35:0] fw;                      // left-aligned frame data (without CRC)
    reg [5:0]  nbits;
    reg        cds_cur;                 // CDS of the next frame
    reg        cds_frame;               // CDS frozen for the current frame
    reg [33:0] ssi_w;                   // published SSI word, left-aligned
    reg [5:0]  ssi_n;

    wire [5:0]  st_n   = (st_len < 5'd10) ? 6'd10 : (st_len > 5'd18) ? 6'd18 : {1'b0, st_len};
    wire [17:0] st_v   = null_val ? 18'd0 : pos;            // MSB-aligned single turn
    wire [15:0] mt_v   = null_val ? 16'd0 : turns;
    wire        ne     = ~(err | null_val);
    wire        nw     = ~warn;
    // right-aligned words, then left-aligned for MSB-first shifting
    wire [17:0] st_sh  = st_v >> (6'd18 - st_n);             // top st_n bits
    wire [5:0]  n_bss  = (mt_en ? 6'd16 : 6'd0) + st_n + 6'd2;
    wire [5:0]  n_ssi  = (mt_en ? 6'd16 : 6'd0) + st_n;
    wire [35:0] rw_b   = ((mt_en ? {20'd0, mt_v} : 36'd0) << (st_n + 6'd2)) |
                         ({18'd0, st_sh} << 2) | {34'd0, ne, nw};
    wire [33:0] rw_s   = ((mt_en ? {18'd0, mt_v} : 34'd0) << st_n) | {16'd0, st_sh};
    wire [35:0] fw_n   = rw_b << (6'd36 - n_bss);
    wire [33:0] sw_bin = rw_s << (6'd34 - n_ssi);
    wire [33:0] sw_g   = gray ? (sw_bin ^ (sw_bin >> 1)) : sw_bin;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ltog_d <= 1'b0; rdy_tog <= 1'b0; fw <= 36'd0; nbits <= 6'd0; cds_frame <= 1'b0;
            lat_seen <= 1'b0; ssi_w <= 34'd0; ssi_n <= 6'd0;
        end else begin
            ltog_d   <= ltog_s;
            lat_seen <= 1'b0;
            if (ltog_s != ltog_d) begin
                fw        <= fw_n;
                nbits     <= n_bss;
                cds_frame <= cds_cur;
                rdy_tog   <= ltog_s;
                lat_seen  <= 1'b1;
            end
            // SSI: publish while MA is idle high and no frame is running
            if (ma_s && !frame_act) begin
                ssi_w <= sw_g;
                ssi_n <= n_ssi;
            end
        end
    end

    // =====================================================================
    // ma domain: frame shift logic
    // =====================================================================
    localparam M_IDLE = 3'd0, M_ACK = 3'd1, M_BUSY = 3'd2, M_CDS = 3'd3, M_DATA = 3'd4,
               M_CRC = 3'd5, M_STOP = 3'd6, M_SSI = 3'd7;
    reg [2:0]  mst;
    reg [35:0] sh;
    reg [5:0]  mcnt;
    reg [5:0]  crc;
    reg        slo_q;
    reg        fall_seen;
    reg        rdy_n1, rdy_p2;          // clk -> ma synchroniser (negedge, then posedge)

    always @(negedge ma or negedge ma_rst_n) begin
        if (!ma_rst_n) begin fall_seen <= 1'b0; rdy_n1 <= 1'b0; end
        else begin fall_seen <= 1'b1; rdy_n1 <= rdy_tog; end
    end
    // ma_tog and lat_tog survive the frame reset (only rst_n clears them)
    always @(posedge ma or negedge rst_n) begin
        if (!rst_n) ma_tog <= 1'b0;
        else        ma_tog <= ~ma_tog;
    end

    wire [5:0] crc_nx = {crc[4:0], 1'b0} ^ ((crc[5] ^ sh[35]) ? 6'h03 : 6'h00);

    always @(posedge ma or negedge ma_rst_n) begin
        if (!ma_rst_n) begin
            mst <= M_IDLE; sh <= 36'd0; mcnt <= 6'd0; crc <= 6'd0; slo_q <= 1'b1; rdy_p2 <= 1'b0;
        end else begin
            rdy_p2 <= rdy_n1;
            case (mst)
                M_IDLE: if (fall_seen) begin
                    if (ssi_mode) begin
                        sh    <= {ssi_w, 2'b00};
                        slo_q <= ssi_w[33];
                        mcnt  <= ssi_n - 6'd1;
                        mst   <= M_SSI;
                    end else begin
                        mst   <= M_ACK;      // this edge is LAT (lat_tog toggled below)
                    end
                end
                M_ACK:  begin slo_q <= 1'b0; mst <= M_BUSY; end
                M_BUSY: if (rdy_p2 == lat_tog) begin
                    slo_q <= 1'b1;           // START
                    sh    <= fw;
                    mcnt  <= nbits;
                    crc   <= 6'd0;
                    mst   <= M_CDS;
                end
                M_CDS:  begin slo_q <= cds_frame; mst <= M_DATA; end
                M_DATA: begin
                    slo_q <= sh[35];
                    crc   <= crc_nx;
                    sh    <= {sh[34:0], 1'b0};
                    mcnt  <= mcnt - 6'd1;
                    if (mcnt == 6'd1) begin mcnt <= 6'd6; mst <= M_CRC; end
                end
                M_CRC:  begin
                    slo_q <= ~crc[5];
                    crc   <= {crc[4:0], 1'b0};
                    mcnt  <= mcnt - 6'd1;
                    if (mcnt == 6'd1) mst <= M_STOP;
                end
                M_STOP: slo_q <= 1'b0;
                M_SSI:  begin
                    if (mcnt != 6'd0) begin
                        slo_q <= sh[34];
                        sh    <= {sh[34:0], 1'b0};
                        mcnt  <= mcnt - 6'd1;
                    end else slo_q <= 1'b0;      // monoflop: low until the timeout
                end
                default: mst <= M_IDLE;
            endcase
        end
    end
    // LAT toggle: separate flop so the frame reset does not clear it
    always @(posedge ma or negedge rst_n) begin
        if (!rst_n) lat_tog <= 1'b0;
        else if (mst == M_IDLE && fall_seen && !ssi_mode) lat_tog <= ~lat_tog;
    end
    // SLO reads 0 (busy) until the slave is armed (after reset and after SPI use),
    // so a master does not start a frame that would be ignored
    assign slo = slo_q & armed;

    // =====================================================================
    // clk domain: control channel (register read of 0x40-0x7F over CDM/CDS)
    //   CDM: S CTS ID[2:0] ADR[6:0] CRC4[3:0](inverted, over ID+ADR) R W S
    //   CDS (following frames): S D[7:0] CRC4[3:0](inverted, over D) then 0
    //   14 consecutive CDM = 0 reset the channel.
    // =====================================================================
    localparam C_IDLE = 2'd0, C_RX = 2'd1, C_TX = 2'd2;
    reg [1:0]  cst;
    reg [4:0]  ccnt;
    reg [17:0] crx;                    // CTS ID ADR CRC R W S
    reg [12:0] ctx;                    // S D CRC
    reg [3:0]  zcnt;

    function [3:0] crc4_step;
        input [3:0] c; input b;
        begin crc4_step = {c[2:0], 1'b0} ^ ((c[3] ^ b) ? 4'h3 : 4'h0); end
    endfunction
    function [3:0] crc4_10;
        input [9:0] d;
        integer i;
        reg [3:0] c;
        begin c = 4'd0; for (i = 9; i >= 0; i = i - 1) c = crc4_step(c, d[i]); crc4_10 = c; end
    endfunction
    function [3:0] crc4_8;
        input [7:0] d;
        integer i;
        reg [3:0] c;
        begin c = 4'd0; for (i = 7; i >= 0; i = i - 1) c = crc4_step(c, d[i]); crc4_8 = c; end
    endfunction

    // received word after the 18th bit: crx[17]=CTS crx[16:14]=ID crx[13:7]=ADR crx[6:3]=CRC crx[2]=R crx[1]=W crx[0]=S
    wire [17:0] crx_n   = {crx[16:0], cdm};
    wire [6:0]  rx_adr  = crx_n[13:7];
    wire        rx_ok   = crx_n[17] && (crx_n[16:14] == 3'd0) &&
                          (crx_n[6:3] == ~crc4_10(crx_n[16:7])) &&
                          crx_n[2] && !crx_n[1] && crx_n[0] && rx_adr[6];
    wire [7:0]  rd_byte;
    r1_idrom #(.PROFILE_ID(PROFILE_ID), .DEV_ID(DEV_ID), .DEV_SN(DEV_SN), .MFR_ID(MFR_ID))
        u_rom (.addr(rx_adr), .data(rd_byte));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cst <= C_IDLE; ccnt <= 5'd0; crx <= 18'd0; ctx <= 13'd0; zcnt <= 4'd0;
            cds_cur <= 1'b0; cc_err_cnt <= 8'd0;
        end else if (cdm_stb) begin
            if (cdm) zcnt <= 4'd0; else if (zcnt != 4'd14) zcnt <= zcnt + 4'd1;
            if (!cdm && zcnt == 4'd13) begin
                cst <= C_IDLE; cds_cur <= 1'b0;          // 14 x CDM = 0: reset
            end else case (cst)
                C_IDLE: begin
                    cds_cur <= 1'b0;
                    if (cdm) begin cst <= C_RX; ccnt <= 5'd0; end
                end
                C_RX: begin
                    crx  <= crx_n;
                    ccnt <= ccnt + 5'd1;
                    if (ccnt == 5'd17) begin
                        if (rx_ok) begin
                            ctx     <= {rd_byte, ~crc4_8(rd_byte), 1'b0};
                            cds_cur <= 1'b1;            // slave start bit
                            ccnt    <= 5'd0;
                            cst     <= C_TX;
                        end else begin
                            cc_err_cnt <= cc_err_cnt + 8'd1;
                            cst <= C_IDLE;
                        end
                    end
                end
                C_TX: begin
                    cds_cur <= ctx[12];
                    ctx     <= {ctx[11:0], 1'b0};
                    ccnt    <= ccnt + 5'd1;
                    if (ccnt == 5'd12) cst <= C_IDLE;
                end
                default: cst <= C_IDLE;
            endcase
        end
    end
endmodule
