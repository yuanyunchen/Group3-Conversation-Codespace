"""Player evaluation scenario builders supporting single- and multi-model pipelines.

This module exposes two configurable pipelines:

* ``build_single_player_scenario`` – runs a battery of tests for a single target
  player, sweeping over opponent ratios, conversation length, player counts,
  memory sizes, competitor rosters, and (optionally) a full hyper-parameter grid.
* ``build_multi_player_scenario`` – evaluates several target players under shared
  environments so their performance can be compared fairly on identical cases.

Both pipelines provide a *simple* mode (≤5 variants per sweep, quick insight) and
an expansive *complex* mode (≥100 variants via grid sweeps for statistical
significance). The dataclass configurations keep the structures easy to adjust.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import product

from .player_registry import DEFAULT_PLAYER_REGISTRY
from .scenario import BenchmarkScenario, BenchmarkSuite, PlayerSpec, SimulationVariant

# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SinglePlayerConfig:
	"""Configuration for the single-player pipeline.

	Attributes are ordered roughly by the suite they influence. ``ratio_steps``,
	``lengths``, ``player_counts`` and ``memory_sizes`` each control the sweep
	size for the corresponding suite. Grid attributes are optional and only used
	in complex mode.
	"""

	target: str
	ratio_steps: Sequence[float]
	lengths: Sequence[int]
	player_counts: Sequence[int]
	memory_sizes: Sequence[int]
	subject_counts: Sequence[int]
	competitor_pool: Sequence[str]
	rounds: int
	seed: int
	grid_lengths: Sequence[int] = ()
	grid_memory_sizes: Sequence[int] = ()
	grid_ratio_steps: Sequence[float] = ()
	grid_player_counts: Sequence[int] = ()


@dataclass(slots=True)
class MultiPlayerConfig:
	"""Configuration for the multi-player comparison pipeline."""

	targets: Sequence[str]
	shared_lengths: Sequence[int]
	shared_player_counts: Sequence[int]
	shared_memory_sizes: Sequence[int]
	subject_counts: Sequence[int]
	ratio_steps: Sequence[float]
	competitor_pool: Sequence[str]
	rounds: int
	seed: int
	grid_lengths: Sequence[int] = ()
	grid_memory_sizes: Sequence[int] = ()
	grid_ratio_steps: Sequence[float] = ()


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_SINGLE_SIMPLE = {
	# ≥5 points per sweep so line charts remain meaningful.
	'ratio_steps': (0.2, 0.35, 0.5, 0.65, 0.8),
	'lengths': (18, 26, 34, 42, 50),
	'player_counts': (4, 6, 8, 10, 12),
	'memory_sizes': (10, 14, 18, 22, 26),
	'subject_counts': (20,),
	'competitor_pool': ('pr', 'p_balanced_greedy', 'p_bst_medium'),
	'rounds': 3,
	'seed': 200,
	'grid_lengths': (),
	'grid_memory_sizes': (),
	'grid_ratio_steps': (),
	'grid_player_counts': (),
}

_SINGLE_COMPLEX = {
	'ratio_steps': (0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95),
	'lengths': (18, 26, 34, 42, 50, 58),
	'player_counts': (4, 6, 8, 10, 12, 14),
	'memory_sizes': (8, 12, 16, 20, 24, 28),
	'subject_counts': (16, 20, 24),
	'competitor_pool': (
		'pr',
		'p_balanced_greedy',
		'p_selfish_greedy',
		'p_selfless_greedy',
		'p_bst_low',
		'p_bst_medium',
		'p_bst_high',
	),
	'rounds': 5,
	'seed': 500,
	'grid_lengths': (24, 36, 48, 60),
	'grid_memory_sizes': (10, 18, 26, 34),
	'grid_ratio_steps': (0.2, 0.4, 0.6, 0.8),
	'grid_player_counts': (6, 8, 10, 12),
}

_MULTI_SIMPLE = {
	'shared_lengths': (20, 28, 36, 44, 52),
	'shared_player_counts': (6, 8, 10, 12, 14),
	'shared_memory_sizes': (12, 16, 20, 24, 28),
	'subject_counts': (20,),
	'ratio_steps': (0.25, 0.4, 0.55, 0.7, 0.85),
	'competitor_pool': ('pr', 'p_balanced_greedy', 'p_bst_medium'),
	'rounds': 3,
	'seed': 300,
	'grid_lengths': (),
	'grid_memory_sizes': (),
	'grid_ratio_steps': (),
}

_MULTI_COMPLEX = {
	'shared_lengths': (18, 26, 34, 42, 50, 58),
	'shared_player_counts': (6, 8, 10, 12, 14),
	'shared_memory_sizes': (10, 14, 18, 22, 26),
	'subject_counts': (16, 20, 24),
	'ratio_steps': (0.2, 0.35, 0.5, 0.65, 0.8, 0.9),
	'competitor_pool': (
		'pr',
		'p_balanced_greedy',
		'p_selfish_greedy',
		'p_selfless_greedy',
		'p_bst_low',
		'p_bst_medium',
		'p_bst_high',
	),
	'rounds': 5,
	'seed': 750,
	'grid_lengths': (24, 32, 40, 48, 56),
	'grid_memory_sizes': (12, 18, 24, 30, 36),
	'grid_ratio_steps': (0.2, 0.35, 0.5, 0.65),
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _seed_sequence(start: int) -> Iterator[int]:
	"""Yield an infinite deterministic seed sequence starting from ``start``."""

	current = start
	while True:
		yield current
		current += 1


def _calc_target_random_counts(total_players: int, ratio: float) -> tuple[int, int]:
	"""Return (target_count, random_count) for single-player sweeps."""

	ratio = max(0.0, min(1.0, ratio))
	target_count = max(1, round(total_players * ratio))
	if target_count >= total_players:
		target_count = total_players - 1
	random_count = max(total_players - target_count, 1)
	return target_count, random_count


def _allocate_multi_counts(
	total_players: int, ratio: float, target_count: int
) -> tuple[list[int], int]:
	"""Allocate counts for each target plus remaining random players."""

	ratio = max(0.0, min(1.0, ratio))
	desired_target = max(target_count, round(total_players * ratio))
	if desired_target >= total_players:
		desired_target = total_players - 1
	random_count = max(total_players - desired_target, 1)
	per_target = max(1, desired_target // target_count)
	allocation = [per_target for _ in range(target_count)]
	assigned = per_target * target_count
	idx = 0
	while assigned < desired_target:
		allocation[idx] += 1
		assigned += 1
		idx = (idx + 1) % target_count
	return allocation, random_count


def _validate_player_codes(codes: Sequence[str]) -> None:
	"""Ensure all player codes exist in the registry."""

	missing = [code for code in codes if code not in DEFAULT_PLAYER_REGISTRY]
	if missing:
		raise ValueError(f'Unknown player codes: {", ".join(missing)}')


# ---------------------------------------------------------------------------
# Default config builders
# ---------------------------------------------------------------------------


def default_single_config(target: str, mode: str = 'simple') -> SinglePlayerConfig:
	"""Return preset configuration for a single-player pipeline."""

	_validate_player_codes([target])
	presets = _SINGLE_SIMPLE if mode == 'simple' else _SINGLE_COMPLEX
	return SinglePlayerConfig(target=target, **presets)


def default_multi_config(targets: Sequence[str], mode: str = 'simple') -> MultiPlayerConfig:
	"""Return preset configuration for a multi-player pipeline."""

	if len(targets) < 2:
		raise ValueError('Multi-player pipeline requires at least two target codes')
	_validate_player_codes(targets)
	presets = _MULTI_SIMPLE if mode == 'simple' else _MULTI_COMPLEX
	return MultiPlayerConfig(targets=tuple(targets), **presets)


# ---------------------------------------------------------------------------
# Single player pipeline suites
# ---------------------------------------------------------------------------


def _single_ratio_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep the ratio of target vs random opponents for a single player."""

	variants: list[SimulationVariant] = []
	total_players = config.player_counts[0]
	base_length = config.lengths[len(config.lengths) // 2]
	base_memory = config.memory_sizes[0]
	base_subjects = config.subject_counts[0]

	for ratio in config.ratio_steps:
		target_count, random_count = _calc_target_random_counts(total_players, ratio)
		variants.append(
			SimulationVariant(
				label=f'Ratio_{int(ratio * 100)}',
				description=f'Target ratio {ratio:.2f} vs random opponents.',
				players=[
					PlayerSpec(code=config.target, count=target_count),
					PlayerSpec(code='pr', count=random_count, label='Random'),
				],
				length=base_length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'target_ratio': round(ratio, 4),
					'player_count': total_players,
					'opponent': 'pr',
				},
				detailed_outputs=ratio in {config.ratio_steps[0], config.ratio_steps[-1]},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Ratio Sweep',
		description='Performance against random opponents as the target ratio changes.',
		variants=variants,
		focus_player=config.target,
		axis_key='target_ratio',
		axis_label='Target player ratio',
	)


def _single_length_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep conversation length for the target player vs random opponents."""

	total_players = config.player_counts[0]
	base_memory = config.memory_sizes[0]
	base_subjects = config.subject_counts[0]
	ratio = config.ratio_steps[len(config.ratio_steps) // 2]
	target_count, random_count = _calc_target_random_counts(total_players, ratio)

	variants = []
	for length in config.lengths:
		variants.append(
			SimulationVariant(
				label=f'Length_{length}',
				description='Conversation length sweep against random opponents.',
				players=[
					PlayerSpec(code=config.target, count=target_count),
					PlayerSpec(code='pr', count=random_count, label='Random'),
				],
				length=length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'length': length,
					'player_count': total_players,
					'target_ratio': round(ratio, 4),
				},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Length Sweep',
		description='Impact of conversation length while facing random opponents.',
		variants=variants,
		focus_player=config.target,
		axis_key='length',
		axis_label='Conversation length',
	)


def _single_player_count_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep total player count for the target player vs random opponents."""

	base_length = config.lengths[len(config.lengths) // 2]
	base_memory = config.memory_sizes[0]
	base_subjects = config.subject_counts[0]
	ratio = config.ratio_steps[len(config.ratio_steps) // 2]

	variants = []
	for total in config.player_counts:
		target_count, random_count = _calc_target_random_counts(total, ratio)
		variants.append(
			SimulationVariant(
				label=f'Players_{total}',
				description='Total player count sweep vs random opponents.',
				players=[
					PlayerSpec(code=config.target, count=target_count),
					PlayerSpec(code='pr', count=random_count, label='Random'),
				],
				length=base_length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'player_count': total,
					'target_ratio': round(ratio, 4),
				},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Player Count Sweep',
		description='Impact of changing total participant count.',
		variants=variants,
		focus_player=config.target,
		axis_key='player_count',
		axis_label='Total players',
	)


def _single_memory_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep memory bank size for the target player vs random opponents."""

	total_players = config.player_counts[0]
	ratio = config.ratio_steps[len(config.ratio_steps) // 2]
	target_count, random_count = _calc_target_random_counts(total_players, ratio)
	base_length = config.lengths[len(config.lengths) // 2]
	base_subjects = config.subject_counts[0]

	variants = []
	for memory in config.memory_sizes:
		variants.append(
			SimulationVariant(
				label=f'Memory_{memory}',
				description='Player memory size sweep vs random opponents.',
				players=[
					PlayerSpec(code=config.target, count=target_count),
					PlayerSpec(code='pr', count=random_count, label='Random'),
				],
				length=base_length,
				memory_size=memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'memory_size': memory,
					'player_count': total_players,
					'target_ratio': round(ratio, 4),
				},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Memory Sweep',
		description='Impact of memory size while facing random opponents.',
		variants=variants,
		focus_player=config.target,
		axis_key='memory_size',
		axis_label='Memory size',
	)


def _single_competitor_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Head-to-head matchups versus a curated competitor pool."""

	base_length = config.lengths[len(config.lengths) // 2]
	base_memory = config.memory_sizes[len(config.memory_sizes) // 2]
	base_subjects = config.subject_counts[0]

	variants = []
	for competitor_code in config.competitor_pool:
		if competitor_code == config.target:
			continue
		variants.append(
			SimulationVariant(
				label=f'Vs_{competitor_code}',
				description=f'Head-to-head vs {competitor_code} players.',
				players=[
					PlayerSpec(code=config.target, count=3),
					PlayerSpec(code=competitor_code, count=3),
				],
				length=base_length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'competitor': competitor_code,
					'players_per_side': 3,
				},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Competitor Mix',
		description='Target player against specific competitor rosters.',
		variants=variants,
		focus_player=config.target,
	)


def _single_grid_suite(config: SinglePlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite | None:
	"""Optional grid sweep covering length, memory, ratio, and player count."""

	if not (
		config.grid_lengths
		and config.grid_memory_sizes
		and config.grid_ratio_steps
		and config.grid_player_counts
	):
		return None

	variants: list[SimulationVariant] = []
	for length, memory, ratio, total in product(
		config.grid_lengths,
		config.grid_memory_sizes,
		config.grid_ratio_steps,
		config.grid_player_counts,
	):
		target_count, random_count = _calc_target_random_counts(total, ratio)
		variants.append(
			SimulationVariant(
				label=f'Grid_L{length}_M{memory}_R{int(ratio * 100)}_P{total}',
				description='Hyperparameter grid sweep (length, memory, ratio, players).',
				players=[
					PlayerSpec(code=config.target, count=target_count),
					PlayerSpec(code='pr', count=random_count, label='Random'),
				],
				length=length,
				memory_size=memory,
				subjects=config.subject_counts[len(config.subject_counts) // 2],
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'length': length,
					'memory_size': memory,
					'target_ratio': round(ratio, 4),
					'player_count': total,
					'grid': True,
				},
			)
		)

	return BenchmarkSuite(
		name=f'{config.target} :: Hyperparameter Grid',
		description='Combinatorial sweep for statistical robustness.',
		variants=variants,
		focus_player=config.target,
	)


def build_single_player_scenario(config: SinglePlayerConfig) -> BenchmarkScenario:
	"""Build the single-player benchmark scenario from a configuration."""

	_validate_player_codes([config.target])
	seeds = _seed_sequence(config.seed)

	suites: list[BenchmarkSuite] = [
		_single_ratio_suite(config, seeds),
		_single_length_suite(config, seeds),
		_single_player_count_suite(config, seeds),
		_single_memory_suite(config, seeds),
		_single_competitor_suite(config, seeds),
	]

	grid_suite = _single_grid_suite(config, seeds)
	if grid_suite is not None:
		suites.append(grid_suite)

	scenario_name = f'Single Player Pipeline :: {config.target}'
	description = (
		'Automated benchmark evaluating a single player across opponent ratios, conversation '
		'lengths, roster sizes, memory capacity, and competitor matchups. Includes optional '
		'grid sweeps for statistical coverage.'
	)

	return BenchmarkScenario(
		name=scenario_name,
		description=description,
		suites=suites,
		default_output_root='benchmarking/results',
	)


# ---------------------------------------------------------------------------
# Multi-player pipeline suites
# ---------------------------------------------------------------------------


def _multi_ratio_suite(config: MultiPlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep ratios when multiple targets share the same environment."""

	base_length = config.shared_lengths[len(config.shared_lengths) // 2]
	base_memory = config.shared_memory_sizes[0]
	base_subjects = config.subject_counts[0]
	total_players = config.shared_player_counts[0]
	target_count = len(config.targets)

	variants = []
	for ratio in config.ratio_steps:
		allocations, random_count = _allocate_multi_counts(total_players, ratio, target_count)
		players: list[PlayerSpec] = [
			PlayerSpec(code=code, count=count)
			for code, count in zip(config.targets, allocations, strict=True)
		]
		players.append(PlayerSpec(code='pr', count=random_count, label='Random'))
		variants.append(
			SimulationVariant(
				label=f'Ratio_{int(ratio * 100)}',
				description='Shared environment ratio sweep against random players.',
				players=players,
				length=base_length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'target_ratio': round(ratio, 4),
					'player_count': total_players,
					'opponent': 'pr',
				},
				detailed_outputs=ratio in {config.ratio_steps[0], config.ratio_steps[-1]},
			)
		)

	return BenchmarkSuite(
		name='Shared Ratio Sweep',
		description='All targets evaluated together as target/random ratios vary.',
		variants=variants,
		focus_player=config.targets[0],
		axis_key='target_ratio',
		axis_label='Target player ratio',
	)


def _multi_length_suite(config: MultiPlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep conversation length for all targets simultaneously."""

	total_players = config.shared_player_counts[-1]
	ratio = config.ratio_steps[len(config.ratio_steps) // 2]
	allocations, random_count = _allocate_multi_counts(total_players, ratio, len(config.targets))

	variants = []
	for length in config.shared_lengths:
		players = [
			PlayerSpec(code=code, count=count)
			for code, count in zip(config.targets, allocations, strict=True)
		]
		players.append(PlayerSpec(code='pr', count=random_count, label='Random'))
		variants.append(
			SimulationVariant(
				label=f'Length_{length}',
				description='Conversation length sweep shared by all targets.',
				players=players,
				length=length,
				memory_size=config.shared_memory_sizes[0],
				subjects=config.subject_counts[0],
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'length': length,
					'player_count': total_players,
					'target_ratio': round(ratio, 4),
				},
			)
		)

	return BenchmarkSuite(
		name='Shared Length Sweep',
		description='Impact of conversation length when all targets face identical conditions.',
		variants=variants,
		focus_player=config.targets[0],
		axis_key='length',
		axis_label='Conversation length',
	)


def _multi_memory_suite(config: MultiPlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Sweep memory capacity with identical rosters for each target."""

	total_players = config.shared_player_counts[-1]
	ratio = config.ratio_steps[len(config.ratio_steps) // 2]
	allocations, random_count = _allocate_multi_counts(total_players, ratio, len(config.targets))

	variants = []
	for memory in config.shared_memory_sizes:
		players = [
			PlayerSpec(code=code, count=count)
			for code, count in zip(config.targets, allocations, strict=True)
		]
		players.append(PlayerSpec(code='pr', count=random_count, label='Random'))
		variants.append(
			SimulationVariant(
				label=f'Memory_{memory}',
				description='Memory capacity sweep shared by all targets.',
				players=players,
				length=config.shared_lengths[len(config.shared_lengths) // 2],
				memory_size=memory,
				subjects=config.subject_counts[0],
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'memory_size': memory,
					'player_count': total_players,
					'target_ratio': round(ratio, 4),
				},
			)
		)

	return BenchmarkSuite(
		name='Shared Memory Sweep',
		description='Impact of memory size with identical rosters for all targets.',
		variants=variants,
		focus_player=config.targets[0],
		axis_key='memory_size',
		axis_label='Memory size',
	)


def _multi_competitor_suite(config: MultiPlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite:
	"""Shared competitor experiments for all targets."""

	base_length = config.shared_lengths[len(config.shared_lengths) // 2]
	base_memory = config.shared_memory_sizes[len(config.shared_memory_sizes) // 2]
	base_subjects = config.subject_counts[0]

	variants = []
	for competitor_code in config.competitor_pool:
		if competitor_code in config.targets:
			continue
		players = [PlayerSpec(code=code, count=2) for code in config.targets]
		players.append(PlayerSpec(code=competitor_code, count=2))
		players.append(PlayerSpec(code='pr', count=2, label='Random'))
		variants.append(
			SimulationVariant(
				label=f'Vs_{competitor_code}',
				description='Shared competitor comparison for all targets.',
				players=players,
				length=base_length,
				memory_size=base_memory,
				subjects=base_subjects,
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'competitor': competitor_code,
					'players_per_target': 2,
				},
			)
		)

	return BenchmarkSuite(
		name='Shared Competitor Mix',
		description='All targets tested together against specific competitor lineups.',
		variants=variants,
		focus_player=config.targets[0],
	)


def _multi_grid_suite(config: MultiPlayerConfig, seeds: Iterator[int]) -> BenchmarkSuite | None:
	"""Optional grid sweep for multi-player comparisons."""

	if not (config.grid_lengths and config.grid_memory_sizes and config.grid_ratio_steps):
		return None

	target_count = len(config.targets)
	variants: list[SimulationVariant] = []
	for length, memory, ratio in product(
		config.grid_lengths,
		config.grid_memory_sizes,
		config.grid_ratio_steps,
	):
		total_players = config.shared_player_counts[-1]
		allocations, random_count = _allocate_multi_counts(total_players, ratio, target_count)
		players = [
			PlayerSpec(code=code, count=count)
			for code, count in zip(config.targets, allocations, strict=True)
		]
		players.append(PlayerSpec(code='pr', count=random_count, label='Random'))
		variants.append(
			SimulationVariant(
				label=f'Grid_L{length}_M{memory}_R{int(ratio * 100)}',
				description='Combinatorial sweep for shared environments.',
				players=players,
				length=length,
				memory_size=memory,
				subjects=config.subject_counts[len(config.subject_counts) // 2],
				rounds=config.rounds,
				seed=next(seeds),
				metadata={
					'length': length,
					'memory_size': memory,
					'target_ratio': round(ratio, 4),
					'player_count': total_players,
					'grid': True,
				},
			)
		)

	return BenchmarkSuite(
		name='Shared Hyperparameter Grid',
		description='Combinatorial sweep allowing direct score comparisons across targets.',
		variants=variants,
		focus_player=config.targets[0],
	)


def build_multi_player_scenario(config: MultiPlayerConfig) -> BenchmarkScenario:
	"""Build the multi-player comparison scenario from a configuration."""

	_validate_player_codes(config.targets)
	seeds = _seed_sequence(config.seed)

	suites: list[BenchmarkSuite] = [
		_multi_ratio_suite(config, seeds),
		_multi_length_suite(config, seeds),
		_multi_memory_suite(config, seeds),
		_multi_competitor_suite(config, seeds),
	]

	grid_suite = _multi_grid_suite(config, seeds)
	if grid_suite is not None:
		suites.append(grid_suite)

	scenario_name = 'Multi Player Comparison Pipeline'
	description = (
		'Unified benchmarking pipeline where all target players undergo identical tests across '
		'ratio sweeps, conversation lengths, memory capacities, competitor rosters, and optional '
		'grid sweeps for statistical robustness.'
	)

	return BenchmarkScenario(
		name=scenario_name,
		description=description,
		suites=suites,
		default_output_root='benchmarking/results',
	)
