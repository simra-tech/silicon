#!/usr/bin/env python3
"""Stop only an identified capture diagnostic after its immutable checkpoint."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(pid):
    p=Path('/proc')/str(pid)
    raw=(p/'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
    return dict(pid=pid,start_ticks=int(fields[19]),command=(p/'cmdline').read_bytes().split(b'\0')[:-1])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pid',type=int,required=True);ap.add_argument('--start-ticks',type=int,required=True)
    ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();os.sched_setaffinity(0,{48});assert not a.output.exists()
    ident=identity(a.pid);assert ident['start_ticks']==a.start_ticks
    required=['klayout','-b','-r',str(a.folder/'instrumented_lvs/sg13g2.lvs')]
    assert [x.decode() for x in ident['command'][:4]]==required
    children=Path('/proc')/str(a.pid)/'task'/str(a.pid)/'children'
    assert children.read_text().strip()==''
    log=a.folder/'engine.log';text=log.read_text()
    assert 'CAPTURE L2N END' in text and 'PROFILE purge END' not in text
    assert text.rstrip().endswith('CAPTURE L2N END')
    files=[a.folder/'before_purge.l2n',a.folder/'before_purge_binary64.json']
    state=lambda:{str(p):dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p)) for p in files}
    first=state();time.sleep(3);second=state();assert first==second
    assert all(v['bytes']>0 for v in first.values())
    assert identity(a.pid)==ident and log.read_text()==text and children.read_text().strip()==''
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='authorized intentional diagnostic interruption',pid=a.pid,start_ticks=a.start_ticks,
        command=[x.decode() for x in ident['command']],signal='SIGTERM',checkpoint_files=first,
        engine_log_sha256=sha(log),stable_interval_seconds=3,no_child_processes=True,
        next_original_statement='target_netlist.purge',native_LVS_acceptance='not run by diagnostic',
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    def save():(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    save();os.kill(a.pid,signal.SIGTERM)
    gone=False
    for _ in range(50):
        try:current=identity(a.pid)
        except FileNotFoundError:gone=True;break
        if current['start_ticks']!=a.start_ticks:gone=True;break
        time.sleep(.1)
    result['exact_engine_process_gone']=gone;save();assert gone


if __name__=='__main__':main()
