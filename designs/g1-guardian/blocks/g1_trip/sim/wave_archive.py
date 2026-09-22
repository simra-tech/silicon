"""Lossless archival of newly generated waves; immutable old runs are never swept."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil


def stream_digest(stream):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size


def archive_new_wave(path):
    """Caller must own a fresh run directory and have finished consuming the wave.

    Explicit opt-in; gzip is fsynced, decoded and checked, then the receipt is
    fsynced before the recoverable plain representation is removed. On any
    earlier exception the plain original remains. No directory traversal.
    """
    path = Path(path)
    if os.environ.get('G1_ARCHIVE_NEW_WAVES') != '1':
        return
    assert path.suffix == '.dat' and path.is_file() and not path.is_symlink()
    compressed = Path(str(path) + '.gz')
    receipt = Path(str(path) + '.archive.json')
    assert not compressed.exists() and not receipt.exists(), 'Never overwrite archives'
    with path.open('rb') as source:
        raw_sha, raw_size = stream_digest(source)
    with compressed.open('xb') as target:
        with gzip.GzipFile(filename='', mode='wb', fileobj=target, compresslevel=6, mtime=0) as encoded:
            with path.open('rb') as source:
                shutil.copyfileobj(source, encoded, 1024 * 1024)
        target.flush()
        os.fsync(target.fileno())
    with gzip.open(str(compressed), 'rb') as decoded:
        assert stream_digest(decoded) == (raw_sha, raw_size), 'Lossless roundtrip failed'
    with compressed.open('rb') as source:
        gzip_sha, gzip_size = stream_digest(source)
    record = {'status': 'passed', 'original_name': path.name,
              'gzip_name': compressed.name, 'original_sha256': raw_sha,
              'original_bytes': raw_size, 'gzip_sha256': gzip_sha,
              'gzip_bytes': gzip_size, 'gzip_level': 6,
              'archiver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Lossless saved waveform bytes; no waveform reduction or solver change.'}
    with receipt.open('x') as target:
        json.dump(record, target, indent=2)
        target.write('\n')
        target.flush()
        os.fsync(target.fileno())
    directory = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
        path.unlink()
        os.fsync(directory)
    finally:
        os.close(directory)


def resolve_wave(path):
    """Return plain wave or verified gzip; NumPy loadtxt supports the latter."""
    path = Path(path)
    if path.exists():
        return path
    compressed = Path(str(path) + '.gz')
    record = json.loads(Path(str(path) + '.archive.json').read_text())
    assert record['status'] == 'passed' and record['original_name'] == path.name
    assert record['gzip_name'] == compressed.name
    with compressed.open('rb') as source:
        assert stream_digest(source) == (record['gzip_sha256'], record['gzip_bytes']), 'Archive checksum mismatch'
    with gzip.open(str(compressed), 'rb') as decoded:
        assert stream_digest(decoded) == (record['original_sha256'], record['original_bytes']), 'Decoded waveform checksum mismatch'
    return compressed


def open_wave(path, mode='rt'):
    resolved = resolve_wave(path)
    return gzip.open(str(resolved), mode) if resolved.suffix == '.gz' else resolved.open(mode)


def wave_sha(path):
    with open_wave(path, 'rb') as stream:
        return stream_digest(stream)[0]
