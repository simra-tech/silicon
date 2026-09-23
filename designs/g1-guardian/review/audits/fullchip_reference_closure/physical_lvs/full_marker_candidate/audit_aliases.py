#!/usr/bin/env python3
"""Read-only native-alias and reachable source-count binding."""
import argparse
import json
from pathlib import Path
import re
import pya
from prepare_full_marker import paths, SPECS, PARENT, PDK, region, sha, text_records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'source', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and sha(a.parent) == PARENT
    assert sha(a.source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    a.output.mkdir(parents=True)
    ly = pya.Layout(); ly.read(str(a.parent))
    stock = pya.Layout(); stock.read(str(PDK / 'libs.ref/sg13g2_io/gds/sg13g2_io.gds'))
    names = {c.name for c in ly.each_cell() if any(re.search(re.escape(s[0]) + r'(?:\$\d+)?$', c.name) for s in SPECS)}
    occurrences = paths(ly.top_cell(), names)
    defs = {}
    for match in re.finditer(r'(?im)^\.SUBCKT\s+(\S+)([^\n]*)\n(.*?)^\.ENDS\b[^\n]*', a.source.read_text(), re.S):
        defs[match.group(1).upper()] = (match.group(2).split(), match.group(3).splitlines())
    source_rows = []
    wanted = {s[0].upper() for s in SPECS}
    def walk(name, prefix, mapping):
        pins, body = defs[name]
        if name in wanted:
            source_rows.append(dict(path=prefix, master=name, pins=mapping))
        for line in body:
            tokens = line.split()
            if not tokens or not tokens[0].upper().startswith('X') and '/' not in tokens:
                continue
            if '/' not in tokens:
                continue
            split = tokens.index('/'); child = tokens[split + 1].upper()
            if child not in defs:
                continue
            nodes = [mapping.get(n.upper(), prefix + '.' + n.upper()) for n in tokens[1:split]]
            assert len(nodes) == len(defs[child][0])
            walk(child, prefix + '.' + tokens[0].upper(), dict(zip([q.upper() for q in defs[child][0]], nodes)))
    top = 'PLACED_CORE_NOT_CONNECTED_FULLCHIP'
    walk(top, top, {q.upper(): q.upper() for q in defs[top][0]})
    rows = []
    for s in SPECS:
        aliases = sorted(n for n in occurrences if re.search(re.escape(s[0]) + r'(?:\$\d+)?$', n))
        ref = stock.cell(s[0]); assert ref
        for name in aliases:
            cell = ly.cell(name)
            differences = []
            for layer in sorted({(q.layer, q.datatype) for l in (ly, stock) for q in l.layer_infos()}):
                delta = region(ly, cell, pya.LayerInfo(*layer)) ^ region(stock, ref, pya.LayerInfo(*layer))
                if not delta.is_empty():
                    differences.append(dict(layer=list(layer), area_dbu2=delta.area(), polygons=delta.count()))
            rows.append(dict(stock_cell=s[0], alias=name, instances=len(occurrences[name]),
                             transforms=[str(t) for t in occurrences[name]], differences=differences,
                             text_equal=text_records(ly, cell) == text_records(stock, ref)))
        assert sum(len(occurrences[n]) for n in aliases) == s[-1]
        assert sum(r['master'] == s[0].upper() for r in source_rows) == s[-1]
    result = dict(status='passed' if all(not r['differences'] and r['text_equal'] for r in rows) else 'failed',
                  parent_sha256=PARENT, source_sha256=sha(a.source), script_sha256=sha(Path(__file__)),
                  geometry_aliases=rows, reachable_source_instances=source_rows)
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
