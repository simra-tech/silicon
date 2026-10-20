// R1_CTRL / r1_bus: SPI register access on SCLK/SDI/SDO/CS_N (pads shared with
// MA/SLO; CS_N low selects SPI).
//
// Native mode (BUS_CFG.AS_MODE = 0): SPI mode 0, 24-bit frames.
//   SDI: R/nW, A[6:0], D[15:0]     (write: D is written; read: D ignored)
//   SDO: STATUS[7:0], RD[15:0]     RD = result of the previous frame
//        (read data of a read command, echo of the written value after a write).
// AS5047P-compatible mode (AS_MODE = 1): SPI mode 1, 16-bit frames.
//   SDI: PARC, R/W(1 = read), ADDR[13:0];  SDO (next frame): PARD, EF, DATA[13:0]
//   0x3FFF ANGLECOM, 0x3FFE ANGLEUNC (both POS[15:2]), 0x3FFD MAG, 0x3FFC DIAAGC,
//   0x0001 ERRFL (read clears), 0x0000 NOP. Writes are not supported: the
//   following data frame is ignored.
// Clocking: the shift logic runs on sclk_i = SCLK ^ AS_MODE; its flops only
// update while CS_N is low, so they hold the received word after CS_N rises and
// MA traffic of a BiSS master on the same pad does not disturb them. The clk
// domain decodes the frame after CS_N rises (2-flop synchroniser) and prepares
// the next SDO word before the next CS_N fall (CS_N high time >= 8 clk ticks).
// SPDX-License-Identifier: Apache-2.0

module r1_spi (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        sclk,
    input  wire        cs_n,
    input  wire        sdi,
    output wire        sdo,
    input  wire        as_mode,
    // register file port (clk domain)
    output reg         reg_wr,
    output reg  [6:0]  reg_addr,
    output reg  [15:0] reg_wdata,
    input  wire [15:0] reg_rdata,      // combinational read of reg_addr
    output reg         reg_rd,         // pulse: a register was read (read side effects)
    input  wire [7:0]  status8,
    // AS5047P-compatible sources
    input  wire [17:0] pos,
    input  wire [11:0] amplitude,
    input  wire        amp_low,
    input  wire        amp_high,
    // events
    output reg         frame_ok,       // pulse: well-formed frame decoded
    output reg  [7:0]  err_cnt
);
    wire sclk_i = sclk ^ as_mode;

    // ---------------- SCLK domain ----------------
    reg        fresh;
    reg [23:0] rx;
    reg [5:0]  rcnt;
    reg [5:0]  oidx;
    reg [23:0] tx_word;                // clk domain, stable while CS_N is low

    always @(posedge sclk_i or posedge cs_n) begin
        if (cs_n) fresh <= 1'b1;
        else      fresh <= 1'b0;
    end
    always @(posedge sclk_i or negedge rst_n) begin
        if (!rst_n) begin
            rx <= 24'd0; rcnt <= 6'd0;
        end else if (!cs_n) begin
            if (fresh) begin
                rx <= {23'd0, sdi}; rcnt <= 6'd1;
            end else begin
                rx <= {rx[22:0], sdi};
                if (rcnt != 6'd63) rcnt <= rcnt + 6'd1;
            end
        end
    end
    always @(negedge sclk_i or posedge cs_n) begin
        if (cs_n) oidx <= 6'd0;
        else if (oidx != 6'd63) oidx <= oidx + 6'd1;
    end
    // mode 1: the first rising SCLK edge drives bit 0, so the index lags by one
    wire [5:0] bidx = (as_mode && oidx != 6'd0) ? (oidx - 6'd1) : oidx;
    assign sdo = (bidx < 6'd24) ? tx_word[5'd23 - bidx[4:0]] : 1'b0;

    // ---------------- clk domain ----------------
    wire cs_s;
    r1_sync2 #(.W(1), .RST_VAL(1)) u_scs (.clk(clk), .rst_n(rst_n), .d(cs_n), .q(cs_s));
    reg        cs_d;
    reg [1:0]  ph;                     // decode phases after CS_N rise
    reg        as_wskip;               // AS mode: next frame carries write data, ignore
    reg        as_ef;                  // AS mode: error in the previous frame
    reg [2:0]  as_errfl;               // PARERR, INVCOMM, FRERR
    reg [23:0] rx_c;
    reg [5:0]  rcnt_c;
    reg        as_rd;                  // AS mode: current frame is a valid read command

    wire as_par_ok = ~^rx_c[15:0];
    wire [13:0] as_addr = rx_c[13:0];
    reg  [13:0] as_data;
    always @(*) begin
        case (as_addr)
            14'h3FFF, 14'h3FFE: as_data = pos[17:4];
            14'h3FFD:           as_data = {amplitude, 2'b00};
            14'h3FFC:           as_data = {2'b00, amp_low, amp_high, 2'b00, 8'd0};   // MAGL, MAGH
            14'h0001:           as_data = {11'd0, as_errfl};
            default:            as_data = 14'd0;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cs_d <= 1'b1; ph <= 2'd0; tx_word <= 24'd0; reg_wr <= 1'b0; reg_rd <= 1'b0;
            reg_addr <= 7'd0; reg_wdata <= 16'd0; frame_ok <= 1'b0; err_cnt <= 8'd0;
            as_wskip <= 1'b0; as_ef <= 1'b0; as_rd <= 1'b0; as_errfl <= 3'd0; rx_c <= 24'd0; rcnt_c <= 6'd0;
        end else begin
            cs_d <= cs_s;
            reg_wr <= 1'b0; reg_rd <= 1'b0; frame_ok <= 1'b0;
            case (ph)
                2'd0: if (cs_s && !cs_d) begin
                    rx_c <= rx; rcnt_c <= rcnt;          // stable: SCLK flops hold while CS_N high
                    ph <= 2'd1;
                end
                2'd1: begin
                    ph <= 2'd2;
                    // native frames; in AS mode a 24-bit frame is also decoded as native
                    // (the way back from AS mode without a reset)
                    if (!as_mode || (rcnt_c == 6'd24 && !as_wskip)) begin
                        as_rd <= 1'b0;
                        if (rcnt_c == 6'd24) begin
                            reg_addr  <= rx_c[22:16];
                            reg_wdata <= rx_c[15:0];
                            reg_wr    <= ~rx_c[23];
                            frame_ok  <= 1'b1;
                        end else begin
                            err_cnt <= err_cnt + 8'd1;
                            ph <= 2'd3;
                        end
                    end else begin
                        as_rd <= 1'b0;
                        if (as_wskip) begin
                            as_wskip <= 1'b0;          // write data frame: answer NOP
                        end else if (rcnt_c != 6'd16 || !as_par_ok) begin
                            as_errfl <= as_errfl | {!as_par_ok && rcnt_c == 6'd16, 1'b0, rcnt_c != 6'd16};
                            as_ef <= 1'b1;
                            err_cnt <= err_cnt + 8'd1;
                            ph <= 2'd3;
                        end else begin
                            frame_ok <= 1'b1;
                            as_rd    <= rx_c[14];
                            if (!rx_c[14]) as_wskip <= 1'b1;   // write: skip the data frame
                        end
                    end
                end
                2'd2: begin
                    // reg_addr / as_addr decoded; prepare the next SDO word
                    ph <= 2'd0;
                    if (!as_mode || rcnt_c == 6'd24) begin
                        tx_word <= {status8, rx_c[23] ? reg_rdata : rx_c[15:0]};
                        reg_rd  <= rx_c[23];
                    end else begin
                        // PARD: even parity over the whole 16-bit word
                        tx_word <= {^{as_ef, (as_rd ? as_data : 14'd0)}, as_ef,
                                    (as_rd ? as_data : 14'd0), 8'd0};
                        as_ef <= 1'b0;
                        if (as_rd && as_addr == 14'h0001) as_errfl <= 3'd0;
                    end
                end
                2'd3: begin
                    // malformed or skipped frame: status only, data 0
                    ph <= 2'd0;
                    if (!as_mode) tx_word <= {status8, 16'd0};
                    else begin    tx_word <= {1'b1, 1'b1, 14'd0, 8'd0}; as_ef <= 1'b0; end
                end
            endcase
        end
    end
endmodule
