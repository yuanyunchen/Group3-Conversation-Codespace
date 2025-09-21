"""Command-line interface for the benchmarking pipelines."""

from __future__ import annotations

import argparse
from pathlib import Path

from .comparison import (
	clone_single_config,
	compute_target_overall,
	merge_comparison_rows,
	summarize_target_metrics,
	write_comparison_markdown,
)
from .pipeline import BenchmarkPipeline
from .player_eval import (
	build_multi_player_scenario,
	build_single_player_scenario,
	default_multi_config,
	default_single_config,
)
from .player_registry import DEFAULT_PLAYER_REGISTRY
from .sample_scenarios import SCENARIO_BUILDERS
from .utils import ensure_dir, slugify, write_csv


def parse_arguments() -> argparse.Namespace:
	"""Build and parse CLI arguments."""

	parser = argparse.ArgumentParser(
		description='Benchmarking pipeline for the conversation simulator',
	)
	parser.add_argument(
		'--scenario',
		default='default',
		help='Scenario key to run (use --list to display options)',
	)
	parser.add_argument(
		'--output-root',
		default=None,
		help='Directory where benchmark results should be written',
	)
	parser.add_argument(
		'--detailed',
		action='store_true',
		help='Force detailed outputs (overrides scenario defaults)',
	)
	parser.add_argument(
		'--list',
		action='store_true',
		help='List available scenarios and exit',
	)
	parser.add_argument(
		'--pipeline',
		choices=['single', 'multi', 'compare'],
		default=None,
		help='Select predefined player-evaluation pipelines',
	)
	parser.add_argument(
		'--mode',
		choices=['simple', 'complex'],
		default='simple',
		help='Pipeline mode controlling number of test cases',
	)
	parser.add_argument(
		'--targets',
		nargs='+',
		default=None,
		help='Player codes to evaluate (pipeline mode)',
	)
	parser.add_argument(
		'--lengths',
		nargs='+',
		type=int,
		default=None,
		help='Conversation lengths to sweep (override defaults)',
	)
	parser.add_argument(
		'--player-counts',
		nargs='+',
		type=int,
		default=None,
		help='Total player counts to sweep (override defaults)',
	)
	parser.add_argument(
		'--memory-sizes',
		nargs='+',
		type=int,
		default=None,
		help='Memory sizes to sweep (override defaults)',
	)
	parser.add_argument(
		'--subject-counts',
		nargs='+',
		type=int,
		default=None,
		help='Subject counts to use (override defaults)',
	)
	parser.add_argument(
		'--ratio-steps',
		nargs='+',
		type=float,
		default=None,
		help='Target ratio sweep values (override defaults)',
	)
	parser.add_argument(
		'--competitors',
		nargs='+',
		default=None,
		help='Competitor player codes for comparison suites (override defaults)',
	)
	parser.add_argument(
		'--rounds-per-variant',
		type=int,
		default=None,
		help='Number of rounds per variant (override defaults)',
	)
	parser.add_argument(
		'--base-seed',
		type=int,
		default=None,
		help='Base random seed for generated variants',
	)
	parser.add_argument(
		'--clean-output',
		action='store_true',
		help='Remove previous runs inside the chosen output root before executing',
	)
	return parser.parse_args()


def list_scenarios() -> None:
	"""Print available static scenarios and pipeline presets."""

	print('Available scenarios:')
	for key in sorted(SCENARIO_BUILDERS):
		print(f'  - {key}')
	print('Pipeline presets:')
	print('  --pipeline single|multi --mode simple|complex')


def main() -> None:
	"""Entry point for running benchmarks via the CLI."""

	args = parse_arguments()
	if args.list:
		list_scenarios()
		return

	pipeline_type = args.pipeline
	scenario_key = args.scenario

	if pipeline_type:
		if not args.targets:
			raise SystemExit('--targets must be provided when using pipeline mode')

		mode = args.mode
		if pipeline_type == 'single':
			if len(args.targets) != 1:
				raise SystemExit('Single pipeline requires exactly one target player code')
			config = default_single_config(args.targets[0], mode)
			if args.ratio_steps:
				config.ratio_steps = tuple(args.ratio_steps)
			if args.lengths:
				config.lengths = tuple(args.lengths)
			if args.player_counts:
				config.player_counts = tuple(args.player_counts)
			if args.memory_sizes:
				config.memory_sizes = tuple(args.memory_sizes)
			if args.subject_counts:
				config.subject_counts = tuple(args.subject_counts)
			if args.competitors:
				config.competitor_pool = tuple(args.competitors)
			if args.rounds_per_variant:
				config.rounds = args.rounds_per_variant
			if args.base_seed:
				config.seed = args.base_seed
			scenario = build_single_player_scenario(config)
		elif pipeline_type == 'multi':
			if len(args.targets) < 2:
				raise SystemExit('Multi pipeline requires at least two target player codes')
			config = default_multi_config(tuple(args.targets), mode)
			if args.lengths:
				config.shared_lengths = tuple(args.lengths)
			if args.player_counts:
				config.shared_player_counts = tuple(args.player_counts)
			if args.memory_sizes:
				config.shared_memory_sizes = tuple(args.memory_sizes)
			if args.subject_counts:
				config.subject_counts = tuple(args.subject_counts)
			if args.ratio_steps:
				config.ratio_steps = tuple(args.ratio_steps)
			if args.competitors:
				config.competitor_pool = tuple(args.competitors)
			if args.rounds_per_variant:
				config.rounds = args.rounds_per_variant
			if args.base_seed:
				config.seed = args.base_seed
			scenario = build_multi_player_scenario(config)
		else:  # compare
			if len(args.targets) < 2:
				raise SystemExit('Compare pipeline requires at least two target player codes')
			base_config = default_single_config(args.targets[0], mode)
			if args.ratio_steps:
				base_config.ratio_steps = tuple(args.ratio_steps)
			if args.lengths:
				base_config.lengths = tuple(args.lengths)
			if args.player_counts:
				base_config.player_counts = tuple(args.player_counts)
			if args.memory_sizes:
				base_config.memory_sizes = tuple(args.memory_sizes)
			if args.subject_counts:
				base_config.subject_counts = tuple(args.subject_counts)
			if args.competitors:
				base_config.competitor_pool = tuple(args.competitors)
			if args.rounds_per_variant:
				base_config.rounds = args.rounds_per_variant
			if args.base_seed:
				base_config.seed = args.base_seed

			output_root = Path(args.output_root or 'benchmarking/results/latest_run')
			if args.clean_output and output_root.exists():
				import shutil

				shutil.rmtree(output_root)
			ensure_dir(output_root)

			comparison_rows = []
			per_target = {}
			reference_aggregates = None

			for target in args.targets:
				config = clone_single_config(base_config, target)
				scenario = build_single_player_scenario(config)
				target_output = output_root / slugify(target)
				pipeline = BenchmarkPipeline(
					scenario,
					output_root=target_output,
					detailed=args.detailed,
					clean_output=False,
				)
				aggregates = pipeline.run()
				reference_aggregates = reference_aggregates or aggregates
				target_type = DEFAULT_PLAYER_REGISTRY.get(target).__name__
				per_target[target] = summarize_target_metrics(
					aggregates,
					target_type=target_type,
				)

			rows = merge_comparison_rows(
				per_target,
				targets=tuple(args.targets),
				aggregates_reference=reference_aggregates or [],
			)
			comparison_dir = output_root / 'comparison_summary'
			ensure_dir(comparison_dir)
			if rows:
				base_fields = [
					'suite',
					'variant',
					'target',
					'avg_score',
					'avg_shared_score',
					'avg_individual',
					'avg_involvement_ratio',
					'avg_contributed_shared',
					'avg_contributed_individual',
					'importance',
					'coherence',
					'freshness',
					'nonmonotone',
					'player_numbers',
					'rounds',
				]
				extra_fields = sorted(
					{key for row in rows for key in row.keys() if key not in base_fields}
				)
				fieldnames = base_fields + extra_fields
				write_csv(comparison_dir / 'comparison_summary.csv', fieldnames, rows)

			overall = compute_target_overall(rows)
			write_comparison_markdown(comparison_dir, rows=rows, overall=overall)

			if comparison_dir.exists():
				print(f'Comparison summary written to {comparison_dir}')
			return
	else:
		if scenario_key == 'player_eval':
			raise SystemExit(
				'Use --pipeline single|multi with --targets to run the evaluation pipelines.'
			)
		if scenario_key not in SCENARIO_BUILDERS:
			list_scenarios()
			raise SystemExit(f"Unknown scenario '{scenario_key}'")
		scenario = SCENARIO_BUILDERS[scenario_key]()
	pipeline = BenchmarkPipeline(
		scenario,
		output_root=args.output_root,
		detailed=args.detailed,
		clean_output=args.clean_output,
	)
	pipeline.run()
	if pipeline.last_run_dir:
		print(f'Benchmark run completed. Results stored at {pipeline.last_run_dir}')


if __name__ == '__main__':
	main()
