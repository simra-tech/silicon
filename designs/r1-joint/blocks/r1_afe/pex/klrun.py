#!/usr/bin/env python3
"""KLayout batch wrapper that prints Python errors (klayout -b does not print SystemExit messages or some tracebacks):
  flow/run.sh klayout -b -r pex/klrun.py -rd script=pex/pex_rc_build.py -rd <name>=<value> ...
Exits non-zero on an error."""
import sys
import traceback
try:
    exec(compile(open(script).read(), script, 'exec'), globals())   # noqa: F821 (-rd script)
except SystemExit as e:
    if e.code not in (None, 0):
        print('ERROR (SystemExit):', e)
        sys.stdout.flush()
        import os
        os._exit(1)
except BaseException:
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    import os
    os._exit(1)
