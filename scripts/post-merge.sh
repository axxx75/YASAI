#!/usr/bin/env bash
set -euo pipefail

# YASAI has no dependency lockfile or database migrations. Keep post-merge
# setup deterministic and fast by checking Python syntax without importing
# modules or contacting external services.
python3 -m compileall -q agent-router