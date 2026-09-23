#!/usr/bin/env python3
"""Explicitly audit the two power ports added by the held powered source view."""
import hashlib
from pathlib import Path

original = Path(__file__).resolve().with_name('prepare.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == 'a6f7481a0726f0167733319d777f226dc914180f3aa3d31931a7dead5499f0d8'
text = original.read_text()
before = "assert lm == pm == 'g1_digital' and lp == pp and len(lp) == 46"
after = "assert lm == pm == 'g1_digital' and len(lp) == 44 and len(pp) == 46\n    assert 'VDD' not in lp and 'VSS' not in lp\n    assert lp == [p for p in pp if p not in ('VDD', 'VSS')]\n    assert pp.count('VDD') == pp.count('VSS') == 1"
assert text.count(before) == 1
text = text.replace(before, after)
text = text.replace('current_digital_instances=7771,', "current_digital_instances=7771, added_power_header_ports=['VDD','VSS'],")
exec(compile(text, str(original), 'exec'), globals())
