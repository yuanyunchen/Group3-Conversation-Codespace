#!/usr/bin/env bash
# Example automation covering both single and multi pipelines.
set -euo pipefail

OUTPUT_ROOT="${1:-benchmarking/results}"
RUN_COMPLEX="${RUN_COMPLEX:-false}"
STAMP="$(date +%Y%m%d_%H%M%S)"

# Quick smoke tests (simple mode)
python -m benchmarking.cli \
  --pipeline single \
  --mode simple \
  --targets p3 \
  --output-root "${OUTPUT_ROOT}/${STAMP}_single_p3_simple" \
  --detailed \
  --clean-output

python -m benchmarking.cli \
  --pipeline multi \
  --mode simple \
  --targets p3 p_bst_medium \
  --output-root "${OUTPUT_ROOT}/${STAMP}_multi_simple" \
  --detailed \
  --clean-output

if [ "${RUN_COMPLEX}" = "true" ]; then
  python -m benchmarking.cli \
    --pipeline single \
    --mode complex \
    --targets p_bst_medium \
    --output-root "${OUTPUT_ROOT}/${STAMP}_single_bst_medium_complex" \
    --detailed \
    --clean-output

  python -m benchmarking.cli \
    --pipeline multi \
    --mode complex \
    --targets p3 p_bst_medium p_bst_high \
    --output-root "${OUTPUT_ROOT}/${STAMP}_multi_complex" \
    --detailed \
    --clean-output
fi
