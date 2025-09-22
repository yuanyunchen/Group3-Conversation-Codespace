"""Benchmarking pipeline orchestration."""

from __future__ import annotations

import csv
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from players.player_mapping import PLAYER_CODE_TO_CLASS

from .config import (
    MEMORY_MULTIPLIERS,
    SUBJECT_COUNTS,
    CONVERSATION_LENGTHS,
    Lineup,
    derive_memory_size,
    generate_lineups,
)

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - tqdm optional dependency
    tqdm = None

CLASS_NAME_TO_CODE = {
    cls.__name__: code for code, cls in PLAYER_CODE_TO_CLASS.items()
}

METRIC_KEYS = [
    "score",
    "individual",
    "shared_score",
    "contributed_individual_score",
    "contributed_shared_score",
    "involvement_ratio",
    "importance",
    "coherence",
    "freshness",
    "nonmonotone",
]


def _normalize_value(value: float | int | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


@dataclass
class BenchmarkConfig:
    lineup: Lineup
    length: int
    subjects: int
    memory_tier: str
    memory_size: int

    @property
    def key(self) -> str:
        return f"L{self.length}_S{self.subjects}_B{self.memory_size}_{self.memory_tier}"


def _resolve_player_class(code: str) -> str:
    cls = PLAYER_CODE_TO_CLASS.get(code)
    if cls is None:
        raise ValueError(f"Unknown player code: {code}")
    return cls.__name__


def _format_player_counts(player_counts: dict[str, int]) -> str:
    parts = [f"{code}x{player_counts[code]}" for code in sorted(player_counts)]
    return ";".join(parts)


def _run_simulation(
    repo_root: Path,
    test_player: str,
    config_dir: Path,
    config: BenchmarkConfig,
    rounds: int,
    seed: int,
    force: bool,
) -> Path:
    target_csv = config_dir.parent / f"{config.key}.csv"

    if target_csv.exists():
        if force:
            target_csv.unlink()
        else:
            return target_csv

    if config_dir.exists() and config_dir.is_dir() and force:
        shutil.rmtree(config_dir)

    config_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [sys.executable, "main.py"]
    for code, count in config.lineup.player_counts.items():
        cmd.extend(["--player", code, str(count)])
    cmd.extend(
        [
            "--length",
            str(config.length),
            "--memory_size",
            str(config.memory_size),
            "--subjects",
            str(config.subjects),
            "--rounds",
            str(rounds),
            "--seed",
            str(seed),
            "--output_path",
            str(config_dir),
            "--test_player",
            test_player,
        ]
    )

    print(f"[benchmark] Running {' '.join(cmd)}")
    subprocess.run(cmd, cwd=repo_root, check=True)

    results_csv = config_dir / "results.csv"
    if not results_csv.exists():
        raise FileNotFoundError(f"results.csv not produced at {results_csv}")

    target_csv.parent.mkdir(parents=True, exist_ok=True)
    results_csv.replace(target_csv)

    try:
        shutil.rmtree(config_dir)
    except OSError:
        pass

    return target_csv


def _parse_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _extract_metrics(results_csv: Path) -> list[dict[str, object]]:
    with results_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in {results_csv}")

    sorted_rows = sorted(rows, key=lambda row: _parse_float(row.get("score")), reverse=True)
    ranks: dict[str, int] = {}
    for idx, row in enumerate(sorted_rows, start=1):
        player_type = row.get("type", "")
        ranks[player_type] = idx

    entries: list[dict[str, object]] = []
    for row in rows:
        player_type = row.get("type", "")
        metrics: dict[str, float] = {}
        for key, value in row.items():
            if key == "type":
                continue
            metrics[key] = _parse_float(value)
        metrics.setdefault("player_numbers", 0.0)
        entries.append(
            {
                "class_name": player_type,
                "rank": ranks.get(player_type, 0),
                "metrics": metrics,
            }
        )

    return entries


def _build_rows(
    *,
    data_rows: list[dict[str, float | int | str]],
    output_csv: Path,
    player_label: str,
    round_name: str,
) -> None:
    headers = [
        "round_name",
        "Player",
        "selection_method",
        "lineup_name",
        "description",
        "P",
        "L",
        "B",
        "memory_tier",
        "S",
        "rounds",
        "rank",
        "player_numbers",
        "player_info",
        "score",
        "individual",
        "shared_score",
        "contributed_individual_score",
        "contributed_shared_score",
        "involvement_ratio",
        "importance",
        "coherence",
        "freshness",
        "nonmonotone",
    ]

    sorted_rows = sorted(
        data_rows,
        key=lambda row: (
            row["Player"],
            row["P"],
            row["L"],
            row["B"],
            row["S"],
            row["selection_method"],
            row["lineup_name"],
        ),
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in sorted_rows:
            writer.writerow({key: _normalize_value(row.get(key, "")) for key in headers})

        if sorted_rows:
            summary = _summary_row(sorted_rows, player_label, round_name)
            writer.writerow({key: _normalize_value(summary.get(key, "")) for key in headers})


def _summary_row(
    rows: list[dict[str, float | int | str]],
    player_label: str,
    round_name: str,
) -> dict[str, str | float | int]:
    numeric_fields = [
        "rank",
        "score",
        "individual",
        "shared_score",
        "contributed_individual_score",
        "contributed_shared_score",
        "involvement_ratio",
        "importance",
        "coherence",
        "freshness",
        "nonmonotone",
    ]
    summary: dict[str, float | int | str] = {key: "" for key in rows[0].keys()}
    summary.update(
        {
            "Player": player_label,
            "round_name": round_name,
            "lineup_name": "summary",
            "selection_method": "all",
            "description": "Averages across configurations",
        }
    )

    for key in numeric_fields:
        values = [float(row[key]) for row in rows if key in row]
        if values:
            summary[key] = statistics.mean(values)

    summary["P"] = ""
    summary["L"] = ""
    summary["B"] = ""
    summary["S"] = ""
    summary["rounds"] = ""
    summary["player_numbers"] = ""
    summary["player_info"] = ""
    summary["memory_tier"] = ""
    return summary


def run_benchmark(
    *,
    test_player: str,
    round_name: str,
    rounds: int,
    seed: int = 91,
    output_root: Path | None = None,
    force: bool = False,
    selection_methods: Iterable[str] | None = None,
    lengths: Iterable[int] | None = None,
    subject_counts: Iterable[int] | None = None,
    memory_tiers: Iterable[str] | None = None,
) -> Path:
    """Run the benchmarking pipeline and return the aggregated CSV path."""

    rounds = max(10, rounds)

    repo_root = Path(__file__).resolve().parents[1]
    output_root = (
        Path(output_root)
        if output_root is not None
        else repo_root / "benchmarking" / "output" / round_name
    )
    output_root.mkdir(parents=True, exist_ok=True)

    lineups = generate_lineups(test_player)
    player_class_name = _resolve_player_class(test_player)

    selection_filter = (
        {str(method) for method in selection_methods}
        if selection_methods is not None
        else None
    )
    length_options = list(lengths) if lengths is not None else CONVERSATION_LENGTHS
    subject_options = (
        list(subject_counts) if subject_counts is not None else SUBJECT_COUNTS
    )
    if memory_tiers is not None:
        memory_map = {name: MEMORY_MULTIPLIERS[name] for name in memory_tiers}
    else:
        memory_map = MEMORY_MULTIPLIERS

    aggregated_rows: list[dict[str, float | int | str]] = []
    per_player_rows: defaultdict[str, list[dict[str, float | int | str]]] = defaultdict(list)

    active_lineups = [
        lineup for lineup in lineups if not selection_filter or lineup.selection_method in selection_filter
    ]

    cases_per_lineup = len(length_options) * len(subject_options) * len(memory_map)
    total_cases = cases_per_lineup * len(active_lineups)
    progress = (
        tqdm(total=total_cases, desc=f"{test_player} configs", unit="case")
        if (tqdm and total_cases)
        else None
    )

    for lineup in active_lineups:
        lineup_dir = f"{lineup.selection_method}_{lineup.name}"

        for length in length_options:
            for subjects in subject_options:
                for tier_name, multiplier in memory_map.items():
                    memory_size = derive_memory_size(length, lineup.total_players, multiplier)
                    config = BenchmarkConfig(
                        lineup=lineup,
                        length=length,
                        subjects=subjects,
                        memory_tier=tier_name,
                        memory_size=memory_size,
                    )
                    config_dir = (
                        output_root
                        / "all_rounds"
                        / lineup_dir
                        / config.key
                    )
                    try:
                        results_csv = _run_simulation(
                            repo_root,
                            test_player,
                            config_dir,
                            config,
                            rounds,
                            seed,
                            force,
                        )
                    except subprocess.CalledProcessError as exc:
                        print(f"[benchmark] Simulation failed for {config_dir}: {exc}")
                        if progress:
                            progress.update(1)
                        continue

                    try:
                        entries = _extract_metrics(results_csv)
                    except ValueError as exc:
                        print(f"[benchmark] {exc}")
                        if progress:
                            progress.update(1)
                        continue

                    participant_counts = _format_player_counts(config.lineup.player_counts)

                    for entry in entries:
                        class_name = entry.get("class_name", "")
                        player_code = CLASS_NAME_TO_CODE.get(class_name, class_name)
                        metrics = entry.get("metrics", {})
                        player_numbers = int(round(metrics.get("player_numbers", 0.0)))

                        row: dict[str, float | int | str] = {
                            "round_name": round_name,
                            "Player": player_code,
                            "selection_method": lineup.selection_method,
                            "lineup_name": config.lineup.name,
                            "description": config.lineup.description,
                            "P": config.lineup.total_players,
                            "L": config.length,
                            "B": config.memory_size,
                            "memory_tier": tier_name,
                            "S": config.subjects,
                            "rounds": rounds,
                            "rank": entry.get("rank", 0),
                            "player_numbers": player_numbers,
                            "player_info": participant_counts,
                        }

                        for key in METRIC_KEYS:
                            row[key] = metrics.get(key, 0.0)

                        per_player_rows[player_code].append(row)

                        if player_code == test_player or class_name == player_class_name:
                            aggregated_rows.append(row)

                    if progress:
                        progress.update(1)

    if progress:
        progress.close()

    aggregated_csv = output_root / f"{test_player}_benchmark.csv"
    if aggregated_rows:
        _build_rows(
            data_rows=aggregated_rows,
            output_csv=aggregated_csv,
            player_label=test_player,
            round_name=round_name,
        )
    else:
        print("[benchmark] No data collected; aggregated CSV not created.")
    other_players_dir = output_root / "other_players"
    for code, rows in sorted(per_player_rows.items()):
        if code == test_player:
            continue
        if not rows:
            continue
        output_path = other_players_dir / f"{code}_benchmark.csv"
        _build_rows(
            data_rows=rows,
            output_csv=output_path,
            player_label=code,
            round_name=round_name,
        )

    return aggregated_csv
