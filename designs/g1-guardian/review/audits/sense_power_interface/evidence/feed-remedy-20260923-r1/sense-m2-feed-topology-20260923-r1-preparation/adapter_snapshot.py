#!/usr/bin/env python3
"""Re-extract the held contact graph after a proven additive M2/Via1 remedy."""
import json
import sys
from pathlib import Path
import pya
from build_sense_dual_gate import snapshot, text_snapshot, hierarchy
from screen_sense_dual_gate_proposal import GM4, sha
from build_sense_m2_feed_remedy import STATUS


def main():
    index = sys.argv.index('--candidate')
    candidate = Path(sys.argv[index+1]); del sys.argv[index:index+2]
    output = Path(sys.argv[sys.argv.index('--output')+1])
    proof = json.loads((candidate/'analysis.json').read_text())
    assert proof['status'] == STATUS
    gds = candidate/'g1_sense_physical.gds'
    baseline = GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    assert sha(gds) == proof['GDS_sha256'] and sha(baseline) == proof['baseline_GDS_sha256']
    old = pya.Layout(); old.read(str(baseline)); new = pya.Layout(); new.read(str(gds))
    a = old.cell('g1_sense_physical'); b = new.cell(a.name)
    before = snapshot(a); after = snapshot(b)
    assert text_snapshot(a) == text_snapshot(b) and hierarchy(old) == hierarchy(new)
    for key in set(before)|set(after):
        x = before.get(key, pya.Region()); y = after.get(key, pya.Region())
        assert (x-y).is_empty(), ('Removed native geometry', key)
        if key not in ((10, 0), (19, 0)): assert (x^y).is_empty(), key
    original = Path(__file__).with_name('extract_sense_contact_topology.py')
    assert sha(original) == '6df5878162508816316a039f44f8bb9ff1ab3d65d8502acec87a4717fd656024'
    text = original.read_text()
    changes = [("    gds = parent/'g1_sense_physical.gds'",
                "    baseline = parent/'g1_sense_physical.gds'\n    gds = Path("+repr(str(gds))+")"),
               ("    assert sha(gds) == footprints['GDS_sha256'] == ledger['GDS_sha256']",
                "    assert sha(baseline) == footprints['GDS_sha256'] == ledger['GDS_sha256']\n"
                "    assert sha(gds) == "+repr(proof['GDS_sha256'])),
               ('source_geometry_unchanged=True,', 'source_and_primitive_contact_geometry_unchanged=True,')]
    for find, replace in changes:
        assert text.count(find) == 1; text = text.replace(find, replace)
    prep = output.with_name(output.name+'-preparation'); assert not prep.exists(); prep.mkdir(parents=True)
    (prep/'derived_extractor.py').write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep/'binding.json').write_text(json.dumps(dict(status='passed exact intrinsic/contact preservation',
        candidate_GDS_sha256=sha(gds), baseline_GDS_sha256=sha(baseline),
        candidate_proof_sha256=sha(candidate/'analysis.json'), original_extractor_sha256=sha(original),
        derived_extractor_sha256=sha(prep/'derived_extractor.py'), adapter_sha256=sha(Path(__file__)),
        model_weights='not selected', current_injection='not selected'), indent=2)+'\n')
    namespace = {'__file__': str(original), '__name__': 'm2_feed_topology_derivative'}
    exec(compile(text, str(original), 'exec'), namespace); namespace['main']()


if __name__ == '__main__': main()
