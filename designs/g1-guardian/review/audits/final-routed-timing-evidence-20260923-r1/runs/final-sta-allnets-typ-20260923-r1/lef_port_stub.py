#!/usr/bin/env python3
"""Derive declaration-only analog bus interfaces from held LEF pin metadata.

These modules supply names, vector indices and directions, not timing arcs,
capacitance or analog functionality. Power pins remain inout declarations.
"""
import re


def port_stub(text, expected_name):
    macros = re.findall(r'^MACRO\s+(\w+)\s*$', text, re.M)
    assert macros == [expected_name], macros
    rows = re.findall(r'^\s+PIN\s+(\S+)\s*\n(.*?)^\s+END\s+\1\s*$', text, re.M | re.S)
    assert rows and len(rows) == len(re.findall(r'^\s+PIN\s+', text, re.M))
    pins = {}
    groups = {}
    for name, body in rows:
        directions = re.findall(r'^\s+DIRECTION\s+(INPUT|OUTPUT|INOUT)\s*;', body, re.M)
        assert len(directions) == 1 and name not in pins
        pins[name] = directions[0].lower()
        match = re.fullmatch(r'([A-Za-z_]\w*)(?:\[(\d+)\])?', name)
        assert match, name
        base, index = match.groups()
        groups.setdefault(base, []).append((None if index is None else int(index), pins[name]))
    declarations = []
    for base, entries in groups.items():
        directions = {direction for _, direction in entries}
        assert len(directions) == 1
        direction = next(iter(directions))
        indices = [index for index, _ in entries]
        if indices == [None]:
            declarations.append('{} {};'.format(direction, base))
        else:
            assert None not in indices
            assert sorted(indices) == list(range(max(indices) + 1))
            declarations.append('{} [{}:0] {};'.format(direction, max(indices), base))
    output = '// Declaration-only interface; no timing or analog model.\n'
    output += 'module {} ({});\n'.format(expected_name, ', '.join(groups))
    output += '\n'.join(declarations) + '\nendmodule\n'
    return output, pins
