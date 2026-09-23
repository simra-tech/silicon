#!/usr/bin/env python3
"""Exact same weight-free graph bounds on a source-held feeder candidate."""
import json
import sys
from pathlib import Path
from screen_sense_dual_gate_proposal import GM4, sha
from build_sense_m2_feed_remedy import STATUS


def main():
    index = sys.argv.index('--candidate')
    candidate = Path(sys.argv[index+1]); del sys.argv[index:index+2]
    topology = Path(sys.argv[sys.argv.index('--topology')+1])
    output = Path(sys.argv[sys.argv.index('--output')+1])
    proof = json.loads((candidate/'analysis.json').read_text())
    m = json.loads((topology/'summary.json').read_text())
    gds = candidate/'g1_sense_physical.gds'
    assert proof['status'] == STATUS and sha(gds) == proof['GDS_sha256'] == m['GDS_sha256']
    binding = topology.with_name(topology.name+'-preparation')/'binding.json'
    attachment = json.loads(binding.read_text())
    assert attachment['status'] == 'passed exact intrinsic/contact preservation'
    assert attachment['candidate_GDS_sha256'] == sha(gds)
    original = Path(__file__).with_name('bound_sense_metal_rails.py')
    assert sha(original) == 'bd053966926fb31e9b66e1a7755dd6ee599d0221739b4a4789867026ba0e23cd'
    text = original.read_text()
    old_gds = "    gds=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4/ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'"
    changes = [('597c4c616cdb63f42d3e0575b52bfdfd0e0259a2bd2a95eba5b1a314ffb0b6f1', sha(topology/'summary.json')),
               ('9613a5c4dedd2063776300b9d3c3663264358e7f5751df1928ac341ac25f6404', sha(topology/'positive_edges.json.gz')),
               (old_gds, old_gds.replace('    gds=', '    baseline=')+'\n    gds=Path('+repr(str(gds))+')'),
               ("    assert sha(gds)==m['GDS_sha256']==support['GDS_sha256']",
                "    assert sha(baseline)==support['GDS_sha256']=="+repr(proof['baseline_GDS_sha256'])+
                "\n    assert sha(gds)==m['GDS_sha256']=="+repr(proof['GDS_sha256'])),
               ("'Geometry change or adoption'", "'Fullchip adoption'")]
    for find, replace in changes:
        assert text.count(find) == 1; text = text.replace(find, replace)
    prep = output.with_name(output.name+'-preparation'); assert not prep.exists(); prep.mkdir(parents=True)
    (prep/'derived_bound.py').write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep/'binding.json').write_text(json.dumps(dict(candidate_sha256=sha(gds),
        topology_binding_sha256=sha(binding), original_bound_sha256=sha(original),
        derived_bound_sha256=sha(prep/'derived_bound.py'), adapter_sha256=sha(Path(__file__)),
        support_scope='Original native terminal support held; no attachment or weights selected'), indent=2)+'\n')
    namespace = {'__file__': str(original), '__name__': 'm2_feed_bound_derivative'}
    exec(compile(text, str(original), 'exec'), namespace); namespace['main']()


if __name__ == '__main__': main()
