#!/usr/bin/env python3
"""Retain all independent native/source audits; extend only upper-metal connectivity."""
import sys
from pathlib import Path
from build_native_prototypes import sha
from build_power_revision import full_nets_upper

HERE=Path(__file__).resolve().parent

def main():
    original=HERE/'audit_full_sense_reference.py'
    assert sha(original)=='7455f47e72fbe6d511e5e8ed05a3839bb08afc32ed32b7b1929d3512d710d027'
    text=original.read_text()
    changes=[("from build_source_faithful_buffer import full_nets", "from build_power_revision import full_nets_upper as full_nets"),
             ("m['status']=='passed complete SENSE scoped preparation'", "m['status']=='passed isolated power routing geometry gate'")]
    for old,new in changes:
        assert text.count(old)==1,old
        text=text.replace(old,new)
    output=Path(sys.argv[sys.argv.index('--output')+1]);prep=output.with_name(output.name+'-preparation')
    assert not prep.exists();prep.mkdir(parents=True)
    (prep/'derived_native_audit.py').write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep/'upper_connectivity_snapshot.py').write_bytes((HERE/'build_power_revision.py').read_bytes())
    namespace={'__file__':str(original),'__name__':'power_reference_derivative'}
    exec(compile(text,str(original),'exec'),namespace);namespace['main']()

if __name__=='__main__':main()
