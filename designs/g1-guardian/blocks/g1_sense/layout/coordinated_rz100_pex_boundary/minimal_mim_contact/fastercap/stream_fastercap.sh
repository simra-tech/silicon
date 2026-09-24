#!/bin/sh
# Output-only adapter: leave FasterCap argv and environment otherwise intact.
exec /usr/bin/stdbuf -oL -eL /foss/tools/bin/FasterCap "$@"
