#!/usr/bin/env python3
"""Independent native/source audit adaptation: exactly two changed passives."""
import json,sys
from pathlib import Path
from inspect_passive_sites import sha,SOURCE

def main():
    here=Path(__file__).resolve().parent;old=here.parent/'coordinated_gm4/audit_full_sense_reference.py'
    assert sha(old)=='7455f47e72fbe6d511e5e8ed05a3839bb08afc32ed32b7b1929d3512d710d027'
    pos=sys.argv.index('--source');source=Path(sys.argv[pos+1]);del sys.argv[pos:pos+2]
    assert sha(source)==SOURCE
    output=Path(sys.argv[sys.argv.index('--output')+1]);prep=output.with_name(output.name+'-preparation');assert not prep.exists()
    text=old.read_text()
    changes=[
        ('from build_source_faithful_buffer import full_nets','from build_power_revision import full_nets_upper as full_nets'),
        ("source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'",'source=Path('+repr(str(source))+');assert sha(source)=='+repr(SOURCE)),
        ("m['status']=='passed complete SENSE scoped preparation'","m['status']=='passed isolated two-passive geometry/connectivity'"),
        ('{(2000,76700,153400000):95,(1000,6200,6200000):3}','{(2000,76700,153400000):95,(1000,6200,6200000):2,(62000,1000,62000000):1}'),
        ('{(69000,23000,1587000000):1,(23000,23000,529000000):2}','{(45000,23000,1035000000):1,(23000,23000,529000000):2}')]
    for a,b in changes:assert text.count(a)==1,a;text=text.replace(a,b)
    prep.mkdir(parents=True);(prep/'derived_audit.py').write_text(text);(prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(source_sha256=SOURCE,original_audit_sha256=sha(old),derived_sha256=sha(prep/'derived_audit.py'),
        exact_patch_count=len(changes),MOS_channels_default_AP_centroids='unchanged native checks; aggregate default equality is NOT compact-model applicability',
        source_projection='Only standard source-to-CDL projection; ng/mm_ok omissions preserved as known stock scope, not parameter waiver',
        physical_adoption='not run'),indent=2)+'\n')
    namespace=dict(__file__=str(old),__name__='comp45_native_audit')
    exec(compile(text,str(prep/'derived_audit.py'),'exec'),namespace);namespace['main']()
if __name__=='__main__':main()
