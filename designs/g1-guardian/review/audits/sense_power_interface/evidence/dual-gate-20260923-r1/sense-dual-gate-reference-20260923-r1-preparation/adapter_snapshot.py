#!/usr/bin/env python3
"""Source-held independent native audit with only the candidate status adapted."""
import sys
from pathlib import Path
from screen_sense_dual_gate_proposal import GM4, sha


def main():
    sys.path.insert(0, str(GM4))
    original = GM4/'audit_full_sense_reference.py'
    assert sha(original) == '7455f47e72fbe6d511e5e8ed05a3839bb08afc32ed32b7b1929d3512d710d027'
    text = original.read_text()
    changes = [('from build_source_faithful_buffer import full_nets',
                'from build_power_revision import full_nets_upper as full_nets'),
               ("m['status']=='passed complete SENSE scoped preparation'",
                "m['status']=='passed source-held dual-ended gate geometry'")]
    for old, new in changes:
        assert text.count(old) == 1; text = text.replace(old, new)
    output = Path(sys.argv[sys.argv.index('--output')+1])
    prep = output.with_name(output.name+'-preparation'); assert not prep.exists(); prep.mkdir(parents=True)
    (prep/'derived_native_audit.py').write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep/'upper_connectivity_snapshot.py').write_bytes((GM4/'build_power_revision.py').read_bytes())
    namespace = {'__file__': str(original), '__name__': 'dual_gate_reference_derivative'}
    exec(compile(text, str(original), 'exec'), namespace); namespace['main']()


if __name__ == '__main__': main()
