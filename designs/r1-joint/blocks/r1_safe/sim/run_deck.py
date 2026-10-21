#!/usr/bin/env python3
"""Shim (2026-10-21, r1_isense revision 2): the shared runner of r1_isense and r1_safe is
../../r1_isense/sim/run_deck.py. The two hand-edited copies were merged there (the r1_safe copy differed only in the
NET handling, which the shared runner keeps). Usage and options: see that file."""
import os, runpy
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "r1_isense", "sim", "run_deck.py"),
               run_name="__main__")
