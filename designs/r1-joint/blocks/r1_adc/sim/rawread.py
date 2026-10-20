#!/usr/bin/env python3
"""Minimal ngspice binary raw reader (real transient data). read(path, names) -> dict name -> numpy array."""
import numpy as np


def read(path, names=None):
    with open(path, "rb") as f:
        data = f.read()
    i = data.index(b"Binary:\n")
    hdr = data[:i].decode("latin-1").splitlines()
    nv = int([l for l in hdr if l.startswith("No. Variables:")][0].split(":")[1])
    npnt = int([l for l in hdr if l.startswith("No. Points:")][0].split(":")[1])
    k = hdr.index("Variables:")
    var = [hdr[k + 1 + j].split()[1] for j in range(nv)]
    arr = np.frombuffer(data[i + 8:i + 8 + nv * npnt * 8], dtype="<f8").reshape(npnt, nv)
    want = var if names is None else names
    out = {}
    for n in want:
        out[n] = arr[:, var.index(n)]
    return out, var
