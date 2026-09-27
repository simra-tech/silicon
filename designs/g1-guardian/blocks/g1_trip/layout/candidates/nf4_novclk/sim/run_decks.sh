#!/usr/bin/env bash
# container side: run every deck given, NPAR at a time (default 8), each ngspice single-threaded; stdout without the
# transient progress lines goes to <deck>.log (stderr to <deck>.err)
printf '%s\n' "$@" | xargs -P "${NPAR:-8}" -I{} sh -c 'ngspice -b "{}" 2> "{}.err" | grep -av "Reference value" > "{}.log"'
