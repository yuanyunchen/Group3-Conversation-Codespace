"""
Command-line interface for the flexible test framework.

This provides an easy way to run custom tests from the command line.
"""

import argparse
import json
import re

from ..sim.test_framework import (
	FlexibleTestRunner,
	ParameterRange,
	TestBuilder,
	TestConfiguration,
	create_altruism_comparison_test,
	create_mixed_opponents_test,
	create_parameter_sweep_test,
	create_random_players_test,
	create_scalability_test,
)


def _parse_player_config_string(config_str: str) -> dict:
	"""Parse a player configuration string into a dict.

	Accepts:
	- Strict JSON (e.g., '{"p10": 10, "pr": 2}')
	- JSON-ish without quoted keys (e.g., '{p10: 10, pr: 2}')
	- Key/value pairs (e.g., 'p10=10 pr=2' or 'p10:10,pr:2')
	"""
	s = config_str.strip()
	# 1) Try strict JSON
	try:
		return json.loads(s)
	except Exception:
		pass

	# 2) Try to repair JSON-ish with unquoted keys and single quotes
	try:
		repaired = s
		repaired = repaired.replace("'", '"')
		repaired = re.sub(r'([\{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', repaired)
		return json.loads(repaired)
	except Exception:
		pass

	# 3) Parse as key/value pairs
	pairs = re.split(r'[\s,]+', s)
	out: dict[str, int] = {}
	for token in pairs:
		if not token:
			continue
		if '=' in token:
			k, v = token.split('=', 1)
		elif ':' in token:
			k, v = token.split(':', 1)
		else:
			# Not a recognizable token, skip
			continue
		k = k.strip().strip('"\'')
		v = v.strip().strip('"\'')
		if not k or not v:
			continue
		try:
			out[k] = int(v)
		except ValueError:
			# Ignore non-int values
			continue
	return out


def create_custom_test_from_args(args) -> TestConfiguration:
	"""Create a custom test configuration from command line arguments."""
	builder = TestBuilder(args.name, args.description)

	# Set parameter ranges
	if args.altruism:
		builder.altruism_range(args.altruism)
	if args.tau:
		builder.tau_range(args.tau)
	if args.epsilon_fresh:
		builder.epsilon_fresh_range(args.epsilon_fresh)
	if args.epsilon_mono:
		builder.epsilon_mono_range(args.epsilon_mono)

	# Set player configurations
	if args.players:
		player_configs = []
		for player_str in args.players:
			parsed = _parse_player_config_string(player_str)
			if parsed:
				player_configs.append(parsed)
			else:
				print(f"Warning: Invalid player configuration '{player_str}', skipping")
		if player_configs:
			builder.player_configs(player_configs)

	# Set simulation parameters
	if args.simulations:
		builder.simulations(args.simulations)
	if args.conversation_length:
		builder.conversation_length(args.conversation_length)
	if args.subjects:
		builder.subjects(args.subjects)
	if args.memory_size:
		builder.memory_size(args.memory_size)

	# Parallel options
	if args.parallel:
		builder.parallel(True, args.workers)

	# Extended ranges
	if args.min_samples:
		builder.min_samples_range(args.min_samples)
	if args.ewma:
		builder.ewma_alpha_range(args.ewma)
	if args.w_importance:
		builder.importance_weight_range(args.w_importance)
	if args.w_coherence:
		builder.coherence_weight_range(args.w_coherence)
	if args.w_freshness:
		builder.freshness_weight_range(args.w_freshness)
	if args.w_monotony:
		builder.monotony_weight_range(args.w_monotony)

	# Set output directory
	if args.output_dir:
		builder.output_dir(args.output_dir)

	return builder.build()


def main():
	"""Main command-line interface."""
	parser = argparse.ArgumentParser(
		description='Flexible Monte Carlo test runner for Player10',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  # Run predefined altruism comparison test
  python -m players.player_10.flexible_runner --predefined altruism

  # Run custom test with specific parameters
  python -m players.player_10.flexible_runner --name "my_test" --altruism 0.0 0.5 1.0 --simulations 100

  # Test against different numbers of random players
  python -m players.player_10.flexible_runner --name "random_test" --players '{"p10": 10, "pr": 5}' --altruism 0.0 0.5 1.0

  # Run multiple player configurations
  python -m players.player_10.flexible_runner --name "multi_config" --players '{"p10": 10}' '{"p10": 10, "pr": 2}' '{"p10": 10, "pr": 5}'
		""",
	)

	# Test selection
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument(
		'--predefined',
		choices=[
			'altruism',
			'random2',
			'random5',
			'random10',
			'scalability',
			'parameter_sweep',
			'mixed',
		],
		help='Run a predefined test',
	)
	group.add_argument('--name', help='Name for custom test')

	# Test description
	parser.add_argument('--description', help='Description for custom test')

	# Parameter ranges
	parser.add_argument('--altruism', nargs='+', type=float, help='Altruism probabilities to test')
	parser.add_argument('--tau', nargs='+', type=float, help='Tau margins to test')
	parser.add_argument(
		'--epsilon-fresh', nargs='+', type=float, help='Epsilon fresh values to test'
	)
	parser.add_argument('--epsilon-mono', nargs='+', type=float, help='Epsilon mono values to test')
	parser.add_argument(
		'--min-samples', nargs='+', type=int, help='Min samples per player for trusted mean'
	)
	parser.add_argument('--ewma', nargs='+', type=float, help='EWMA alpha values to test')
	parser.add_argument('--w-importance', nargs='+', type=float, help='Importance weight values')
	parser.add_argument('--w-coherence', nargs='+', type=float, help='Coherence weight values')
	parser.add_argument('--w-freshness', nargs='+', type=float, help='Freshness weight values')
	parser.add_argument('--w-monotony', nargs='+', type=float, help='Monotony weight values')

	# Player configurations
	parser.add_argument('--players', nargs='+', help='Player configurations as JSON strings')

	# Simulation parameters
	parser.add_argument('--simulations', type=int, help='Number of simulations per configuration')
	parser.add_argument('--conversation-length', type=int, help='Conversation length')
	parser.add_argument('--subjects', type=int, help='Number of subjects')
	parser.add_argument('--memory-size', type=int, help='Memory size')
	parser.add_argument(
		'--parallel', action='store_true', help='Run simulations in parallel across CPU cores'
	)
	parser.add_argument(
		'--workers', type=int, help='Number of worker processes (defaults to CPU count)'
	)

	# Output settings
	parser.add_argument('--output-dir', help='Output directory for results')
	parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
	parser.add_argument('--quiet', action='store_true', help='Suppress progress output')

	args = parser.parse_args()

	# Create test configuration
	if args.predefined:
		# Use predefined test
		predefined_tests = {
			'altruism': create_altruism_comparison_test(),
			'random2': create_random_players_test(2),
			'random5': create_random_players_test(5),
			'random10': create_random_players_test(10),
			'scalability': create_scalability_test(),
			'parameter_sweep': create_parameter_sweep_test(),
			'mixed': create_mixed_opponents_test(),
		}
		config = predefined_tests[args.predefined]
	else:
		# Create custom test
		config = create_custom_test_from_args(args)

	# Override settings from command line (applies to both predefined and custom)
	# Parameter ranges
	if args.predefined:
		if args.altruism:
			config.altruism_probs = ParameterRange(
				values=args.altruism, name='altruism_prob', description='Altruism probability'
			)
		if args.tau:
			config.tau_margins = ParameterRange(
				values=args.tau, name='tau_margin', description='Tau margin'
			)
		if args.epsilon_fresh:
			config.epsilon_fresh_values = ParameterRange(
				values=args.epsilon_fresh, name='epsilon_fresh', description='Epsilon fresh'
			)
		if args.epsilon_mono:
			config.epsilon_mono_values = ParameterRange(
				values=args.epsilon_mono, name='epsilon_mono', description='Epsilon mono'
			)
		if args.min_samples:
			config.min_samples_values = ParameterRange(
				values=args.min_samples,
				name='min_samples_pid',
				description='Min samples per player for trusted mean',
			)
		if args.ewma:
			config.ewma_alpha_values = ParameterRange(
				values=args.ewma, name='ewma_alpha', description='EWMA alpha'
			)
		if args.w_importance:
			config.importance_weights = ParameterRange(
				values=args.w_importance, name='importance_weight', description='Importance weight'
			)
		if args.w_coherence:
			config.coherence_weights = ParameterRange(
				values=args.w_coherence, name='coherence_weight', description='Coherence weight'
			)
		if args.w_freshness:
			config.freshness_weights = ParameterRange(
				values=args.w_freshness, name='freshness_weight', description='Freshness weight'
			)
		if args.w_monotony:
			config.monotony_weights = ParameterRange(
				values=args.w_monotony, name='monotony_weight', description='Monotony weight'
			)
		# Player configurations
		if args.players:
			player_configs = []
			for player_str in args.players:
				parsed = _parse_player_config_string(player_str)
				if parsed:
					player_configs.append(parsed)
			if player_configs:
				config.player_configs = player_configs
		# Simulation parameters
		if args.simulations:
			config.num_simulations = args.simulations
		if args.conversation_length:
			config.conversation_length = args.conversation_length
		if args.subjects:
			config.subjects = args.subjects
		if args.memory_size:
			config.memory_size = args.memory_size
		# Parallel
		if args.parallel:
			config.parallel = True
			if args.workers:
				config.workers = args.workers
		# Output directory
		if args.output_dir:
			config.output_dir = args.output_dir

	# Generic flags
	if args.no_save:
		config.save_results = False
	if args.quiet:
		config.print_progress = False

	# Create and run test
	runner = FlexibleTestRunner(config.output_dir)
	results = runner.run_test(config)

	# Print summary
	print('\n=== TEST COMPLETED ===')
	print(f'Test: {config.name}')
	print(f'Total simulations: {len(results)}')
	print(f'Configurations tested: {len(results) // config.num_simulations}')

	# Analyze results if we have them
	if results:
		runner.simulator.results = results
		analysis = runner.simulator.analyze_results()

		# Print comprehensive results table
		print('\n=== COMPREHENSIVE RESULTS TABLE ===')
		print(
			f'{"Rank":<4} {"Altruism":<8} {"Tau":<6} {"Fresh":<6} {"Mono":<6} {"Total Score":<10} {"P10 Score":<9} {"Std Dev":<8} {"Count":<5}'
		)
		print('-' * 80)

		for i, config_result in enumerate(analysis['best_configurations'], 1):
			altruism, tau, fresh, mono = config_result['config']
			total_score = config_result['mean_score']

			# Get additional stats from config_summaries
			config_key = str(config_result['config'])
			if config_key in analysis['config_summaries']:
				summary = analysis['config_summaries'][config_key]
				p10_score = summary['player10_score']['mean']
				std = summary['total_score']['std']
				count = summary['total_score'].get('count', config.num_simulations)
			else:
				p10_score = 0.0
				std = 0.0
				count = config.num_simulations

			print(
				f'{i:<4} {altruism:<8.1f} {tau:<6.2f} {fresh:<6.2f} {mono:<6.2f} {total_score:<10.2f} {p10_score:<9.2f} {std:<8.2f} {count:<5}'
			)

		# Print detailed configuration table
		print('\n=== DETAILED CONFIGURATION TABLE ===')
		print(
			f'{"Rank":<4} {"Configuration":<25} {"Total Score":<12} {"P10 Score":<11} {"Conv Len":<9} {"Pauses":<7} {"Items":<6} {"Early Term":<10}'
		)
		print('-' * 100)

		for i, config_result in enumerate(analysis['best_configurations'], 1):
			altruism, tau, fresh, mono = config_result['config']
			config_key = str(config_result['config'])

			if config_key in analysis['config_summaries']:
				summary = analysis['config_summaries'][config_key]
				config_str = f'Alt={altruism:.1f},τ={tau:.2f},εf={fresh:.2f},εm={mono:.2f}'
				total_score = (
					f'{summary["total_score"]["mean"]:.2f}±{summary["total_score"]["std"]:.2f}'
				)
				p10_score = f'{summary["player10_score"]["mean"]:.2f}±{summary["player10_score"]["std"]:.2f}'
				conv_len = f'{summary["conversation_metrics"]["avg_length"]:.1f}'
				pauses = f'{summary["conversation_metrics"]["avg_pause_count"]:.1f}'
				items = f'{summary["conversation_metrics"]["avg_unique_items"]:.1f}'
				early_term = f'{summary["conversation_metrics"]["early_termination_rate"]:.2f}'
			else:
				config_str = f'Alt={altruism:.1f},τ={tau:.2f},εf={fresh:.2f},εm={mono:.2f}'
				total_score = f'{config_result["mean_score"]:.2f}±0.00'
				p10_score = '0.00±0.00'
				conv_len = '50.0'
				pauses = '0.0'
				items = '0.0'
				early_term = '0.00'

			print(
				f'{i:<4} {config_str:<25} {total_score:<12} {p10_score:<11} {conv_len:<9} {pauses:<7} {items:<6} {early_term:<10}'
			)

		# Print top 3 detailed analysis
		print('\n=== TOP 3 DETAILED ANALYSIS ===')
		for i, config_result in enumerate(analysis['best_configurations'][:3], 1):
			altruism, tau, fresh, mono = config_result['config']
			config_key = str(config_result['config'])

			if config_key in analysis['config_summaries']:
				summary = analysis['config_summaries'][config_key]
				print(
					f'\n{i}. Configuration: Altruism={altruism:.1f}, Tau={tau:.2f}, Fresh={fresh:.2f}, Mono={mono:.2f}'
				)
				print(
					f'   Total Score: {summary["total_score"]["mean"]:.2f} ± {summary["total_score"]["std"]:.2f}'
				)
				print(
					f'   Player10 Score: {summary["player10_score"]["mean"]:.2f} ± {summary["player10_score"]["std"]:.2f}'
				)
				print(
					f'   Avg Conversation Length: {summary["conversation_metrics"]["avg_length"]:.1f}'
				)
				print(
					f'   Early Termination Rate: {summary["conversation_metrics"]["early_termination_rate"]:.2f}'
				)
				print(
					f'   Avg Pause Count: {summary["conversation_metrics"]["avg_pause_count"]:.1f}'
				)
				print(
					f'   Avg Unique Items: {summary["conversation_metrics"]["avg_unique_items"]:.1f}'
				)

		# --- New: Full-parameterization aggregation and Top-10 table ---
		def _std(values: list[float]) -> float:
			if len(values) < 2:
				return 0.0
			m = sum(values) / len(values)
			var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
			return var**0.5

		# Group by full parameterization including players and extended knobs
		from collections import defaultdict

		groups: dict[tuple, dict] = {}
		by_key_scores: dict[tuple, list[float]] = defaultdict(list)
		by_key_p10: dict[tuple, list[float]] = defaultdict(list)

		def _players_key(players_dict: dict[str, int]) -> tuple:
			return tuple(sorted(players_dict.items()))

		def _key_from_cfg(cfg) -> tuple:
			return (
				round(cfg.altruism_prob, 6),
				round(cfg.tau_margin, 6),
				round(cfg.epsilon_fresh, 6),
				round(cfg.epsilon_mono, 6),
				int(cfg.min_samples_pid),
				round(cfg.ewma_alpha, 6),
				round(cfg.importance_weight, 6),
				round(cfg.coherence_weight, 6),
				round(cfg.freshness_weight, 6),
				round(cfg.monotony_weight, 6),
				_players_key(cfg.players),
				cfg.conversation_length,
				cfg.subjects,
				cfg.memory_size,
			)

		for r in results:
			k = _key_from_cfg(r.config)
			if k not in groups:
				groups[k] = {
					'altruism_prob': r.config.altruism_prob,
					'tau_margin': r.config.tau_margin,
					'epsilon_fresh': r.config.epsilon_fresh,
					'epsilon_mono': r.config.epsilon_mono,
					'min_samples_pid': r.config.min_samples_pid,
					'ewma_alpha': r.config.ewma_alpha,
					'importance_weight': r.config.importance_weight,
					'coherence_weight': r.config.coherence_weight,
					'freshness_weight': r.config.freshness_weight,
					'monotony_weight': r.config.monotony_weight,
					'players': r.config.players,
					'conversation_length': r.config.conversation_length,
					'subjects': r.config.subjects,
					'memory_size': r.config.memory_size,
				}
			by_key_scores[k].append(r.total_score)
			by_key_p10[k].append(r.player_scores.get('Player10', 0.0))

		# Build summary rows
		rows = []
		for k, meta in groups.items():
			scores = by_key_scores[k]
			p10_scores = by_key_p10[k]
			rows.append(
				{
					'key': k,
					'meta': meta,
					'mean': sum(scores) / len(scores),
					'std': _std(scores),
					'count': len(scores),
					'p10_mean': (sum(p10_scores) / len(p10_scores)) if p10_scores else 0.0,
					'p10_std': _std(p10_scores) if p10_scores else 0.0,
				}
			)

		rows.sort(key=lambda x: x['mean'], reverse=True)

		print('\n=== TOP 10 PARAMETERIZATIONS (FULL CONFIG) ===')
		header = (
			f'{"Rank":<4} {"Total (μ±σ)":<16} {"P10 (μ±σ)":<16} {"Count":<6} '
			f'{"Altruism":<8} {"Tau":<6} {"εfresh":<8} {"εmono":<7} {"MIN_S":<6} '
			f'{"EWMA":<6} {"Wimp":<6} {"Wcoh":<6} {"Wfre":<6} {"Wmon":<6} {"Players":<30}'
		)
		print(header)
		print('-' * len(header))

		for i, row in enumerate(rows[:10], start=1):
			m = row['meta']
			players_str = ','.join(f'{k}={v}' for k, v in sorted(m['players'].items()))
			print(
				f'{i:<4} '
				f'{row["mean"]:.2f}±{row["std"]:.2f} '
				f'{row["p10_mean"]:.2f}±{row["p10_std"]:.2f} '
				f'{row["count"]:<6} '
				f'{m["altruism_prob"]:<8.2f} {m["tau_margin"]:<6.2f} {m["epsilon_fresh"]:<8.2f} {m["epsilon_mono"]:<7.2f} '
				f'{m["min_samples_pid"]:<6} {m["ewma_alpha"]:<6.2f} {m["importance_weight"]:<6.2f} {m["coherence_weight"]:<6.2f} '
				f'{m["freshness_weight"]:<6.2f} {m["monotony_weight"]:<6.2f} {players_str:<30}'
			)

		# Overall stats across all runs
		all_scores = [r.total_score for r in results]
		overall_mean = sum(all_scores) / len(all_scores) if all_scores else 0.0
		overall_std = _std(all_scores) if all_scores else 0.0
		print(
			f'\nOverall Total Score: {overall_mean:.2f} ± {overall_std:.2f} across {len(all_scores)} runs'
		)


if __name__ == '__main__':
	main()
