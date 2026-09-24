"""Scheduling-only09:21:29Z leaf cutoff around unchanged joint586 science."""
import datetime,json,os
from pathlib import Path
import run_joint586_calibration as original
CUTOFF='2026-09-24T09:21:29Z'
def active(now=None):return(now or datetime.datetime.utcnow())<datetime.datetime.strptime(CUTOFF,'%Y-%m-%dT%H:%M:%SZ')
def main():
    packet_path=original.ROOT/os.environ['G1_JOINT7_PACKET_REL'];digest=os.environ['G1_JOINT7_PACKET_SHA256'];packet=json.loads(packet_path.read_text())
    assert original.sha(packet_path)==digest and packet['cutoff_utc']==CUTOFF
    for path in [Path(original.__file__).resolve(),Path(__file__).resolve()]:assert original.sha(path)==packet['bindings_sha256'][str(path.relative_to(original.ROOT))]
    pause=original.check_pause;engine=original.run_bounded
    def check(path):
        pause(path)
        if not active():raise InterruptedError('Owner09:21:29Z cutoff; next solver NOT RUN')
    def run(*args,**kwargs):
        assert args[0][:2]==['ngspice','-b']and args[3]==1200
        assert original.sha(packet_path)==digest
        check(None)
        return engine(*args,**kwargs)
    original.check_pause=check;original.run_bounded=run;original.main()
if __name__=='__main__':main()
