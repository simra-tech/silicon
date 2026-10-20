// R1_CTRL: read-only BiSS identification bytes in the fixed address area
// 0x40..0x7F (BiSS C Rev D2, "BiSS MEMORY MAP", Table 2; no EDS, one bank).
// Multi-byte parameters are big-endian, the highest-value byte at the lowest
// address (D2 p. 22). ok = 1 for the addresses this slave accepts for a read:
//   0x41 EDS_BANK = 0x00 (no EDS, D2 Table 5), 0x42..0x43 BP_ID, 0x44..0x47
//   DEV_SN (0 = no serial number, D2 Table 7), 0x78..0x7D DEV_ID, 0x7E..0x7F
//   MFR_ID. Refused: 0x00..0x3F (no register bank), 0x40 BSEL (one bank only:
//   "read and write access to BSEL are refused", D2 Table 4), 0x48..0x77.
// SPDX-License-Identifier: Apache-2.0

module r1_idrom #(
    parameter [15:0] PROFILE_ID = 16'h0001,
    parameter [47:0] DEV_ID     = 48'h52_31_4A_46_45_30,
    parameter [31:0] DEV_SN     = 32'h0000_0000,
    parameter [15:0] MFR_ID     = 16'h0000
) (
    input  wire [6:0] addr,
    output reg  [7:0] data,
    output wire       ok
);
    assign ok = (addr >= 7'h41 && addr <= 7'h47) || (addr >= 7'h78);
    always @(*) begin
        case (addr)
            7'h42: data = PROFILE_ID[15:8];  7'h43: data = PROFILE_ID[7:0];
            7'h44: data = DEV_SN[31:24];     7'h45: data = DEV_SN[23:16];
            7'h46: data = DEV_SN[15:8];      7'h47: data = DEV_SN[7:0];
            7'h78: data = DEV_ID[47:40];     7'h79: data = DEV_ID[39:32];
            7'h7A: data = DEV_ID[31:24];     7'h7B: data = DEV_ID[23:16];
            7'h7C: data = DEV_ID[15:8];      7'h7D: data = DEV_ID[7:0];
            7'h7E: data = MFR_ID[15:8];      7'h7F: data = MFR_ID[7:0];
            default: data = 8'h00;
        endcase
    end
endmodule
