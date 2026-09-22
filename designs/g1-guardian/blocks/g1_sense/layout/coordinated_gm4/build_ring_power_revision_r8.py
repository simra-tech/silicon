#!/usr/bin/env python3
"""Isolated r8: 5 um wide-ring parallel spacing, preserving r7 and nine ports."""
import sys
from pathlib import Path
from build_native_prototypes import sha

HERE=Path(__file__).resolve().parent


def main():
    original=HERE/'build_ring_power_revision.py'
    assert sha(original)=='545f1fe226a2974bf0ffdd2fb3eb79782f3f48c5c7688def0d004a1fe33a7fed'
    text=original.read_text()
    changes=[
        ('[(36,172),(383,172)', '[(40,172),(383,172)'),
        ("('vdd',(36.,54.", "('vdd',(40.,54."),
        ("escape=36. if net=='vdd'", "escape=40. if net=='vdd'"),
        ('stem=36. if dx==0.', 'stem=40. if dx==0.'),
        ('left>=33160','left>=36160'),
        ('required_min_local_x_um=33.16','required_min_local_x_um=36.16'),
    ]
    for old,new in changes:
        assert text.count(old)==(2 if old=='left>=33160'else 1),old
        text=text.replace(old,new)
    output=Path(sys.argv[sys.argv.index('--output')+1])
    prep=output.with_name(output.name+'-r8-adapter')
    assert not prep.exists()
    prep.mkdir(parents=True)
    (prep/'derived_adapter.py').write_text(text)
    (prep/'r8_adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    namespace={'__file__':str(original),'__name__':'ring_r8_adapter'}
    exec(compile(text,str(prep/'derived_adapter.py'),'exec'),namespace)
    namespace['main']()


if __name__=='__main__':
    main()
