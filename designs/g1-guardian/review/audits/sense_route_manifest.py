"""Validate the artifact binding before using candidate route estimates in SPICE."""
import hashlib
import json
import math
from pathlib import Path


def load_candidate_resistances(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    candidate_path = manifest_path.parent / 'g1_chip_top.gds'
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    if digest != manifest.get('candidate_sha256'):
        raise ValueError('Candidate GDS does not match route manifest SHA256')
    rows = manifest.get('routes')
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError('Manifest must contain exactly one P route and one N route')
    values = {}
    for row in rows:
        name = row.get('net')
        if name not in ('P', 'N') or name in values:
            raise ValueError('Route names must be distinct P and N')
        value = row.get('total_R_ohm_estimate')
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Route resistance must be numeric')
        if not math.isfinite(value) or value <= 0:
            raise ValueError('Route resistance must be finite and positive')
        values[name] = value
    return manifest, values
