#!/usr/bin/env python3
"""Rename two clock instances in OpenDB with exact inverse DEF/roundtrip checks.

Run with the pinned OpenROAD -python interpreter. No placement/routing command
is called. The input database remains immutable; all outputs are fresh.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import odb


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    original_hash = sha(a.input)
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    started = time.monotonic()
    record = dict(status='running', input=str(a.input), input_sha256=original_hash)
    try:
        db = odb.dbDatabase.create()
        odb.read_db(db, str(a.input))
        block = db.getChip().getBlock()
        before = a.output/'before.def'
        after = a.output/'g1_digital.def'
        odb.write_def(block, str(before))
        old_bytes = before.read_bytes()
        names = {inst.getName() for inst in block.getInsts()}
        mapping = {}
        for i in (0, 1):
            old = 'clkbuf_fanout_split%d_osc_clk' % i
            new = old+'_cell'
            assert old in names and new not in names and new.encode() not in old_bytes
            inst = block.findInst(old)
            assert inst.getMaster().getName() == 'sg13g2_buf_16'
            assert inst.findITerm('X').getNet().getName() == old
            instance_id = inst.getId()
            inst.rename(new)
            # SWIG may return a distinct Python wrapper for the same DB object.
            found = block.findInst(new)
            assert inst.getName() == new and found and found.getId() == instance_id
            assert not block.findInst(old)
            mapping[old] = new
        odb.write_def(block, str(after))
        restored = after.read_bytes()
        for old, new in mapping.items():
            restored = restored.replace(new.encode(), old.encode())
        assert restored == old_bytes, 'Non-name DEF change'
        output_db = a.output/'g1_digital.odb'
        odb.write_db(db, str(output_db))
        reloaded = odb.dbDatabase.create()
        odb.read_db(reloaded, str(output_db))
        replay = a.output/'roundtrip.def'
        odb.write_def(reloaded.getChip().getBlock(), str(replay))
        assert replay.read_bytes() == after.read_bytes(), 'Saved OpenDB/DEF mismatch'
        assert sha(a.input) == original_hash
        record.update(status='passed exact inverse DEF and saved OpenDB roundtrip',
                      instances=len(names), mapping=mapping,
                      outputs_sha256={x.name:sha(x) for x in (before, after, output_db, replay)},
                      not_run=['Full downstream validation on renamed database', 'Adoption'],
                      not_applicable=['Analog simulation', 'Statistical seed'])
    except Exception as exc:
        record.update(status='failed database rename/control', error=repr(exc))
        raise
    finally:
        record['wall_s'] = time.monotonic()-started
        (a.output/'summary.json').write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
