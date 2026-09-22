#!/usr/bin/env python3
"""Read-only stack telemetry around the unchanged installed KPEX CLI."""
import faulthandler
import runpy
import sys

faulthandler.enable()
faulthandler.dump_traceback_later(60, repeat=True)
sys.argv[0] = 'kpex'
try:
    runpy.run_module('klayout_pex.kpex_cli', run_name='__main__')
finally:
    faulthandler.cancel_dump_traceback_later()
