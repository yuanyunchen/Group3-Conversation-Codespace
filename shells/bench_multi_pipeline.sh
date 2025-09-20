#!/usr/bin/env bash
# Run the multi-player benchmarking pipeline in simple or complex mode.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  cat <<EOF
Usage: $0 <player_code_1> <player_code_2> [player_code_3 ...] [--mode simple|complex] [--output <output_root>]
Example: $0 p3 p_bst_medium p_bst_high --mode complex --output benchmarking/results
EOF
  exit 1
fi

MODE="simple"
OUTPUT_ROOT="benchmarking/results"
TARGETS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    simple|complex)
      MODE="$1"
      shift
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

if [ ${#TARGETS[@]} -lt 2 ]; then
  echo "Multi pipeline requires at least two target player codes." >&2
  exit 1
fi

if [ "$MODE" != "simple" ] && [ "$MODE" != "complex" ]; then
  echo "Mode must be 'simple' or 'complex'." >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"

python -m benchmarking.cli \
  --pipeline multi \
  --mode "${MODE}" \
  --targets "${TARGETS[@]}" \
  --output-root "${OUTPUT_ROOT}/${STAMP}_multi_${MODE}" \
  --detailed \
  --clean-output
