#!/usr/bin/env python3
"""Unchanged DC-target settling analysis, explicitly bound to the R100 source."""
import hashlib,json,sys
from pathlib import Path
def main():
    old=Path(__file__).resolve().parent/'analyze_comp45_settling.py'
    assert hashlib.sha256(old.read_bytes()).hexdigest()=='35fd8b7da90944f8484a4a7a75ca92fc6369b72670b899403c2aa801a8550e20'
    original=old.read_text();before='from run_comp45_followthrough import SOURCE';after='from expose_rz100_internal_nodes import SOURCE'
    assert original.count(before)==1
    text=original.replace(before,after);assert text.replace(after,before)==original
    out=Path(sys.argv[sys.argv.index('--output')+1]);prep=out.with_name(out.name+'-adapter');assert not prep.exists() and not out.exists()
    prep.mkdir(parents=True);(prep/'derived.py').write_text(text);(prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(original_helper_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
        derived_sha256=hashlib.sha256(text.encode()).hexdigest(),exact_inverse=True,only_change='R100 source identity import; all criteria and analysis unchanged'),indent=2)+'\n')
    scope=dict(__file__=str(old),__name__='rz100_settling_analysis');exec(compile(text,str(prep/'derived.py'),'exec'),scope);scope['main']()
if __name__=='__main__':main()
