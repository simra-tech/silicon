# Chip-level timing constraints for the g1_digital macro (macro of record: run7).
# To be sourced from the ring owner's flow/g1_chip_top.sdc AFTER its own
# create_clock / set_clock_uncertainty / set_propagated_clock lines, e.g.
#     source [file join [file dirname [info script]] ../../g1_ctrl/layout/g1_digital_top.sdc]
# Rationale and evidence: TOP_SDC.md next to this file. Everything here repeats,
# at chip level, the constraints the macro was hardened and signed off with
# (../flow/g1_digital.sdc), so that a chip-level STA that reads the macro's
# netlist and SPEF (LibreLane default STA_MACRO_PRIORITIZE_NL = true) judges the
# macro's internal paths by the same rules as its own signoff.
#
# Names follow the chip netlist of the dry run (blocks/g1_padring, D14):
#   digital macro instance  i_core.u_digital  (its osc_clk pin is driven by i_core.u_osc/osc_clk)
#   serial-clock pad        pad14_sclk        (sg13g2_IOPadIn, core-side pin p2c)
# The chip SDC creates the serial clock as "SCLK" on pad14_sclk/p2c
# (CLOCK_PORT SCLK, CLOCK_NET pad14_sclk/p2c); adjust the names below if the
# instance names change.

set g1d i_core.u_digital

# 1. The oscillator clock: ~10 MHz nominal, +-20 % untrimmed, constrained at
#    100 ns like the macro signoff (the macro is functionally rate-independent;
#    worst setup slack > 28 ns). 0.3 ns transition as in the macro SDC.
#    The clock is defined on the input of the macro's root clock buffer,
#    i_core.u_digital/clkbuf_0_osc_clk/A (the only leaf pin the macro's osc_clk
#    port drives; the name is fixed for the run7 netlist), and NOT on the
#    oscillator's output or the macro's hierarchical osc_clk pin: g1_osc is a
#    black box without a liberty model, so its output pin has no direction and
#    OpenSTA finds no leaf driver to propagate the clock from -- a clock created
#    there is accepted but reaches no register (verified on the dryrun-1350
#    database: 0 registers on osc_clk with either of those pins, 1148 with the
#    buffer pin; TOP_SDC.md). The wire from the oscillator to the macro is
#    thereby excluded from the clock latency, which is common to every osc_clk
#    path and does not change any check.
if { [llength [get_clocks -quiet osc_clk]] == 0 } {
    create_clock -name osc_clk -period 100.0 [get_pins $g1d/clkbuf_0_osc_clk/A]
}
set_clock_transition 0.3 [get_clocks osc_clk]
set_propagated_clock [get_clocks osc_clk]

# 2. The two clocks are asynchronous (register map section 1.3: every crossing
#    goes through a toggle or level synchroniser inside the macro).
set_clock_groups -asynchronous -name g1_digital_async \
    -group [get_clocks osc_clk] -group [get_clocks SCLK]

# 3. Clock uncertainty as used for the macro signoff: 0.5 ns for setup
#    (oscillator jitter), 0.05 ns for hold. The chip template applies
#    CLOCK_UNCERTAINTY_CONSTRAINT (0.25 ns) to both setup and hold of SCLK; on
#    hold that is 0.2 ns more than the macro was hardened with and turns its
#    +0.106 ns worst hold slack into -0.094 ns (TOP_SDC.md). Later
#    set_clock_uncertainty statements override earlier ones for the same clock.
set_clock_uncertainty -setup 0.5  [get_clocks {osc_clk SCLK}]
set_clock_uncertainty -hold  0.05 [get_clocks {osc_clk SCLK}]

# 4. Asynchronous inputs of the macro (synchronised inside; no timing
#    requirement). EN is also the chip's reset, so the template's input delay on
#    the EN pad must not create SCLK-relative checks into the osc_clk domain.
set_false_path -from [get_ports EN]
foreach p {cmp_soft cmp_hard tripped en por_n} {
    set_false_path -through [get_pins $g1d/$p]
}

# 5. Serial data: SDI is sampled on the rising edge of SCLK and driven by the
#    host on the falling edge (>= 2 ns after it); SDO changes on the falling
#    edge and is sampled by the host on the next rising edge. The template's
#    IO_DELAY_CONSTRAINT (20 % of the period = 20 ns) on SDI/SDO is consistent
#    with the macro SDC (max 20 ns, min 2 ns / 0 ns) and is kept; only the
#    minimum input delay of SDI is stated here because the template uses 0.
set_input_delay -min 2.0 -clock [get_clocks SCLK] [get_ports SDI]

# 6. Everything else the macro drives (DAC codes, comparator strobe, latch
#    controls, oscillator enable/trim, level-shifter inputs) ends at analog
#    macros without timing models and is quasi-static; the macro signoff timed
#    them with a 20 ns output delay against osc_clk. No chip-level constraint
#    is needed; nothing is unconstrained by mistake as long as osc_clk exists.
