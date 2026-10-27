* R1 full-chip testbench (track T10), block view "sch": the schematic netlists of record.
* r1_chip.sp instantiates the canonical cell names of the chip LVS reference (lvs/make_top_cdl_e.py) with their
* pin lists. This file maps each canonical cell to the block netlist of record. To run the same decks on the
* extracted netlists, replace this include by views/pex.inc (same cell names and pins; see tb/README.md).
* Paths are container paths (repository mounted at /work by flow/run.sh).
*
* Netlists of record (sha256 recorded by tb/run_tb.py in run.json; table in tb/README.md):
.include /work/designs/r1-joint/blocks/r1_afe/schematic/r1_afe_revE.spice
.include /work/designs/r1-joint/blocks/r1_adc/schematic/r1_adc_r5.spice
.include /work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice
.include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice
.include /work/designs/r1-joint/blocks/r1_bgr/schematic/r1_bgr.spice
.include /work/designs/r1-joint/blocks/r1_bias/schematic/r1_bias_rev1d.spice
* r1_bias revision 1d = the committed netlist of record (sha256 3fa56d92...); r1_bias.spice in the tree is revision 2 work (D20, two new pins)
.include /work/designs/r1-joint/blocks/r1_osc/schematic/r1_osc.spice
.include /work/designs/r1-joint/blocks/r1_t2f/schematic/g1_t2f_rev2.spice
.include /work/designs/r1-joint/blocks/r1_gate/schematic/g1_cells_copy.spice
.include /work/designs/r1-joint/blocks/r1_ls/schematic/g1_ls_up_copy.spice

* r1_gate_lv: the schematic file r1_gate.spice includes its cells by a relative path, so the cell is repeated here
* (text identical to r1_gate/schematic/r1_gate.spice, variant L; checked by run_tb.py)
.subckt r1_gate_lv pwm_a pwm_b pwm_c gate_en gc_a gc_b gc_c vdd vdda vss
XNA pwm_a gate_en na vdd vss g1_lv_nand2
XIA na gc_a vdd vss g1_lv_inv
XNB pwm_b gate_en nb vdd vss g1_lv_nand2
XIB nb gc_b vdd vss g1_lv_inv
XNC pwm_c gate_en nc vdd vss g1_lv_nand2
XIC nc gc_c vdd vss g1_lv_inv
.ends

* canonical names of the chip reference -> schematic cells (pin lists identical, checked by run_tb.py)
.subckt r1_safe outa_p outa_n outb_p outb_n vref
+ oa_p0 oa_p1 oa_p2 oa_p3 oa_p4 oa_p5 oa_p6 oa_p7 oa_n0 oa_n1 oa_n2 oa_n3 oa_n4 oa_n5 oa_n6 oa_n7
+ na_p0 na_p1 na_p2 na_p3 na_p4 na_p5 na_p6 na_p7 na_n0 na_n1 na_n2 na_n3 na_n4 na_n5 na_n6 na_n7
+ ob_p0 ob_p1 ob_p2 ob_p3 ob_p4 ob_p5 ob_p6 ob_p7 ob_n0 ob_n1 ob_n2 ob_n3 ob_n4 ob_n5 ob_n6 ob_n7
+ nb_p0 nb_p1 nb_p2 nb_p3 nb_p4 nb_p5 nb_p6 nb_p7 nb_n0 nb_n1 nb_n2 nb_n3 nb_n4 nb_n5 nb_n6 nb_n7
+ oc_a neg_a oc_b neg_b ibias_oa ibias_na ibias_ob ibias_nb vdda vdd vss
XAN outa_p outa_n outb_p outb_n vref
+ oa_p0 oa_p1 oa_p2 oa_p3 oa_p4 oa_p5 oa_p6 oa_p7 oa_n0 oa_n1 oa_n2 oa_n3 oa_n4 oa_n5 oa_n6 oa_n7
+ na_p0 na_p1 na_p2 na_p3 na_p4 na_p5 na_p6 na_p7 na_n0 na_n1 na_n2 na_n3 na_n4 na_n5 na_n6 na_n7
+ ob_p0 ob_p1 ob_p2 ob_p3 ob_p4 ob_p5 ob_p6 ob_p7 ob_n0 ob_n1 ob_n2 ob_n3 ob_n4 ob_n5 ob_n6 ob_n7
+ nb_p0 nb_p1 nb_p2 nb_p3 nb_p4 nb_p5 nb_p6 nb_p7 nb_n0 nb_n1 nb_n2 nb_n3 nb_n4 nb_n5 nb_n6 nb_n7
+ oc_a neg_a oc_b neg_b ibias_oa ibias_na ibias_ob ibias_nb vdda vdd vss r1_safe_an
.ends
.subckt r1_t2f vdd vdd12 vss pbias pcasc vref en mode fout
X1 vdd vdd12 vss pbias pcasc vref en mode fout g1_t2f
.ends
* t10_ls = chip cell r1_ls (renamed in the testbench: r1_isense.spice defines its own internal r1_ls with other pins)
.subckt t10_ls in out vdd vdda vss
X1 in out vdd vdda vss g1_ls_up
.ends

* r1_adc: no macro of record exists (placeholder r1_adc_ph in try e). This wrapper has the placeholder pin list
* (plus cur_trk, see tb/README.md) and contains the r1_adc revision-5 cells of record: r1_adc5_core (both slices,
* comparators, CDACs, bootstrapped switches, clkgen; the SAR register is XSPICE digital in the ADC netlist itself),
* r1_reffilt5 (10 pF input filter) and r1_refbuf5 (option 3c, ndec=4 ndecl=2, bias pin nb).
* MODEL parts (no block owns them yet): the timing ports come from the sequencer model in rtl/r1_chip_dig.v through
* the global nodes seq_*; vcm2 (AFE output CM) and vcm (isense CM) are ideal 0.6 V sources with 1 kOhm;
* the 14 raw decisions per slice are decoded from the ADC netlist's behavioural raw word.
.global seq_trka0 seq_trka1 seq_trkb0 seq_trkb1 seq_win seq_lat seq_valid
+ seq_stb0 seq_stb1 seq_stb2 seq_stb3 seq_stb4 seq_stb5 seq_stb6 seq_stb7 seq_stb8 seq_stb9 seq_stb10 seq_stb11 seq_stb12 seq_stb13
.subckt r1_adc adc_hold is_smp clk adc_start adc_sel adc_valid_a
+ adc_raw_a_0 adc_raw_a_1 adc_raw_a_2 adc_raw_a_3 adc_raw_a_4 adc_raw_a_5 adc_raw_a_6 adc_raw_a_7 adc_raw_a_8 adc_raw_a_9 adc_raw_a_10 adc_raw_a_11 adc_raw_a_12 adc_raw_a_13
+ adc_valid_b
+ adc_raw_b_0 adc_raw_b_1 adc_raw_b_2 adc_raw_b_3 adc_raw_b_4 adc_raw_b_5 adc_raw_b_6 adc_raw_b_7 adc_raw_b_8 adc_raw_b_9 adc_raw_b_10 adc_raw_b_11 adc_raw_b_12 adc_raw_b_13
+ por_n ain_sin_p ain_sin_n ain_cos_p ain_cos_n vcm2 ibias ain_isa_p ain_isa_n ain_isb_p ain_isb_n vcm vdda vdd vss vref_in cur_trk
* digital inputs of the placeholder pin list: a small load only (the sequencer model reads ctrl directly)
Cl_hold adc_hold vss 5f
Cl_ismp is_smp vss 5f
Cl_start adc_start vss 5f
Cl_sel adc_sel vss 5f
Cl_por por_n vss 5f
Cl_cur cur_trk vss 5f
* reference: bandgap -> 10 pF filter -> buffer (MSB and LSB array references)
XCF vref_in vss r1_reffilt5 w=82u
XREF vref_in vrefo vreflo ibias vdda vss r1_refbuf5 ndec=4 ndecl=2
XCORE ain_sin_p ain_sin_n ain_cos_p ain_cos_n ain_isa_p ain_isa_n ain_isb_p ain_isb_n
+ seq_trka0 seq_trka1 seq_trkb0 seq_trkb1 clk seq_win seq_win seq_lat seq_lat
+ seq_stb0 seq_stb1 seq_stb2 seq_stb3 seq_stb4 seq_stb5 seq_stb6 seq_stb7 seq_stb8 seq_stb9 seq_stb10 seq_stb11 seq_stb12 seq_stb13
+ seq_stb0 seq_stb1 seq_stb2 seq_stb3 seq_stb4 seq_stb5 seq_stb6 seq_stb7 seq_stb8 seq_stb9 seq_stb10 seq_stb11 seq_stb12 seq_stb13
+ rawa rawb topap topan topbp topbn vdd vrefo vrefo vreflo vreflo vss r1_adc5_core
* MODEL: common-mode outputs (the ADC revision 5 has no vcm generator)
Vcm2s vcm2i vss 0.6
Rcm2 vcm2i vcm2 1k
Vcms vcmi vss 0.6
Rcm vcmi vcm 1k
* MODEL: valid of both slices from the sequencer model (both slices convert in parallel, stagger 0)
Bva adc_valid_a vss V=v(seq_valid)
Bvb adc_valid_b vss V=v(seq_valid)
* raw decisions: bit i of the raw word (rawa/rawb are the integer word in volts, written by the ADC SAR register)
Bra0 adc_raw_a_0 vss V=1.2*(floor((v(rawa)+0.5)/1)-2*floor((v(rawa)+0.5)/2))
Bra1 adc_raw_a_1 vss V=1.2*(floor((v(rawa)+0.5)/2)-2*floor((v(rawa)+0.5)/4))
Bra2 adc_raw_a_2 vss V=1.2*(floor((v(rawa)+0.5)/4)-2*floor((v(rawa)+0.5)/8))
Bra3 adc_raw_a_3 vss V=1.2*(floor((v(rawa)+0.5)/8)-2*floor((v(rawa)+0.5)/16))
Bra4 adc_raw_a_4 vss V=1.2*(floor((v(rawa)+0.5)/16)-2*floor((v(rawa)+0.5)/32))
Bra5 adc_raw_a_5 vss V=1.2*(floor((v(rawa)+0.5)/32)-2*floor((v(rawa)+0.5)/64))
Bra6 adc_raw_a_6 vss V=1.2*(floor((v(rawa)+0.5)/64)-2*floor((v(rawa)+0.5)/128))
Bra7 adc_raw_a_7 vss V=1.2*(floor((v(rawa)+0.5)/128)-2*floor((v(rawa)+0.5)/256))
Bra8 adc_raw_a_8 vss V=1.2*(floor((v(rawa)+0.5)/256)-2*floor((v(rawa)+0.5)/512))
Bra9 adc_raw_a_9 vss V=1.2*(floor((v(rawa)+0.5)/512)-2*floor((v(rawa)+0.5)/1024))
Bra10 adc_raw_a_10 vss V=1.2*(floor((v(rawa)+0.5)/1024)-2*floor((v(rawa)+0.5)/2048))
Bra11 adc_raw_a_11 vss V=1.2*(floor((v(rawa)+0.5)/2048)-2*floor((v(rawa)+0.5)/4096))
Bra12 adc_raw_a_12 vss V=1.2*(floor((v(rawa)+0.5)/4096)-2*floor((v(rawa)+0.5)/8192))
Bra13 adc_raw_a_13 vss V=1.2*(floor((v(rawa)+0.5)/8192)-2*floor((v(rawa)+0.5)/16384))
Brb0 adc_raw_b_0 vss V=1.2*(floor((v(rawb)+0.5)/1)-2*floor((v(rawb)+0.5)/2))
Brb1 adc_raw_b_1 vss V=1.2*(floor((v(rawb)+0.5)/2)-2*floor((v(rawb)+0.5)/4))
Brb2 adc_raw_b_2 vss V=1.2*(floor((v(rawb)+0.5)/4)-2*floor((v(rawb)+0.5)/8))
Brb3 adc_raw_b_3 vss V=1.2*(floor((v(rawb)+0.5)/8)-2*floor((v(rawb)+0.5)/16))
Brb4 adc_raw_b_4 vss V=1.2*(floor((v(rawb)+0.5)/16)-2*floor((v(rawb)+0.5)/32))
Brb5 adc_raw_b_5 vss V=1.2*(floor((v(rawb)+0.5)/32)-2*floor((v(rawb)+0.5)/64))
Brb6 adc_raw_b_6 vss V=1.2*(floor((v(rawb)+0.5)/64)-2*floor((v(rawb)+0.5)/128))
Brb7 adc_raw_b_7 vss V=1.2*(floor((v(rawb)+0.5)/128)-2*floor((v(rawb)+0.5)/256))
Brb8 adc_raw_b_8 vss V=1.2*(floor((v(rawb)+0.5)/256)-2*floor((v(rawb)+0.5)/512))
Brb9 adc_raw_b_9 vss V=1.2*(floor((v(rawb)+0.5)/512)-2*floor((v(rawb)+0.5)/1024))
Brb10 adc_raw_b_10 vss V=1.2*(floor((v(rawb)+0.5)/1024)-2*floor((v(rawb)+0.5)/2048))
Brb11 adc_raw_b_11 vss V=1.2*(floor((v(rawb)+0.5)/2048)-2*floor((v(rawb)+0.5)/4096))
Brb12 adc_raw_b_12 vss V=1.2*(floor((v(rawb)+0.5)/4096)-2*floor((v(rawb)+0.5)/8192))
Brb13 adc_raw_b_13 vss V=1.2*(floor((v(rawb)+0.5)/8192)-2*floor((v(rawb)+0.5)/16384))
.ends r1_adc
