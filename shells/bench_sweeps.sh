#!/bin/zsh

set -euo pipefail

# Long conversations with varying random ratios
uv run python -m benchmarks.sweeps \
  --scenario long_conversation \
  --total_players 8 \
  --random_code pr \
  --random_ratios 0.0 0.25 0.5 0.75 \
  --lengths 100 200 \
  --memory_sizes 20 50 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/long_conversation_sweep.csv

# Self-collaboration: each type vs itself
uv run python -m benchmarks.sweeps \
  --scenario self_collaboration \
  --player_types p_balanced_greedy p_selfless_greedy p_selfish_greedy p_bst_low p_bst_medium p_bst_high \
  --total_players 8 \
  --lengths 50 100 \
  --memory_sizes 10 20 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/self_collab_sweep.csv

# Complex environment with heterogeneous mixes
uv run python -m benchmarks.sweeps \
  --scenario complex_environment \
  --lengths 100 \
  --memory_sizes 50 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/complex_env_sweep.csv

# Vary random ratio against a base mix
uv run python -m benchmarks.sweeps \
  --scenario vs_random_ratio \
  --base_mix p_balanced_greedy:4,p_bst_low:4 \
  --random_code pr \
  --random_ratios 0.0 0.25 0.5 0.75 1.0 \
  --total_players 8 \
  --lengths 50 100 \
  --memory_sizes 10 20 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/vs_random_ratio_sweep.csv

# BST effort sweep: each effort vs itself
uv run python -m benchmarks.sweeps \
  --scenario bst_effort_self \
  --efforts p_bst_low p_bst_medium p_bst_high \
  --total_players 8 \
  --lengths 50 100 \
  --memory_sizes 20 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/bst_effort_self_sweep.csv

# BST effort sweep: each effort in mixed opponents
uv run python -m benchmarks.sweeps \
  --scenario bst_effort_mixed \
  --efforts p_bst_low p_bst_medium p_bst_high \
  --total_players 8 \
  --lengths 50 100 \
  --memory_sizes 20 \
  --subjects_list 20 \
  --rounds 3 \
  --seed 91 \
  --output results/benchmarks/bst_effort_mixed_sweep.csv

# Seed sensitivity for a fixed config
uv run python -m benchmarks.sweeps \
  --scenario seed_sensitivity \
  --players_single p_balanced_greedy:4,pr:4 \
  --seed_start 91 \
  --seeds_count 20 \
  --output results/benchmarks/seed_sensitivity.csv

echo "All sweeps submitted. CSVs written under results/benchmarks/"


