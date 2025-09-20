"""Benchmarking pipeline implementation."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from core.engine import Engine
from core.utils import ConversationAnalyzer, CustomEncoder
from models.player import Player

from .player_registry import PlayerRegistry, DEFAULT_PLAYER_REGISTRY
from .scenario import BenchmarkScenario, BenchmarkSuite, PlayerSpec, SimulationVariant
from .utils import ensure_dir, slugify, timestamp, write_csv, write_json
from .visualization import (
    create_suite_focus_chart,
    create_variant_player_comparison_chart,
)
from .reporting import write_run_overview, write_suite_index


@dataclass(slots=True)
class VariantAggregate:
    """Summary of a variant after executing its rounds."""

    scenario: str
    suite: str
    variant: str
    description: str
    config: SimulationVariant
    average_conversation_length: float
    average_pauses: float
    player_metrics: List[dict]
    rounds_executed: int

    def to_csv_rows(self) -> Iterable[dict]:
        """Flatten the per-player metrics for the global summary CSV."""

        for metric in self.player_metrics:
            row = {
                "scenario": self.scenario,
                "suite": self.suite,
                "variant": self.variant,
                "variant_description": self.description,
                "player_type": metric["type"],
                "avg_score": f"{metric['avg_score']:.4f}",
                "avg_shared_score": f"{metric['avg_shared_score']:.4f}",
                "avg_individual_score": f"{metric['avg_individual']:.4f}",
                "avg_involvement_ratio": f"{metric['avg_involvement_ratio']:.4f}",
                "avg_contributed_shared": f"{metric['avg_contributed_shared']:.4f}",
                "avg_contributed_individual": f"{metric['avg_contributed_individual']:.4f}",
                "importance_per_turn": f"{metric['importance']:.4f}",
                "coherence_per_turn": f"{metric['coherence']:.4f}",
                "freshness_per_turn": f"{metric['freshness']:.4f}",
                "nonmonotone_per_turn": f"{metric['nonmonotone']:.4f}",
                "player_instances": metric["player_numbers"],
                "rounds": self.config.rounds,
                "seed_start": self.config.seed,
                "length": self.config.length,
                "memory_size": self.config.memory_size,
                "subjects": self.config.subjects,
                "average_actual_length": f"{self.average_conversation_length:.4f}",
                "average_pauses": f"{self.average_pauses:.4f}",
            }
            for key, value in sorted(self.config.metadata.items()):
                row[f"meta_{key}"] = value
            yield row


class BenchmarkPipeline:
    """Run a scenario and collect CSV/report/chart artefacts."""

    def __init__(
        self,
        scenario: BenchmarkScenario,
        *,
        output_root: Optional[str | Path] = None,
        registry: Optional[PlayerRegistry] = None,
        detailed: bool = False,
        clean_output: bool = False,
    ) -> None:
        self.scenario = scenario
        self.registry = registry or DEFAULT_PLAYER_REGISTRY
        self.detailed = detailed
        root_path = Path(output_root or scenario.default_output_root)
        self.run_root = ensure_dir(root_path)
        self.analyzer = ConversationAnalyzer()
        self.last_run_dir: Optional[Path] = None
        self.clean_output = clean_output

    def run(self) -> List[VariantAggregate]:
        if self.clean_output:
            self._clean_previous_runs()

        run_id = f"{timestamp()}_{slugify(self.scenario.name)}"
        scenario_dir = ensure_dir(self.run_root / run_id)
        write_json(
            scenario_dir / "scenario_config.json",
            self._scenario_to_dict(self.scenario),
        )
        self.last_run_dir = scenario_dir

        aggregates: List[VariantAggregate] = []
        suite_dirs: Dict[str, Path] = {}
        variant_dirs: Dict[tuple[str, str], Path] = {}

        for suite in self.scenario.suites:
            suite_dir = ensure_dir(scenario_dir / slugify(suite.name))
            suite_dirs[suite.name] = suite_dir
            suite_specific_aggregates: List[VariantAggregate] = []
            for variant in suite.variants:
                variant_dir = ensure_dir(suite_dir / slugify(variant.label))
                variant_dirs[(suite.name, variant.label)] = variant_dir
                variant_aggregate = self._run_variant(
                    suite=suite,
                    variant=variant,
                    output_dir=variant_dir,
                )
                aggregates.append(variant_aggregate)
                suite_specific_aggregates.append(variant_aggregate)

                # Charts per variant: compare player types and annotate configuration
                create_variant_player_comparison_chart(
                    variant_aggregate,
                    output_dir=variant_dir,
                )

            # Charts per suite: show how each player evolves across the sweep
            create_suite_focus_chart(
                suite,
                suite_specific_aggregates,
                output_dir=suite_dir,
                registry=self.registry,
            )

            write_suite_index(
                suite,
                suite_specific_aggregates,
                suite_dir,
                variant_dirs,
            )

        summary_csv = scenario_dir / "summary.csv"
        csv_rows = [row for agg in aggregates for row in agg.to_csv_rows()]
        if csv_rows:
            base_fields = [
                "scenario",
                "suite",
                "variant",
                "variant_description",
                "player_type",
                "avg_score",
                "avg_shared_score",
                "avg_individual_score",
                "avg_involvement_ratio",
                "avg_contributed_shared",
                "avg_contributed_individual",
                "importance_per_turn",
                "coherence_per_turn",
                "freshness_per_turn",
                "nonmonotone_per_turn",
                "player_instances",
                "rounds",
                "seed_start",
                "length",
                "memory_size",
                "subjects",
                "average_actual_length",
                "average_pauses",
            ]
            extra_fields = sorted({
                key
                for row in csv_rows
                for key in row.keys()
                if key not in base_fields
            })
            fieldnames = base_fields + extra_fields
            write_csv(summary_csv, fieldnames, csv_rows)

        report_path = scenario_dir / "summary_report.txt"
        report_content = self._build_report(aggregates)
        report_path.write_text(report_content, encoding="utf-8")

        overview_path = scenario_dir / "README.md"
        overview_path.write_text(
            write_run_overview(
                scenario=self.scenario,
                aggregates=aggregates,
                scenario_dir=scenario_dir,
                suite_dirs=suite_dirs,
                variant_dirs=variant_dirs,
            ),
            encoding="utf-8",
        )

        self._update_latest_symlink(scenario_dir)

        return aggregates

    def _run_variant(
        self,
        *,
        suite: BenchmarkSuite,
        variant: SimulationVariant,
        output_dir: Path,
    ) -> VariantAggregate:
        player_classes = self._expand_player_specs(variant.players)
        player_count = len(player_classes)
        metric_accumulator: Dict[str, dict] = {}
        lengths: List[int] = []
        pauses: List[int] = []

        detailed_outputs = self.detailed or variant.detailed_outputs
        for round_index in range(variant.rounds):
            seed = variant.seed + round_index
            engine = Engine(
                players=player_classes,
                player_count=player_count,
                subjects=variant.subjects,
                memory_size=variant.memory_size,
                conversation_length=variant.length,
                seed=seed,
            )
            simulation_results = engine.run(player_classes)

            lengths.append(simulation_results["scores"].get("conversation_length", 0))
            pauses.append(simulation_results["scores"].get("pauses", 0))

            # Aggregate per-player-type statistics for later averaging
            per_type_rows = self.analyzer.compute_type_averages(simulation_results, engine)
            for row in per_type_rows:
                entry = metric_accumulator.setdefault(
                    row["type"],
                    {
                        "sum_score": 0.0,
                        "sum_shared": 0.0,
                        "sum_individual": 0.0,
                        "sum_involvement": 0.0,
                        "sum_contrib_shared": 0.0,
                        "sum_contrib_individual": 0.0,
                        "sum_importance": 0.0,
                        "sum_coherence": 0.0,
                        "sum_freshness": 0.0,
                        "sum_nonmonotone": 0.0,
                        "player_numbers": row.get("player_numbers", 0),
                        "appearances": 0,
                    },
                )
                entry["sum_score"] += float(row["score"])
                entry["sum_shared"] += float(row["shared_score"])
                entry["sum_individual"] += float(row["individual"])
                entry["sum_involvement"] += float(row["involvement_ratio"])
                entry["sum_contrib_shared"] += float(row["contributed_shared_score"])
                entry["sum_contrib_individual"] += float(row["contributed_individual_score"])
                entry["sum_importance"] += float(row["importance"])
                entry["sum_coherence"] += float(row["coherence"])
                entry["sum_freshness"] += float(row["freshness"])
                entry["sum_nonmonotone"] += float(row["nonmonotone"])
                entry["appearances"] += 1

            if detailed_outputs:
                self._write_round_outputs(
                    engine=engine,
                    simulation_results=simulation_results,
                    base_dir=output_dir / f"round_{round_index + 1:02d}",
                )

        aggregated_metrics: List[dict] = []
        for player_type, totals in metric_accumulator.items():
            appearances = max(1, totals.pop("appearances", 1))
            aggregated_metrics.append(
                {
                    "type": player_type,
                    "avg_score": round(totals["sum_score"] / appearances, 4),
                    "avg_shared_score": round(totals["sum_shared"] / appearances, 4),
                    "avg_individual": round(totals["sum_individual"] / appearances, 4),
                    "avg_involvement_ratio": round(totals["sum_involvement"] / appearances, 4),
                    "avg_contributed_shared": round(totals["sum_contrib_shared"] / appearances, 4),
                    "avg_contributed_individual": round(totals["sum_contrib_individual"] / appearances, 4),
                    "importance": round(totals["sum_importance"] / appearances, 4),
                    "coherence": round(totals["sum_coherence"] / appearances, 4),
                    "freshness": round(totals["sum_freshness"] / appearances, 4),
                    "nonmonotone": round(totals["sum_nonmonotone"] / appearances, 4),
                    "player_numbers": totals["player_numbers"],
                }
            )
        aggregated_metrics.sort(key=lambda item: item["avg_score"], reverse=True)

        variant_summary_path = output_dir / "variant_summary.csv"
        if aggregated_metrics:
            fieldnames = [
                "player_type",
                "avg_score",
                "avg_shared_score",
                "avg_individual",
                "avg_involvement_ratio",
                "avg_contributed_shared",
                "avg_contributed_individual",
                "importance",
                "coherence",
                "freshness",
                "nonmonotone",
                "player_numbers",
            ]
            rows = [
                {
                    "player_type": metric["type"],
                    "avg_score": f"{metric['avg_score']:.4f}",
                    "avg_shared_score": f"{metric['avg_shared_score']:.4f}",
                    "avg_individual": f"{metric['avg_individual']:.4f}",
                    "avg_involvement_ratio": f"{metric['avg_involvement_ratio']:.4f}",
                    "avg_contributed_shared": f"{metric['avg_contributed_shared']:.4f}",
                    "avg_contributed_individual": f"{metric['avg_contributed_individual']:.4f}",
                    "importance": f"{metric['importance']:.4f}",
                    "coherence": f"{metric['coherence']:.4f}",
                    "freshness": f"{metric['freshness']:.4f}",
                    "nonmonotone": f"{metric['nonmonotone']:.4f}",
                    "player_numbers": metric["player_numbers"],
                }
                for metric in aggregated_metrics
            ]
            write_csv(variant_summary_path, fieldnames, rows)

        config_copy = asdict(variant)
        write_json(output_dir / "config.json", config_copy)

        average_length = round(sum(lengths) / len(lengths), 4) if lengths else 0.0
        average_pauses = round(sum(pauses) / len(pauses), 4) if pauses else 0.0

        return VariantAggregate(
            scenario=self.scenario.name,
            suite=suite.name,
            variant=variant.label,
            description=variant.description,
            config=variant,
            average_conversation_length=average_length,
            average_pauses=average_pauses,
            player_metrics=aggregated_metrics,
            rounds_executed=variant.rounds,
        )

    def _expand_player_specs(self, specs: List[PlayerSpec]) -> List[type[Player]]:
        """Expand player specifications into the classes expected by the engine."""

        players: List[type[Player]] = []
        for spec in specs:
            player_cls = self.registry.get(spec.code)
            players.extend([player_cls] * spec.count)
        return players

    def _write_round_outputs(self, *, engine: Engine, simulation_results: dict, base_dir: Path) -> None:
        """Persist per-round artefacts (JSON, text, and CSV)."""

        ensure_dir(base_dir)
        json_path = base_dir / "simulation_results.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(simulation_results, handle, cls=CustomEncoder, indent=2)

        report_text = self.analyzer.raw_data_to_human_readable(simulation_results, engine)
        (base_dir / "analysis.txt").write_text(report_text, encoding="utf-8")

        csv_path = base_dir / "player_metrics.csv"
        self.analyzer.raw_data_to_csv(
            simulation_results,
            engine=engine,
            csv_path=str(csv_path),
        )

    def _scenario_to_dict(self, scenario: BenchmarkScenario) -> dict:
        """Convert a scenario to a serialisable dictionary."""

        return {
            "name": scenario.name,
            "description": scenario.description,
            "suites": [
                {
                    "name": suite.name,
                    "description": suite.description,
                    "focus_player": suite.focus_player,
                    "variants": [
                        {
                            "label": variant.label,
                            "description": variant.description,
                            "length": variant.length,
                            "memory_size": variant.memory_size,
                            "subjects": variant.subjects,
                            "rounds": variant.rounds,
                            "seed": variant.seed,
                            "metadata": variant.metadata,
                            "players": [spec.as_dict() for spec in variant.players],
                        }
                        for variant in suite.variants
                    ],
                }
                for suite in scenario.suites
            ],
        }

    def _build_report(self, aggregates: List[VariantAggregate]) -> str:
        """Compose the human-readable summary report."""

        if not aggregates:
            return "No benchmark data available."

        lines: List[str] = []
        lines.append(f"SCENARIO: {self.scenario.name}")
        lines.append(self.scenario.description)
        lines.append("")
        lines.append(f"Total suites: {len(self.scenario.suites)}")
        total_variants = len(aggregates)
        total_rounds = sum(agg.rounds_executed for agg in aggregates)
        lines.append(f"Total variants: {total_variants}")
        lines.append(f"Total rounds executed: {total_rounds}")
        lines.append("=" * 70)
        lines.append("")

        aggregates_by_suite: Dict[str, List[VariantAggregate]] = {}
        for aggregate in aggregates:
            aggregates_by_suite.setdefault(aggregate.suite, []).append(aggregate)

        for suite in self.scenario.suites:
            suite_aggregates = aggregates_by_suite.get(suite.name, [])
            lines.append(f"Suite: {suite.name}")
            lines.append(suite.description)
            lines.append(f"Variants: {len(suite_aggregates)}")
            lines.append("-" * 70)
            for aggregate in suite_aggregates:
                lines.append(f"  Variant: {aggregate.variant}")
                if aggregate.description:
                    lines.append(f"    {aggregate.description}")
                lines.append(
                    f"    Avg length: {aggregate.average_conversation_length:.4f} | Avg pauses: {aggregate.average_pauses:.4f}"
                )
                for metric in aggregate.player_metrics:
                    lines.append(
                        "    "
                        + f"{metric['type']}: score={metric['avg_score']:.4f}, "
                        + f"shared={metric['avg_shared_score']:.4f}, individual={metric['avg_individual']:.4f}, involvement={metric['avg_involvement_ratio']:.4f}"
                    )
                if aggregate.config.metadata:
                    meta_parts = [f"{k}={v}" for k, v in aggregate.config.metadata.items()]
                    lines.append("    Metadata: " + ", ".join(meta_parts))
                lines.append("")
            lines.append("".rstrip())
        return "\n".join(lines)

    def _clean_previous_runs(self) -> None:
        """Remove previous run directories within the output root."""

        for item in list(self.run_root.iterdir()):
            if item.name.startswith("."):
                continue
            if item.is_symlink() or item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def _update_latest_symlink(self, scenario_dir: Path) -> None:
        """Create/refresh a symlink pointing at the most recent run."""

        latest_link = self.run_root / f"latest_{slugify(self.scenario.name)}"
        if latest_link.exists() or latest_link.is_symlink():
            if latest_link.is_dir() and not latest_link.is_symlink():
                shutil.rmtree(latest_link)
            else:
                latest_link.unlink()
        latest_link.symlink_to(scenario_dir, target_is_directory=True)

        marker = self.run_root / "LATEST.txt"
        marker.write_text(str(scenario_dir.resolve()), encoding="utf-8")
