"""LibreLane plugin for the pin-compatible re-hardening of g1_digital.

Adds one step, G1.SplitClockRoot, inserted after OpenROAD.CTS by
substituting_steps ("+OpenROAD.CTS": G1.SplitClockRoot). It repeats in-flow
what the chip macro's CTS rework did outside the flow
(review/audits/run_digital_cts_fanout.py --cluster 8 --split-root): every
clock-tree root buffer clkbuf_0_<clk> that drives more than 8 buffer inputs
gets its sinks split, in name order, into groups of 8, each group driven by a
new sg13g2_buf_16 (instance clkbuf_fanout_split<g>_<clk>_cell, net
clkbuf_fanout_split<g>_<clk>, the chip's final names); then detailed
placement legalises. Found by LibreLane's plugin discovery when this
directory is on PYTHONPATH (eco/run_trial.sh does that).
"""
import os

from librelane.steps import Step

_CTS = Step.factory.get("OpenROAD.CTS")


@Step.factory.register()
class SplitClockRoot(_CTS):
    """Split clock-root fanout > 8 with sg13g2_buf_16 buffers, then legalise."""

    id = "G1.SplitClockRoot"
    name = "Split clock-tree root fanout (G1)"

    def get_script_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "split_clock_root.tcl")
