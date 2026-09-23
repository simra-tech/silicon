"""Five independent required source-held route contexts, serial one-CPU batch."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
base = Path('@RESULTS@/final-remaining-contexts-20260923-r1')
assert not base.exists()
base.mkdir()
pairs = [('isense_vref', 'i_core.isense', 'i_core.vref', 1, 1),
         ('vrefbuf_dac', 'i_core.vref_buf', 'i_core.dac_hard[2]', 1, 8),
         ('iptat_isense', 'i_core.iptat', 'i_core.isense', 6, 3),
         ('sense_inputs', 'i_core.sense_n', 'i_core.sense_p', 3, 5),
         ('vref_pcasc', 'i_core.vref', 'i_core.pcasc', 8, 6)]
runner = root/'@SESSION_RECEIPTS@/run_final_selected_clip_20260923.py'
checker = root/'designs/g1-guardian/review/audits/final_route_context/check_context.py'
bound = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (runner, checker)}
result = dict(status='running', source_sha256=bound, pairs=[])
(base/'runner.py').write_bytes(Path(__file__).read_bytes())
for name, victim, neighbor, vseg, nseg in pairs:
    directory = base/name
    directory.mkdir()
    item = dict(name=name, victim=victim, neighbor=neighbor, steps=[])
    result['pairs'].append(item)
    for width in (12, 24, 48):
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in bound.items())
        command = [sys.executable, str(runner), '--output', str(directory/('width%d'%width)),
                   '--context-um', str(width), '--victim', victim, '--neighbor', neighbor,
                   '--victim-segment', str(vseg), '--neighbor-segment', str(nseg)]
        start = time.monotonic()
        with (directory/('width%d.log'%width)).open('x') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        item['steps'].append(dict(width=width, command=command, returncode=child.returncode, wall_s=time.monotonic()-start))
        (base/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
        if child.returncode:
            item['status'] = 'failed extraction/check; other independent pairs continue'
            break
    if len(item['steps']) == 3 and all(r['returncode'] == 0 for r in item['steps']):
        command = [sys.executable, str(checker)]
        for width in (12,24,48):
            command += ['--width%d'%width, str(directory/('width%d'%width))]
        command += ['--output', str(directory/'context_check.json')]
        with (directory/'context_check.log').open('x') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        item['context_command'] = command
        item['context_returncode'] = child.returncode
        item['status'] = 'passed' if child.returncode == 0 else 'failed context criterion'
    (base/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
result['status'] = 'passed' if all(r['status']=='passed' for r in result['pairs']) else 'failed'
(base/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['status']=='passed' else 1)
