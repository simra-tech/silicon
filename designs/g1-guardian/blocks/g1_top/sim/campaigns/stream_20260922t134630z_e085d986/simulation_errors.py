"""Reject solver and co-simulator failures even if ngspice returns zero."""
import re

def solver_failure(text):
    # XSPICE may reach the analog endpoint with its RTL executable unloaded.
    return re.search(r'Timestep too small|doAnalyses:|^Error:|simulation\s+aborted|'
                     r'Unable to open input file|mismatched XSPICE/co-simulator '
                     r'(?:input|output) counts|failed to load|cannot open.*(?:vvp|vpi)',
                     text, re.M | re.I)
