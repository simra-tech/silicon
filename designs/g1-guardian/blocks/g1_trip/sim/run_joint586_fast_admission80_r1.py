"""Process-local scheduling adapter; frozen scientific runner remains unchanged."""
import os,sys
from pathlib import Path
import run_joint586_fast_nodeset_staged as original
sys.path.insert(0,str(original.ROOT/'.private/research/verification'))
import fast80_leaf_admission_r1 as admission
def main():
    packet_path=original.ROOT/os.environ['G1_FAST80_PACKET_REL'];digest=os.environ['G1_FAST80_PACKET_SHA256']
    cpu=int(os.environ['G1_FAST80_CPU']);seed=int(sys.argv[sys.argv.index('--seed')+1])
    admission.bindings(original.ROOT,packet_path,digest)
    real=original.run_bounded
    def guarded(*args,**kwargs):
        assert args[0][0:2]==['ngspice','-b']and args[3]==1200
        admission.wait(original.ROOT,packet_path,digest,cpu,seed,Path(args[2]).parent)
        assert admission.active()
        return real(*args,**kwargs)
    original.run_bounded=guarded
    original.main()
if __name__=='__main__':main()
