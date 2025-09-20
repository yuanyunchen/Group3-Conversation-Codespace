#!/usr/bin/env bash
# Generic runner for benchmarking pipelines with convenient flags.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_benchmark.sh --pipeline <single|multi|compare|scenario> [options]

Options:
  --pipeline <type>      Pipeline type: single, multi, compare, or scenario (static)
  --mode <simple|complex>   Mode for pipelines (default: simple)
  --targets "p1 p2 ..."  Space-separated player codes (required for single/multi)
  --scenario-key <key>    Scenario key when --pipeline scenario (default: default)
  --output <dir>          Output root directory (default: benchmarking/results/latest_run)
  --rounds <n>            Rounds per variant (passed to CLI)
  --lengths "..."         Override sweep lengths (space-separated)
  --player-counts "..."   Override total player counts
  --memory-sizes "..."    Override memory sizes
  --ratio-steps "..."     Override target ratios
  --competitors "..."     Override competitor list
  --base-seed <n>         Base seed override
  --detailed              Enable detailed outputs
  --help                  Show this message

Examples:
  run_benchmark.sh --pipeline single --mode simple --targets "p3" --rounds 3
  run_benchmark.sh --pipeline multi --mode complex --targets "p3 p_bst_medium p_bst_high" \
                   --output benchmarking/results/multi_run --rounds 2
  run_benchmark.sh --pipeline compare --mode simple --targets "p3 p_bst_medium" --rounds 2
  run_benchmark.sh --pipeline scenario --scenario-key default --rounds 5
EOF
}

PIPELINE=""
MODE="simple"
TARGETS=()
SCENARIO_KEY="default"
OUTPUT_ROOT="benchmarking/results/latest_run"
ROUNDS=""
LENGTHS=()
PLAYER_COUNTS=()
MEMORY_SIZES=()
RATIO_STEPS=()
COMPETITORS=()
BASE_SEED=""
DETAILED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pipeline)
      PIPELINE="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --targets)
      IFS=' ' read -r -a TARGETS <<< "$2"
      shift 2
      ;;
    --scenario-key)
      SCENARIO_KEY="$2"
      shift 2
      ;;
    --output)
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --rounds)
      ROUNDS="$2"
      shift 2
      ;;
    --lengths)
      IFS=' ' read -r -a LENGTHS <<< "$2"
      shift 2
      ;;
    --player-counts)
      IFS=' ' read -r -a PLAYER_COUNTS <<< "$2"
      shift 2
      ;;
    --memory-sizes)
      IFS=' ' read -r -a MEMORY_SIZES <<< "$2"
      shift 2
      ;;
    --ratio-steps)
      IFS=' ' read -r -a RATIO_STEPS <<< "$2"
      shift 2
      ;;
    --competitors)
      IFS=' ' read -r -a COMPETITORS <<< "$2"
      shift 2
      ;;
    --base-seed)
      BASE_SEED="$2"
      shift 2
      ;;
    --detailed)
      DETAILED=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$PIPELINE" ]]; then
  echo "--pipeline is required" >&2
  usage
  exit 1
fi

CLI_ARGS=("python" "-m" "benchmarking.cli" "--output-root" "$OUTPUT_ROOT" "--clean-output")
if [[ $DETAILED -eq 1 ]]; then
  CLI_ARGS+=("--detailed")
fi

case "$PIPELINE" in
  single|multi|compare)
    CLI_ARGS+=("--pipeline" "$PIPELINE" "--mode" "$MODE")
    if [[ ${#TARGETS[@]} -eq 0 ]]; then
      echo "--targets is required for pipeline '$PIPELINE'" >&2
      exit 1
    fi
    CLI_ARGS+=("--targets" "${TARGETS[@]}")
    ;;
  scenario)
    CLI_ARGS+=("--scenario" "$SCENARIO_KEY")
    ;;
  *)
    echo "Invalid pipeline type: $PIPELINE" >&2
    usage
    exit 1
    ;;
esac

if [[ -n "$ROUNDS" ]]; then
  CLI_ARGS+=("--rounds-per-variant" "$ROUNDS")
fi

if [[ ${#LENGTHS[@]} -gt 0 ]]; then
  CLI_ARGS+=("--lengths" "${LENGTHS[@]}")
fi
if [[ ${#PLAYER_COUNTS[@]} -gt 0 ]]; then
  CLI_ARGS+=("--player-counts" "${PLAYER_COUNTS[@]}")
fi
if [[ ${#MEMORY_SIZES[@]} -gt 0 ]]; then
  CLI_ARGS+=("--memory-sizes" "${MEMORY_SIZES[@]}")
fi
if [[ ${#RATIO_STEPS[@]} -gt 0 ]]; then
  CLI_ARGS+=("--ratio-steps" "${RATIO_STEPS[@]}")
fi
if [[ ${#COMPETITORS[@]} -gt 0 ]]; then
  CLI_ARGS+=("--competitors" "${COMPETITORS[@]}")
fi
if [[ -n "$BASE_SEED" ]]; then
  CLI_ARGS+=("--base-seed" "$BASE_SEED")
fi

echo "Running: ${CLI_ARGS[*]}"
"${CLI_ARGS[@]}"
