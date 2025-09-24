#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Configuration (edit values here or export env vars to override).
# Allow first positional argument to override TEST_PLAYER env variable.
if [ $# -ge 1 ]; then
  TEST_PLAYER=$1
  shift
fi

TEST_PLAYER=${TEST_PLAYER:-p3}

ROUNDS=${ROUNDS:-5}                     # Monte Carlo rounds per configuration
SEED=${SEED:-91}                         # Base seed for simulations
ROUND_PREFIX=${ROUND_PREFIX:-compare_mixed_zipper_player_0923_5rounds_simple}  # Prefix for round names
MODE=${MODE:-simple}                       # full | short | simple
MAX_TIME=${MAX_TIME:-30}                   # Optional timeout (seconds) per game

OUTPUT_DIR=${OUTPUT_DIR:-}               # Optional output directory (blank = auto)
FORCE=${FORCE:-false}                    # Set to "true" to force reruns
# ----------------------------------------------------------------------------

# Run the benchmarking pipeline for a single test player.
# Usage:
#   TEST_PLAYER=p3 ./shells/run_benchmarking.sh

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

if ! command -v python >/dev/null 2>&1; then
  echo "python is required to run the benchmarking pipeline" >&2
  exit 1
fi

python_args_base=(
  --rounds "${ROUNDS}"
  --seed "${SEED}"
  --mode "${MODE}"
)

if [ -n "${MAX_TIME}" ]; then
  python_args_base+=(--max-time "${MAX_TIME}")
fi

if [ -n "${OUTPUT_DIR}" ]; then
  python_args_base+=(--output-dir "${OUTPUT_DIR}")
fi

if [ "${FORCE}" = "true" ]; then
  python_args_base+=(--force)
fi

round_name="${ROUND_PREFIX}_${TEST_PLAYER}"
echo "[benchmark] Running pipeline for ${TEST_PLAYER} (round: ${round_name})"
python -m benchmarking "${TEST_PLAYER}" \
  --round-name "${round_name}" \
  "${python_args_base[@]}"
