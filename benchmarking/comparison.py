"""Utilities for running per-player benchmarks and aggregating comparisons."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .player_eval import SinglePlayerConfig, build_single_player_scenario
from .pipeline import BenchmarkPipeline, VariantAggregate
from .player_registry import DEFAULT_PLAYER_REGISTRY
from .utils import ensure_dir, slugify, write_csv


def clone_single_config(base: SinglePlayerConfig, target: str) -> SinglePlayerConfig:
    """Return a copy of ``base`` with a new target."""

    return SinglePlayerConfig(
        target=target,
        ratio_steps=base.ratio_steps,
        lengths=base.lengths,
        player_counts=base.player_counts,
        memory_sizes=base.memory_sizes,
        subject_counts=base.subject_counts,
        competitor_pool=base.competitor_pool,
        rounds=base.rounds,
        seed=base.seed,
        grid_lengths=base.grid_lengths,
        grid_memory_sizes=base.grid_memory_sizes,
        grid_ratio_steps=base.grid_ratio_steps,
        grid_player_counts=base.grid_player_counts,
    )


def summarize_target_metrics(
    aggregates: Iterable[VariantAggregate],
    *,
    target_type: str,
) -> Dict[tuple[str, str], dict]:
    """Extract per-variant metrics for the given target player type."""

    summary: Dict[tuple[str, str], dict] = {}
    for aggregate in aggregates:
        suite_id = aggregate.suite.split("::")[-1].strip()
        key = (suite_id, aggregate.variant)
        metadata = dict(aggregate.config.metadata)
        metadata.update({
            "length": aggregate.config.length,
            "memory_size": aggregate.config.memory_size,
            "subjects": aggregate.config.subjects,
        })
        for metric in aggregate.player_metrics:
            if metric["type"] != target_type:
                continue
            summary[key] = {
                "avg_score": metric["avg_score"],
                "avg_shared_score": metric["avg_shared_score"],
                "avg_individual": metric["avg_individual"],
                "avg_involvement_ratio": metric["avg_involvement_ratio"],
                "avg_contributed_shared": metric["avg_contributed_shared"],
                "avg_contributed_individual": metric["avg_contributed_individual"],
                "importance": metric["importance"],
                "coherence": metric["coherence"],
                "freshness": metric["freshness"],
                "nonmonotone": metric["nonmonotone"],
                "player_numbers": metric["player_numbers"],
                "rounds": aggregate.rounds_executed,
                "metadata": metadata,
                "suite_display": aggregate.suite,
            }
            break
    return summary


def merge_comparison_rows(
    per_target: Dict[str, Dict[tuple[str, str], dict]],
    *,
    targets: Sequence[str],
    aggregates_reference: Iterable[VariantAggregate],
) -> List[dict]:
    """Combine per-target summaries into a long-form comparison table."""

    rows: List[dict] = []
    for aggregate in aggregates_reference:
        suite_id = aggregate.suite.split("::")[-1].strip()
        key = (suite_id, aggregate.variant)
        for target in targets:
            summary = per_target.get(target, {}).get(key)
            if not summary:
                continue
            row = {
                "suite": suite_id,
                "variant": aggregate.variant,
                "target": target,
                "avg_score": f"{summary['avg_score']:.4f}",
                "avg_shared_score": f"{summary['avg_shared_score']:.4f}",
                "avg_individual": f"{summary['avg_individual']:.4f}",
                "avg_involvement_ratio": f"{summary['avg_involvement_ratio']:.4f}",
                "avg_contributed_shared": f"{summary['avg_contributed_shared']:.4f}",
                "avg_contributed_individual": f"{summary['avg_contributed_individual']:.4f}",
                "importance": f"{summary['importance']:.4f}",
                "coherence": f"{summary['coherence']:.4f}",
                "freshness": f"{summary['freshness']:.4f}",
                "nonmonotone": f"{summary['nonmonotone']:.4f}",
                "player_numbers": summary["player_numbers"],
                "rounds": summary["rounds"],
            }
            for meta_key, meta_value in sorted(summary["metadata"].items()):
                row[f"meta_{meta_key}"] = meta_value
            rows.append(row)
    return rows


def compute_target_overall(rows: Iterable[dict]) -> List[dict]:
    """Aggregate overall averages per target."""

    totals: Dict[str, dict] = {}
    counts: Dict[str, int] = {}
    for row in rows:
        target = row["target"]
        totals.setdefault(target, {
            "avg_score": 0.0,
            "avg_shared_score": 0.0,
            "avg_individual": 0.0,
        })
        counts[target] = counts.get(target, 0) + 1
        totals[target]["avg_score"] += float(row["avg_score"])
        totals[target]["avg_shared_score"] += float(row["avg_shared_score"])
        totals[target]["avg_individual"] += float(row["avg_individual"])

    results: List[dict] = []
    for target, sums in totals.items():
        n = max(1, counts[target])
        results.append({
            "target": target,
            "avg_score": f"{sums['avg_score'] / n:.4f}",
            "avg_shared_score": f"{sums['avg_shared_score'] / n:.4f}",
            "avg_individual": f"{sums['avg_individual'] / n:.4f}",
            "tests": n,
        })
    results.sort(key=lambda item: float(item["avg_score"]), reverse=True)
    return results


def write_comparison_markdown(
    output_dir: Path,
    *,
    rows: List[dict],
    overall: List[dict],
) -> None:
    """Render Markdown files summarising the comparison table."""

    ensure_dir(output_dir)
    md_lines: List[str] = []
    md_lines.append("# Player Comparison Summary")
    md_lines.append("")
    md_lines.append("## Overall Rankings")
    md_lines.append("| Target | Avg Score | Avg Shared | Avg Individual | Tests |")
    md_lines.append("| --- | --- | --- | --- | --- |")
    for item in overall:
        md_lines.append(
            f"| {item['target']} | {item['avg_score']} | {item['avg_shared_score']} | "
            f"{item['avg_individual']} | {item['tests']} |"
        )
    md_lines.append("")
    md_lines.append("## Detailed Cases")
    md_lines.append(
        "| Suite | Variant | Target | Avg Score | Shared | Individual | Involvement | Metadata |"
    )
    md_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        metadata = ", ".join(
            f"{key[5:]}={value}" for key, value in row.items() if key.startswith("meta_")
        ) or "-"
        md_lines.append(
            f"| {row['suite']} | {row['variant']} | {row['target']} | {row['avg_score']} | "
            f"{row['avg_shared_score']} | {row['avg_individual']} | {row['avg_involvement_ratio']} | {metadata} |"
        )
    (output_dir / "comparison_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
