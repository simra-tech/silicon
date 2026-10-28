# SPDX-License-Identifier: Apache-2.0
"""Ring LVS reference with one IOPadIOVss replaced by IOPadVss (track T8g, try h1 pad-map variant).

  python3 ring_cdl_padswap.py <ring projected reference .cdl> <out .cdl> <die pad 4|6>

The flat G1-form projected reference of the ring (r1_padring/netlist/r1_padring_1700_projected_ref.cdl) names every
device after its pad instance (PAD04_IOVSS.*). The script removes the devices of the given IOVSS pad and inserts a copy
of the devices of the VSS pad 5 (PAD05_VSS.*, the unmodified IOPadVss) under the name PADnn_VSS. Nets of the copied
devices are global (VSS, IOVSS, IOVDD), so the copy is the IOPadVss cell at the other position. Pins are unchanged.
Writes <out> and <out>.json (counts, sha256).
"""
import hashlib
import json
import sys

src, out, pad = sys.argv[1], sys.argv[2], int(sys.argv[3])
old_tag, new_tag = "PAD%02d_IOVSS." % pad, "PAD%02d_VSS." % pad
lines = open(src).read().split("\n")
# group into statements (a line plus its '+' continuations); comment lines are their own statement
st = []
for ln in lines:
    if ln.startswith("+") and st:
        st[-1].append(ln)
    else:
        st.append([ln])


def tagged(s, tag):
    h = s[0]
    if not h.strip():
        return False
    return tag in h.split()[0] or (h.startswith("* device instance ") and tag in h)


removed = [s for s in st if tagged(s, old_tag)]
copy = [[ln.replace("PAD05_VSS.", new_tag) for ln in s] for s in st if tagged(s, "PAD05_VSS.")]
internal = [s for s in copy if any(new_tag + "NET" in ln.upper() for ln in s)]
if internal:
    raise SystemExit("PAD05_VSS has internal nets; a copy needs renamed nets: %s" % internal[:2])
res, done = [], False
for s in st:
    if tagged(s, old_tag):
        if not done:
            res.extend(copy)
            done = True
        continue
    res.append(s)
if not done:
    raise SystemExit("no devices of %s in %s" % (old_tag, src))
txt = "\n".join(ln for s in res for ln in s)
open(out, "w").write(txt)
dev = lambda ss: sum(1 for s in ss if not s[0].startswith("*") and s[0].strip())
info = {"source": src, "source_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(), "output": out,
        "output_sha256": hashlib.sha256(txt.encode()).hexdigest(), "die_pad": pad,
        "devices_removed": dev(removed), "devices_inserted": dev(copy),
        "removed": [s[0] for s in removed if not s[0].startswith("*")],
        "inserted": [s[0] for s in copy if not s[0].startswith("*")]}
json.dump(info, open(out + ".json", "w"), indent=1)
print(json.dumps(info, indent=1))
