"""Scenario definitions for benchmarking pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class PlayerSpec:
    """Describes how many instances of a player type to include in a run."""

    code: str
    count: int
    label: Optional[str] = None

    def as_dict(self) -> dict:
        return {"code": self.code, "count": self.count, "label": self.label}


@dataclass(slots=True)
class SimulationVariant:
    """Single experiment configuration within a suite."""

    label: str
    players: List[PlayerSpec]
    length: int
    memory_size: int
    subjects: int
    rounds: int = 1
    seed: int = 42
    description: str = ""
    metadata: Dict[str, str | int | float] = field(default_factory=dict)
    detailed_outputs: bool = False

    def to_engine_kwargs(self) -> dict:
        return {
            "conversation_length": self.length,
            "memory_size": self.memory_size,
            "subjects": self.subjects,
        }

    def tags(self) -> List[str]:
        tags: List[str] = []
        for key, value in self.metadata.items():
            tags.append(f"{key}={value}")
        return tags


@dataclass(slots=True)
class BenchmarkSuite:
    """A group of related variants exploring a scenario axis."""

    name: str
    description: str
    variants: List[SimulationVariant]
    focus_player: Optional[str] = None
    axis_key: Optional[str] = None
    axis_label: Optional[str] = None

    def variant_labels(self) -> List[str]:
        return [variant.label for variant in self.variants]


@dataclass(slots=True)
class BenchmarkScenario:
    """Top-level scenario aggregating suites for benchmarking."""

    name: str
    description: str
    suites: List[BenchmarkSuite]
    default_output_root: str = "benchmarking/results"

    def all_variants(self) -> List[SimulationVariant]:
        runs: List[SimulationVariant] = []
        for suite in self.suites:
            runs.extend(suite.variants)
        return runs
