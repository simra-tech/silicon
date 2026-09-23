#!/usr/bin/env python3
"""Independent hierarchy control: direct active ownership versus child subtraction."""
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent
original = here/'audit_dimensions.py'
assert hashlib.sha256(original.read_bytes()).hexdigest() == 'c82957847dea49bf02e0b36de22e9dbe06d1c98531f42eab9324e0bc4c4f5a4c'
analytical = here/'audit_dimensions_r2.py'
assert hashlib.sha256(analytical.read_bytes()).hexdigest() == '835beb602aa89fd75e0316b473047586336b58f6b6b594cd30bc84758c6d8965'
text = analytical.read_text()
scope = {'__file__':str(analytical),'__name__':'geometry_only_analytical_function'}
exec(compile(text[:text.index('\noriginal = Path')],str(analytical),'exec'),scope)
code = original.read_text()
needle = 'own = (reg-inherited[kind]).merged()'
assert code.count(needle) == 1
code = code.replace(needle, "direct = pya.Region(cell.shapes(ly.layer(*layers['activ_drw'])))+pya.Region(cell.shapes(ly.layer(*layers['activ_filler'])))\n                own = (reg & direct).merged()")
assert code.count("source_geometry_bijection=") == 1
code = code.replace("source_geometry_bijection='not run; no source parameter replacement from aggregate inventory'", "source_geometry_bijection='not run; direct-active ownership hypothesis only, not source adopted'")
namespace = {'__file__':str(Path(__file__).resolve()),'__name__':'direct_active_hierarchy_control'}
exec(compile(code,str(original),'exec'),namespace)
namespace['polygon_record'] = scope['polygon_record']
namespace['main']()
