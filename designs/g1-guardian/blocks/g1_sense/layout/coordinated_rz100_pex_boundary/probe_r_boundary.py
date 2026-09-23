#!/usr/bin/env python3
"""Independent resistance-only diagnostic; retain the failed full RC check."""
import hashlib,json,sys
from pathlib import Path

def main():
    parent=Path(__file__).with_name('probe_rc_boundary.py')
    original=parent.read_text()
    assert hashlib.sha256(original.encode()).hexdigest()=='06b70779dc982f9b9152e976dfa88052b4ca344b7f4c4f792f3df320caf84317'
    changes=[("\"'--mode','RC'\"","\"'--mode','R'\""),
             ('assert rows\\n        resistors=[]','assert summary.resistances\\n        resistors=[]'),
             ('unchanged native2.5D RC, full-device mode','unchanged native2.5D R, full-device mode'),
             ('completed raw native RC diagnostic','completed raw native R diagnostic'),
             ('failed raw RC diagnostic','failed raw R diagnostic')]
    derived=original
    for old,new in changes:
        assert derived.count(old)==1,old
        derived=derived.replace(old,new)
    restored=derived
    for old,new in reversed(changes):
        assert restored.count(new)==1
        restored=restored.replace(new,old)
    assert restored==original
    output=Path(sys.argv[sys.argv.index('--output')+1])
    record=output.with_name(output.name+'-r-only-contract.json')
    assert not record.exists() and not output.exists()
    record.write_text(json.dumps(dict(exact_inverse=True,changes=changes,
        wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        RC_helper_sha256=hashlib.sha256(original.encode()).hexdigest(),
        derived_helper_sha256=hashlib.sha256(derived.encode()).hexdigest(),
        scope='Resistance-only raw diagnostic, not a repair or substitute for failed full-RC capacitance extraction; no model/reference-plane acceptance.'),indent=2)+'\n')
    namespace=dict(__file__=str(parent),__name__='r_boundary_probe')
    exec(compile(derived,str(parent)+'[R-only]','exec'),namespace)
    try:namespace['main']()
    finally:
        adapter=output.with_name(output.name+'-adapter')
        if adapter.exists():
            (adapter/'r_only_wrapper.py').write_bytes(Path(__file__).read_bytes())
            (adapter/'r_only_parent.py').write_text(derived)

if __name__=='__main__':main()
