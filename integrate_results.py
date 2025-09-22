#!/usr/bin/env python3
"""Aggregate player results across test outputs into a single CSV."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import OrderedDict
from typing import Iterable, Set

from players.player_mapping import PLAYER_CODE_TO_CLASS

PRESET_TO_TYPE_NAME: dict[str, str] = {
    preset: cls.__name__ for preset, cls in PLAYER_CODE_TO_CLASS.items()
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Integrate per-test CSV results for a specific player into a single file."
        )
    )
    parser.add_argument(
        "path",
        help=(
            "Path to the directory containing per-test result subdirectories (each "
            "with a results.csv file)."
        ),
    )
    parser.add_argument(
        "test_player",
        help="Player name to extract from each results.csv (matches the 'type' column).",
    )
    return parser.parse_args()


def collect_test_files(base_path: str) -> list[tuple[str, str]]:
    """
    Return a sorted list of (test_name, csv_path) tuples for each subdirectory
    directly under base_path that contains a results.csv file.
    """
    test_files: list[tuple[str, str]] = []
    try:
        with os.scandir(base_path) as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                csv_path = os.path.join(entry.path, "results.csv")
                if os.path.isfile(csv_path):
                    test_files.append((entry.name, csv_path))
    except FileNotFoundError:
        return []

    test_files.sort(key=lambda item: item[0])
    return test_files


def extract_player_row(
    csv_path: str, player_names: Iterable[str]
) -> dict[str, str] | None:
    """Return the CSV row matching any accepted player name in the 'type' column."""
    accepted: Set[str] = {name for name in player_names if name}
    if not accepted:
        return None
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("type") in accepted:
                return row
    return None


def integrate_results(base_path: str, player: str) -> str:
    """
    Integrate metrics for the requested player across each test.

    Returns the path of the generated CSV file.
    """
    test_files = collect_test_files(base_path)
    if not test_files:
        raise FileNotFoundError(
            f"No per-test results found under '{base_path}'. Expected subdirectories "
            "with results.csv files."
        )

    metric_order: list[str] | None = None
    test_rows: OrderedDict[str, OrderedDict[str, str]] = OrderedDict()
    tests_with_missing_player: list[str] = []

    candidate_names = resolve_player_names(player)

    for test_name, csv_path in test_files:
        row = extract_player_row(csv_path, candidate_names)
        if row is None:
            tests_with_missing_player.append(test_name)
            continue

        if metric_order is None:
            metric_order = [field for field in row.keys() if field != "type"]

        ordered_values = OrderedDict()
        for metric in metric_order:
            ordered_values[metric] = row.get(metric, "")
        test_rows[test_name] = ordered_values

    if not test_rows:
        resolved_names = "', '".join(sorted(candidate_names))
        raise ValueError(
            f"Player '{player}' (resolved as '{resolved_names}') was not found in any "
            f"results.csv under '{base_path}'."
        )

    output_filename = f"{os.path.basename(os.path.normpath(base_path))}.csv"
    output_path = os.path.join(base_path, output_filename)

    test_names = [name for name, _ in test_files if name in test_rows]

    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        header = ["test", *(metric_order or [])]
        writer.writerow(header)
        for test_name in test_names:
            values = test_rows[test_name]
            row = [test_name]
            for metric in metric_order or []:
                row.append(values.get(metric, ""))
            writer.writerow(row)

    if tests_with_missing_player:
        missing = ", ".join(tests_with_missing_player)
        print(
            f"Warning: Player '{player}' not found in tests: {missing}",
            file=sys.stderr,
        )

    return output_path


def resolve_player_names(player: str) -> Set[str]:
    """Return the set of CSV type names associated with the requested player value."""
    names: Set[str] = {player}
    mapped = PRESET_TO_TYPE_NAME.get(player)
    if mapped:
        names.add(mapped)
    return names


def main() -> int:
    args = parse_args()
    base_path = os.path.abspath(args.path)

    if not os.path.isdir(base_path):
        print(f"Error: '{args.path}' is not a directory", file=sys.stderr)
        return 1

    try:
        output_path = integrate_results(base_path, args.test_player)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Aggregated results written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
