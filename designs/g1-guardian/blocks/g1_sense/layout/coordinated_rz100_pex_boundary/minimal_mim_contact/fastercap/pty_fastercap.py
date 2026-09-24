#!/usr/bin/env python3
"""Output-only PTY relay for the pinned FasterCap executable."""
import errno
import os
import subprocess
import sys


def main():
    master, slave = os.openpty()
    try:
        proc = subprocess.Popen(['/foss/tools/bin/FasterCap', *sys.argv[1:]],
                                stdin=subprocess.DEVNULL, stdout=slave,
                                stderr=subprocess.STDOUT, close_fds=True)
    finally:
        os.close(slave)
    try:
        while True:
            try:
                block = os.read(master, 16384)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not block:
                break
            sys.stdout.buffer.write(block)
            sys.stdout.buffer.flush()
    finally:
        os.close(master)
    raise SystemExit(proc.wait())


if __name__ == '__main__':
    main()
