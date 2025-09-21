"""Scenario definitions for benchmarking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlayerSpec:
	"""Describes how many instances of a player type to include in a run."""

	code: str
	count: int
	label: str | None = None

	def as_dict(self) -> dict:
		return {'code': self.code, 'count': self.count, 'label': self.label}


@dataclass(slots=True)
class SimulationVariant:
	"""Single experiment configuration within a suite."""

	label: str
	players: list[PlayerSpec]
	length: int
	memory_size: int
	subjects: int
	rounds: int = 1
	seed: int = 42
	description: str = ''
	metadata: dict[str, str | int | float] = field(default_factory=dict)
	detailed_outputs: bool = False

	def to_engine_kwargs(self) -> dict:
		return {
			'conversation_length': self.length,
			'memory_size': self.memory_size,
			'subjects': self.subjects,
		}

	def tags(self) -> list[str]:
		tags: list[str] = []
		for key, value in self.metadata.items():
			tags.append(f'{key}={value}')
		return tags


@dataclass(slots=True)
class BenchmarkSuite:
	"""A group of related variants exploring a scenario axis."""

	name: str
	description: str
	variants: list[SimulationVariant]
	focus_player: str | None = None
	axis_key: str | None = None
	axis_label: str | None = None

	def variant_labels(self) -> list[str]:
		return [variant.label for variant in self.variants]


@dataclass(slots=True)
class BenchmarkScenario:
	"""Top-level scenario aggregating suites for benchmarking."""

	name: str
	description: str
	suites: list[BenchmarkSuite]
	default_output_root: str = 'benchmarking/results'

	def all_variants(self) -> list[SimulationVariant]:
		runs: list[SimulationVariant] = []
		for suite in self.suites:
			runs.extend(suite.variants)
		return runs
