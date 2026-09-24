#!/usr/bin/env python3
"""Mechanical allowed-ID extension of the qualified cohort1 clip logic."""
import hashlib
from pathlib import Path

path=Path(__file__).with_name('prepare_local_via_cohort1_clip.py')
assert hashlib.sha256(path.read_bytes()).hexdigest()=='7488f5b634e5fd0e6eec6f98df211676659904906017856fafb903639526d935'
text=path.read_text()
assert text.count('choices=[0,1,5,6]')==1
text=text.replace('choices=[0,1,5,6]','choices=[7,8,9,16,11,12,13,14,15,17,18,20]')
text=text.replace('Cohort1 stages0/1/5/6 only; no automatic expansion.','Explicit remaining stage selection; same12x12 boundaries and checks.')
exec(compile(text,str(path),'exec'),dict(__file__=__file__,__name__='remaining_local_clip'))
