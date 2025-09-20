"""Markdown reporting utilities for benchmark runs."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .scenario import BenchmarkScenario, BenchmarkSuite
from .utils import slugify


def _relative_path(base: Path, target: Path) -> str:
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        return target.as_posix()


def _format_metadata(metadata: dict) -> str:
    if not metadata:
        return "-"
    parts = [f"{k}={v}" for k, v in sorted(metadata.items())]
    return ", ".join(parts)


def write_run_overview(
    *,
    scenario: BenchmarkScenario,
    aggregates: List,
    scenario_dir: Path,
    suite_dirs: Dict[str, Path],
    variant_dirs: Dict[Tuple[str, str], Path],
) -> str:
    """Return Markdown overview for the entire run."""

    lines: List[str] = []
    lines.append(f"# {scenario.name}")
    lines.append("")
    lines.append(scenario.description)
    lines.append("")
    lines.append(f"- Total suites: {len(scenario.suites)}")
    lines.append(f"- Total variants: {len(aggregates)}")
    total_rounds = sum(getattr(agg, "rounds_executed", 0) for agg in aggregates)
    lines.append(f"- Total rounds executed: {total_rounds}")
    lines.append("")

    lines.append("## Contents")
    for suite in scenario.suites:
        rel_suite_path = _relative_path(scenario_dir, suite_dirs[suite.name])
        lines.append(f"- [{suite.name}]({rel_suite_path}/suite_index.md)")
    lines.append("")

    aggregate_lookup = {(agg.suite, agg.variant): agg for agg in aggregates}

    lines.append("## Summary Table")
    lines.append("| Suite | Variant | Player | Avg Score | Shared | Individual | Rounds |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for aggregate in aggregates:
        for metric in aggregate.player_metrics:
            lines.append(
                "| "
                + f"{aggregate.suite} | {aggregate.variant} | {metric['type']} | "
                + f"{metric['avg_score']:.4f} | {metric['avg_shared_score']:.4f} | "
                + f"{metric['avg_individual']:.4f} | {aggregate.rounds_executed} |"
            )
    lines.append("")

    for suite in scenario.suites:
        lines.append(f"## {suite.name}")
        if suite.description:
            lines.append(suite.description)
        if suite.axis_key:
            label = suite.axis_label or suite.axis_key
            lines.append(f"- Sweep axis: `{suite.axis_key}` ({label})")
        lines.append("")
        lines.append("| Variant | Axis Value | Players | Variant CSV | Player Chart | Metadata |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for variant in suite.variants:
            aggregate = aggregate_lookup.get((suite.name, variant.label))
            if not aggregate:
                continue
            axis_value = "-"
            if suite.axis_key:
                axis_value = str(variant.metadata.get(suite.axis_key, "-"))
            player_names = ", ".join(metric["type"] for metric in aggregate.player_metrics)
            variant_dir = variant_dirs[(suite.name, variant.label)]
            csv_path = _relative_path(scenario_dir, variant_dir / "variant_summary.csv")
            chart_path = _relative_path(scenario_dir, variant_dir / "player_comparison.png")
            metadata_text = _format_metadata(variant.metadata)
            lines.append(
                f"| {variant.label} | {axis_value} | {player_names} | "
                f"[{variant.label}]({csv_path}) | [Chart]({chart_path}) | {metadata_text} |"
            )
        lines.append("")

    return "\n".join(lines)


def write_suite_index(
    suite: BenchmarkSuite,
    aggregates: Iterable,
    suite_dir: Path,
    variant_dirs: Dict[Tuple[str, str], Path],
) -> None:
    """Write a per-suite Markdown index summarising variants and outputs."""

    aggregates_list = list(aggregates)
    lines: List[str] = []
    lines.append(f"# {suite.name}")
    if suite.description:
        lines.append("")
        lines.append(suite.description)
        lines.append("")

    focus_text = suite.focus_player or "(none)"
    lines.append(f"- Focus player: {focus_text}")
    if suite.axis_key:
        label = suite.axis_label or suite.axis_key
        lines.append(f"- Sweep axis: `{suite.axis_key}` ({label})")
    lines.append(f"- Variants: {len(aggregates_list)}")
    lines.append("")

    chart_path = suite_dir / f"suite_focus_{slugify(suite.name)}.png"
    if chart_path.exists():
        rel_chart = _relative_path(suite_dir, chart_path)
        lines.append(f"![Suite chart]({rel_chart})")
        lines.append("")

    lines.append("| Variant | Players | Metadata | Variant CSV | Player Chart |")
    lines.append("| --- | --- | --- | --- | --- |")
    for aggregate in aggregates_list:
        variant_dir = variant_dirs[(aggregate.suite, aggregate.variant)]
        players = ", ".join(metric["type"] for metric in aggregate.player_metrics)
        metadata_text = _format_metadata(aggregate.config.metadata)
        csv_path = _relative_path(suite_dir, variant_dir / "variant_summary.csv")
        chart_path = _relative_path(suite_dir, variant_dir / "player_comparison.png")
        lines.append(
            f"| {aggregate.variant} | {players} | {metadata_text} | "
            f"[{aggregate.variant}]({csv_path}) | [Chart]({chart_path}) |"
        )

    (suite_dir / "suite_index.md").write_text("\n".join(lines), encoding="utf-8")
