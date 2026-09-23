#!/usr/bin/env python3
"""Use the held stock runner with only CPU48/global-budget metadata changes."""
import hashlib
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    original = here.parent/'coordinated_dvbe_followup_20260923/run_stock.py'
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '83385b1f3589da863dd2c1f64c71fea95ecc2befe2e5aed224bd9a755f4412a7'
    for before, after in (('set(os.sched_getaffinity(0))=={0}', 'set(os.sched_getaffinity(0))=={48}'),
                          ("gate['project_cpu_budget']>=43", "gate['project_cpu_budget']>=56"),
                          ('cpu=0,watchdog_s=180', 'cpu=48,watchdog_s=180')):
        assert text.count(before) == 1
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='held_stock_cpu48')
    exec(compile(text, str(original), 'exec'), scope)
    return scope['main']()


if __name__ == '__main__':
    raise SystemExit(main())
