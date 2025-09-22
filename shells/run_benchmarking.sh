#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Configuration (override via export ROUNDS=..., etc., or edit here).
# ROUNDS=${ROUNDS:-10}            # Monte Carlo rounds per configuration
# SEED=${ID:-91}                # Base seed for simulations
# ROUND_PREFIX=${ROUND_PREFIX:-benchmark}  # Prefix for round names


ROUNDS=10           # Monte Carlo rounds per configuration
SEED=${ID:-91}                # Base seed for simulations
ROUND_PREFIX="test_benchmakring_pipeline"  # Prefix for round names


OUTPUT_DIR=${OUTPUT_DIR:-}      # Optional output directory
FORCE=${FORCE:-false}           # Set to "true" to force reruns
PLAYERS_DEFAULT=(p1 p2 p4 p5 p6 p7 p8 p9 p10 pr)
# ----------------------------------------------------------------------------

# Run the benchmarking pipeline for one or more test players.
# Usage:
#   ./shells/run_benchmarking.sh [p1 p2 ...]

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

if ! command -v python >/dev/null 2>&1; then
  echo "python is required to run the benchmarking pipeline" >&2
  exit 1
fi

# Players to benchmark (defaults to full roster excluding p3 unless provided).
if [ "$#" -gt 0 ]; then
  PLAYERS=("$@")
else
  PLAYERS=(p1 p2 p4 p5 p6 p7 p8 p9 p10 pr)
fi

ROUNDS=${ROUNDS:-10}
SEED=${SEED:-91}
ROUND_PREFIX=${ROUND_PREFIX:-benchmark}
OUTPUT_DIR=${OUTPUT_DIR:-}
FORCE=${FORCE:-false}

python_args_base=(
  --rounds "${ROUNDS}"
  --seed "${SEED}"
)

if [ -n "${OUTPUT_DIR}" ]; then
  python_args_base+=(--output-dir "${OUTPUT_DIR}")
fi

if [ "${FORCE}" = "true" ]; then
  python_args_base+=(--force)
fi

for player in "${PLAYERS[@]}"; do
  round_name="${ROUND_PREFIX}_${player}"
  echo "[benchmark] Running pipeline for ${player} (round: ${round_name})"
  python -m benchmarking "${player}" \
    --round-name "${round_name}" \
    "${python_args_base[@]}"
done
