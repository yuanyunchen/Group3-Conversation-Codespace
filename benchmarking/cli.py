"""Command-line interface for the benchmarking pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .config import generate_lineups
from .pipeline import run_benchmark


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tournament benchmarking batches.")
    parser.add_argument("test_player", help="Player preset code to benchmark (e.g., p3)")
    parser.add_argument("--round-name", required=True, help="Label for this benchmark run")
    parser.add_argument("--rounds", type=int, default=10, help="Number of Monte Carlo rounds")
    parser.add_argument("--seed", type=int, default=91, help="Base random seed")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output root directory (defaults to benchmarking/output/<round_name>)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run simulations even if results.csv already exists",
    )
    parser.add_argument(
        "--selection-method",
        dest="selection_methods",
        action="append",
        help="Restrict to specific selection methods (may be repeated)",
    )
    parser.add_argument(
        "--length",
        dest="lengths",
        type=int,
        action="append",
        help="Restrict to specific conversation lengths (may be repeated)",
    )
    parser.add_argument(
        "--subjects",
        dest="subjects",
        type=int,
        action="append",
        help="Restrict to specific subject counts (may be repeated)",
    )
    parser.add_argument(
        "--memory-tier",
        dest="memory_tiers",
        action="append",
        help="Restrict to specific memory tiers (keys from config.MEMORY_MULTIPLIERS)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Print the planned lineups and exit without running simulations",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        if args.list_only:
            lineups = generate_lineups(args.test_player)
            selection_filter = (
                {str(method) for method in args.selection_methods}
                if args.selection_methods
                else None
            )
            for lineup in lineups:
                if selection_filter and lineup.selection_method not in selection_filter:
                    continue
                print(
                    f"{lineup.selection_method}: {lineup.name} -> {lineup.player_counts}"
                )
            return 0

        csv_path = run_benchmark(
            test_player=args.test_player,
            round_name=args.round_name,
            rounds=args.rounds,
            seed=args.seed,
            output_root=args.output_dir,
            force=args.force,
            selection_methods=args.selection_methods,
            lengths=args.lengths,
            subject_counts=args.subjects,
            memory_tiers=args.memory_tiers,
        )
    except Exception as exc:  # noqa: BLE001 - CLI guardrail
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Aggregated results written to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
