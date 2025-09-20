#!/usr/bin/env bash
# Run the single-player benchmarking pipeline in simple or complex mode.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <player_code> [simple|complex] [output_root]"
  exit 1
fi

TARGET="$1"
MODE="${2:-simple}"
OUTPUT_ROOT="${3:-benchmarking/results}"
STAMP="$(date +%Y%m%d_%H%M%S)"

if [ "$MODE" != "simple" ] && [ "$MODE" != "complex" ]; then
  echo "Mode must be 'simple' or 'complex'." >&2
  exit 1
fi

python -m benchmarking.cli \
  --pipeline single \
  --mode "${MODE}" \
  --targets "${TARGET}" \
  --output-root "${OUTPUT_ROOT}/${STAMP}_single_${TARGET}_${MODE}" \
  --detailed \
  --clean-output
