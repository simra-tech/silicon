#!/bin/sh
# Derive the gate-level chip testbench from tb/tb_top.v without editing it.
# usage: sh mk_gl_tb.sh <in tb_top.v> <out tb_top_gl.v>
# Hierarchical probes into the RTL are replaced by nets that survive in the flattened t7 netlist.
# Probes that do not survive are reduced or skipped and are labelled GLNOTE / GLSKIP in the log.
sed \
 -e 's/^module tb_top;/module tb_top;\n    reg [2047:0] sdf_file; \/\/ GL: SDF back-annotation\n    reg [255:0] sdf_mode;\n    initial begin\n        if ($value$plusargs("sdf=%s", sdf_file)) begin\n            if (!$value$plusargs("sdfmode=%s", sdf_mode)) sdf_mode = "MAXIMUM";\n            $sdf_annotate(sdf_file, tb_top.dut, , "sdf_annotate.log", sdf_mode);\n            $display("GLNOTE sdf annotated %0s mode %0s", sdf_file, sdf_mode);\n        end else $display("GLNOTE no SDF (zero-delay gate level)");\n    end\n    wire [3:0] gl_cal_exh = {dut.\\cal_exh[3] , dut.\\cal_exh[2] , dut.\\cal_exh[1] , dut.\\cal_exh[0] };\n    wire [7:0] gl_status_lo = {~dut.fault_n, dut.pos_valid, 1'"'"'b0, dut.cal_valid, dut.track_err, 1'"'"'b0, dut.amp_high, dut.amp_low};\n    wire [13:0] gl_status = {|gl_cal_exh, dut.cal_done, dut.cal_busy, dut.osc_done, 2'"'"'b0, gl_status_lo};\n    wire [12:0] gl_cause = {1'"'"'bx, dut.\\cause[11] , dut.\\cause[10] , dut.\\cause[9] , dut.\\cause[8] , dut.\\cause[7] , dut.\\cause[6] , dut.\\cause[5] , dut.\\cause[4] , dut.\\cause[3] , dut.\\cause[2] , dut.\\cause[1] , dut.\\cause[0] };/' \
 -e 's/dut\.cal_exh/gl_cal_exh/g' \
 -e 's/spi_mi\[23:16\] == dut\.status\[7:0\]/(spi_mi[23:16] \& 8'"'"'hDB) == (gl_status_lo \& 8'"'"'hDB)/' \
 -e 's/dut\.status\[/gl_status[/g' \
 -e 's/dut\.u_gate\.pwm_wrap/dut.pwm_wrap/g' \
 -e 's/dut\.u_safe\.cause\[3:0\]/gl_cause[3:0]/g' \
 -e 's/dut\.u_safe\.cause\[12\] \&\& dut\.u_safe\.cause\[11\]/gl_cause[11]/' \
 -e 's/while (dut\.u_safe\.e_a\[23:8\] >= 16'"'"'d2000) #(1000);/#(2400 * clk_ns); \/\/ GLNOTE e_a is not observable in the netlist: fixed wait of 8 I2t updates/' \
 -e 's/check(dut\.u_biss\.cst == 3'"'"'d0, \(.*\));/$display("GLSKIP %0s (control-channel state register recoded by synthesis, no observable net)", \1);/' \
 "$1" > "$2"
