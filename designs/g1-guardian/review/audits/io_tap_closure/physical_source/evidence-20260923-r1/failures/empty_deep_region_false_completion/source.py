#!/usr/bin/env python3
"""Preserve actual top-level mask context, rather than assuming it empty."""
import hashlib
from pathlib import Path

original=Path(__file__).resolve().with_name('derive_deep_taps.py')
assert hashlib.sha256(original.read_bytes()).hexdigest()=='807728ad04759d323959ba29a83c97ccff0db02c55c11f4cf5a9db04fa127b96'
code=original.read_text()
needle="        assert all(top.shapes(ly.layer(*layers[n])).is_empty() for n in required)\n        assert top.shapes(ly.layer(63,0)).is_empty()"
assert code.count(needle)==1
code=code.replace(needle,"        result['preserved_direct_top_inputs']=[dict(layer=n,shapes=top.shapes(ly.layer(*layers[n])).size(),area_dbu2=pya.Region(top.shapes(ly.layer(*layers[n]))).area()) for n in required]\n        result['preserved_top_text63_shapes']=top.shapes(ly.layer(63,0)).size()")
code=code.replace('scoped IO subset','scoped140 IO instances plus all exact original top-level raw mask context')
exec(compile(code,str(original),'exec'),globals())
