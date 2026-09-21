#!/usr/bin/env python3
"""Fetch the unchanged public TI model into the ignored build tree."""
import hashlib,urllib.request,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
URL='https://www.ti.com/lit/zip/sllm127b'
EXPECTED='c5572438f1a79c8e9f48cfcf5a8d152daafdad8e8ec26ac30f807f0211edf2df'
p=ROOT/'build/g1_gate/vendor';p.mkdir(parents=True,exist_ok=True)
archive=urllib.request.urlopen(URL,timeout=60).read()
with zipfile.ZipFile(io.BytesIO(archive)) as z:data=z.read('CSD16340Q3.lib')
if hashlib.sha256(data).hexdigest()!=EXPECTED:raise SystemExit('Model changed: hash mismatch; refusing to use it')
for name,content in [('sllm127b.zip',archive),('CSD16340Q3.lib',data)]:
 out=p/name
 if out.exists() and out.read_bytes()!=content:raise SystemExit('Refusing to overwrite differing download: '+str(out))
 out.write_bytes(content)
print(p.relative_to(ROOT)/'CSD16340Q3.lib',EXPECTED)
