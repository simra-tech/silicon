#!/usr/bin/env python3
"""Bounded sequential saved-data analysis; never launches an analog solver."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    run = bulk/'bgr-dvbe-kpex-20260923-r1'
    prepared = bulk/'bgr-dvbe-fixture-20260923-r1'
    output = bulk/'bgr-dvbe-comparison-20260923-r1'
    assert not output.exists()
    output.mkdir()
    paths = [HERE.parent/'coordinated_model_boundary/analyze_external_pin.py',
             HERE/'compare_dvbe.py', Path(__file__)]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (output/'analysis_sources.json').write_text(json.dumps(hashes, indent=2)+'\n')
    commands = [
        [sys.executable, str(paths[0]), '--run', str(run), '--prepared', str(prepared)],
        [sys.executable, str(paths[1]),
         '--baseline-prepared', str(bulk/'bgr-external-pin-source-20260923-r1'),
         '--candidate-prepared', str(prepared),
         '--baseline-run', str(bulk/'bgr-external-pin-kpex-20260923-r1'),
         '--candidate-run', str(run),
         '--source', str(HERE.parents[1]/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'),
         '--output', str(output/'analysis.json')]]
    for i, argv in enumerate(commands):
        with (output/('stage%d.log' % i)).open('x') as log:
            p = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=60)
        assert p.returncode == 0, (i, p.returncode)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in hashes.items())
    print((output/'analysis.json').read_text()[:1000])


if __name__ == '__main__':
    main()
