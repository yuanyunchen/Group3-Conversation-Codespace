#!/bin/zsh

set -euo pipefail

# Example 1: BalancedGreedy vs Random, mid-length
uv run python -m benchmarks.runner \
  --scenario custom_balanced_vs_random \
  --players p_balanced_greedy:4,pr:4 \
  --subjects 20 --memory_size 20 --length 100 \
  --rounds 5 --seed 123 \
  --output results/benchmarks/custom_balanced_vs_random.csv

# Example 2: Zipper + Greedy + Random
uv run python -m benchmarks.runner \
  --scenario custom_zipper_greedy_random \
  --players p_zipper:3,p_balanced_greedy:3,pr:2 \
  --subjects 20 --memory_size 50 --length 200 \
  --rounds 3 --seed 42 \
  --output results/benchmarks/custom_zipper_greedy_random.csv

# Example 3: BST medium vs itself, long talk
uv run python -m benchmarks.runner \
  --scenario custom_bst_medium_self \
  --players p_bst_medium:8 \
  --subjects 20 --memory_size 20 --length 200 \
  --rounds 5 --seed 91 \
  --output results/benchmarks/custom_bst_medium_self.csv

echo "Custom examples complete. CSVs in results/benchmarks/"


