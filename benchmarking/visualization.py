"""Visualization helpers for benchmarking results."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .player_registry import PlayerRegistry
from .scenario import BenchmarkSuite
from .utils import ensure_dir, slugify

try:  # pragma: no cover - optional dependency
	import matplotlib.pyplot as plt

	HAS_MPL = True
except Exception:  # pragma: no cover - optional dependency
	plt = None
	HAS_MPL = False


def _warn_missing_backend():  # pragma: no cover - logging would be overkill here
	print('[benchmarking] matplotlib not available; skipping chart generation')


def create_variant_player_comparison_chart(variant_aggregate, output_dir: Path) -> None:
	"""Render a column chart comparing player types inside a single variant."""

	if not HAS_MPL or not variant_aggregate.player_metrics:
		if not HAS_MPL:
			_warn_missing_backend()
		return

	ensure_dir(output_dir)
	player_types = [metric['type'] for metric in variant_aggregate.player_metrics]
	scores = [metric['avg_score'] for metric in variant_aggregate.player_metrics]

	figure_width = min(max(6, len(player_types) * 0.9), 18)
	figure, axis = plt.subplots(figsize=(figure_width, 4.5))
	figure.suptitle(
		f'{variant_aggregate.scenario} → {variant_aggregate.suite}\n'
		f'Variant: {variant_aggregate.variant}',
		fontsize=11,
	)
	bars = axis.bar(player_types, scores, color='#4C72B0')
	axis.set_title(f'Player Comparison — {variant_aggregate.variant}')
	axis.set_ylabel('Average Score')
	axis.set_ylim(bottom=0)
	axis.tick_params(axis='x', rotation=30)
	for label in axis.get_xticklabels():
		label.set_horizontalalignment('right')

	metadata_lines = [
		f'length={variant_aggregate.config.length}',
		f'memory={variant_aggregate.config.memory_size}',
		f'subjects={variant_aggregate.config.subjects}',
		f'rounds={variant_aggregate.config.rounds}',
		f'seed={variant_aggregate.config.seed}',
	]
	for key, value in sorted(variant_aggregate.config.metadata.items()):
		metadata_lines.append(f'{key}={value}')

	for bar, score in zip(bars, scores, strict=False):
		axis.annotate(
			f'{score:.4f}',
			xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
			xytext=(0, 3),
			textcoords='offset points',
			ha='center',
			va='bottom',
			fontsize=8,
		)

	axis.grid(axis='y', linestyle='--', alpha=0.3)
	figure.text(
		0.99,
		0.02,
		'\n'.join(metadata_lines),
		ha='right',
		va='bottom',
		fontsize=8,
		family='monospace',
	)
	figure.tight_layout()
	figure.savefig(output_dir / 'player_comparison.png', dpi=200)
	plt.close(figure)


def create_suite_focus_chart(
	suite: BenchmarkSuite,
	aggregates: Iterable,
	*,
	output_dir: Path,
	registry: PlayerRegistry | None = None,
) -> None:
	"""Render a suite-level chart.

	When ``suite.axis_key`` refers to numeric metadata, the chart plots one line
	per player type (up to six) across that axis. Otherwise a grouped bar chart
	compares every player type per variant. This makes it easier to see how each
	model reacts to changing parameters rather than just tracking a single
	"focus" player.
	"""

	aggregates = list(aggregates)
	if not HAS_MPL or not aggregates:
		if not HAS_MPL:
			_warn_missing_backend()
		return

	ensure_dir(output_dir)

	focus_type_name: str | None = None
	if suite.focus_player and registry:
		try:
			focus_type_name = registry.get(suite.focus_player).__name__
		except KeyError:
			focus_type_name = None

	# Collect per-player metrics keyed by axis value.
	point_count = len(aggregates)
	if point_count == 0:
		return
	if point_count > 80:
		print(
			f"[benchmarking] skipping suite chart for '{suite.name}' (too many variants: {point_count})"
		)
		return

	axis_key = suite.axis_key
	type_series: dict[str, list[tuple]] = {}
	numeric_axis = True

	for idx, aggregate in enumerate(sorted(aggregates, key=lambda a: a.variant)):
		axis_value = idx
		if axis_key:
			meta_value = aggregate.config.metadata.get(axis_key)
			if isinstance(meta_value, (int, float)):
				axis_value = meta_value
			else:
				numeric_axis = False
				axis_value = aggregate.variant

		for metric in aggregate.player_metrics:
			type_series.setdefault(metric['type'], []).append(
				(axis_value, metric['avg_score'], aggregate.variant)
			)

	# Limit clutter to the focus player plus up to five best averages.
	averages = {
		ptype: sum(score for _, score, _ in points) / len(points)
		for ptype, points in type_series.items()
		if points
	}
	ordered_types = sorted(averages.items(), key=lambda item: item[1], reverse=True)
	selected_types: list[str] = []
	if focus_type_name and focus_type_name in type_series:
		selected_types.append(focus_type_name)
	for tname, _ in ordered_types:
		if tname not in selected_types:
			selected_types.append(tname)
		if len(selected_types) >= 6:
			break

	title_suffix = f' ({focus_type_name})' if focus_type_name else ''
	figure_width = min(max(6, len(type_series) * 1.2, point_count * 0.8), 24)
	figure, axis = plt.subplots(figsize=(figure_width, 4.5))
	scenario_name = aggregates[0].scenario if aggregates else ''
	title_lines = [scenario_name, suite.name]
	if suite.description:
		title_lines.append(suite.description)
	figure.suptitle('\n'.join(filter(None, title_lines)), fontsize=11)

	if numeric_axis and isinstance(list(type_series.values())[0][0][0], (int, float)):
		for tname in selected_types:
			series_points = sorted(type_series.get(tname, []), key=lambda item: item[0])
			if not series_points:
				continue
			x_values = [point[0] for point in series_points]
			y_values = [point[1] for point in series_points]
			labels = [point[2] for point in series_points]
			axis.plot(x_values, y_values, marker='o', linewidth=2, label=tname)
			for x_val, y_val, label_text in zip(x_values, y_values, labels, strict=False):
				axis.annotate(
					f'{y_val:.4f}\n{label_text}',
					xy=(x_val, y_val),
					xytext=(0, 6),
					textcoords='offset points',
					ha='center',
					va='bottom',
					fontsize=8,
				)

		axis.set_xlabel(suite.axis_label or axis_key or 'Variants')
		axis.set_ylabel('Average Score')
		axis.set_title(f'Suite Trend — {suite.name}{title_suffix}')
		axis.grid(axis='y', linestyle='--', alpha=0.35)
		axis.legend(loc='best', fontsize=8)
	else:
		categories = [aggregate.variant for aggregate in aggregates]
		bar_positions = range(len(categories))
		bar_width = max(0.8 / max(len(selected_types), 1), 0.15)

		for idx, tname in enumerate(selected_types):
			series_points = type_series.get(tname, [])
			scores = []
			for category in categories:
				match = next(
					(score for x_val, score, label in series_points if label == category), 0.0
				)
				scores.append(match)
			offsets = [
				pos + (idx - (len(selected_types) - 1) / 2) * bar_width for pos in bar_positions
			]
			axis.bar(offsets, scores, width=bar_width, label=tname)
			for x_pos, score in zip(offsets, scores, strict=False):
				axis.annotate(
					f'{score:.4f}',
					xy=(x_pos, score),
					xytext=(0, 3),
					textcoords='offset points',
					ha='center',
					va='bottom',
					fontsize=7,
				)

		axis.set_xticks(list(bar_positions))
		axis.set_xticklabels(categories, rotation=20, ha='right')
		axis.set_ylabel('Average Score')
		axis.set_title(f'Suite Comparison — {suite.name}{title_suffix}')
		axis.legend(loc='best', fontsize=8)

	figure.tight_layout()
	filename = f'suite_focus_{slugify(suite.name)}.png'
	figure.savefig(output_dir / filename, dpi=200)
	plt.close(figure)
