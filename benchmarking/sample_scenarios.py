"""Predefined benchmarking scenarios for quick usage."""
from __future__ import annotations

from .scenario import BenchmarkScenario, BenchmarkSuite, PlayerSpec, SimulationVariant


def build_default_scenario() -> BenchmarkScenario:
    """Return a scenario covering baseline, stress, and edge cases."""

    baseline_suite = BenchmarkSuite(
        name="Baseline Mix",
        description="Baseline comparisons between greedy and random style players.",
        focus_player="p_balanced_greedy",
        variants=[
            SimulationVariant(
                label="Mixed_Default",
                description="Balanced greedy vs random players in a short conversation.",
                players=[
                    PlayerSpec(code="p_balanced_greedy", count=2),
                    PlayerSpec(code="pr", count=2),
                    PlayerSpec(code="pp", count=2),
                ],
                length=18,
                memory_size=10,
                subjects=20,
                rounds=3,
                seed=91,
                metadata={"category": "baseline", "conversation": "short"},
                detailed_outputs=True,
            ),
            SimulationVariant(
                label="Balanced_vs_BST",
                description="Balanced greedy players competing with BST medium players.",
                players=[
                    PlayerSpec(code="p_balanced_greedy", count=3),
                    PlayerSpec(code="p_bst_medium", count=3),
                ],
                length=25,
                memory_size=12,
                subjects=24,
                rounds=3,
                seed=123,
                metadata={"category": "baseline", "conversation": "medium"},
            ),
        ],
    )

    self_play_suite = BenchmarkSuite(
        name="Self Play",
        description="Self-play experiments for BST variants.",
        focus_player="p_bst_medium",
        variants=[
            SimulationVariant(
                label="BST_Medium_SelfPlay",
                description="Four BST medium players facing each other.",
                players=[PlayerSpec(code="p_bst_medium", count=4)],
                length=30,
                memory_size=14,
                subjects=20,
                rounds=2,
                seed=321,
                metadata={"mode": "self_play", "variant": "medium"},
            ),
            SimulationVariant(
                label="BST_High_SelfPlay",
                description="Higher effort BST players with longer conversations.",
                players=[PlayerSpec(code="p_bst_high", count=4)],
                length=40,
                memory_size=18,
                subjects=22,
                rounds=2,
                seed=654,
                metadata={"mode": "self_play", "variant": "high"},
            ),
        ],
    )

    stress_suite = BenchmarkSuite(
        name="Stress Tests",
        description="Stress conversations with long lengths and large memory banks.",
        focus_player="p_bst_dynamic_depth",
        variants=[
            SimulationVariant(
                label="Long_Run_Competition",
                description="Long conversation with mixed strategies and dynamic BST player.",
                players=[
                    PlayerSpec(code="p_bst_dynamic_depth", count=2),
                    PlayerSpec(code="p_selfish_greedy", count=2),
                    PlayerSpec(code="pr", count=2),
                ],
                length=60,
                memory_size=25,
                subjects=28,
                rounds=2,
                seed=777,
                metadata={"category": "stress", "length": 60},
            ),
            SimulationVariant(
                label="Large_Memory_Mix",
                description="Large memory banks with dynamic BST and zipper players.",
                players=[
                    PlayerSpec(code="p_bst_dynamic_width", count=2),
                    PlayerSpec(code="p_zipper", count=2),
                    PlayerSpec(code="p_selfless_greedy", count=2),
                ],
                length=55,
                memory_size=30,
                subjects=28,
                rounds=2,
                seed=888,
                metadata={"category": "stress", "memory_size": 30},
            ),
        ],
    )

    edge_suite = BenchmarkSuite(
        name="Edge Cases",
        description="Edge-case scenarios focusing on pauses and subject scarcity.",
        focus_player="p_selfish_greedy",
        variants=[
            SimulationVariant(
                label="Pause_Dominant",
                description="High pause pressure with pause players and greedy competitors.",
                players=[
                    PlayerSpec(code="pp", count=3),
                    PlayerSpec(code="p_selfish_greedy", count=2),
                    PlayerSpec(code="pr", count=1),
                ],
                length=20,
                memory_size=8,
                subjects=16,
                rounds=3,
                seed=999,
                metadata={"edge_case": "pause"},
            ),
            SimulationVariant(
                label="Low_Subject_Squeeze",
                description="Fewer subjects increase repetition pressure.",
                players=[
                    PlayerSpec(code="p_bst_low", count=2),
                    PlayerSpec(code="p_balanced_greedy", count=2),
                    PlayerSpec(code="pr", count=2),
                ],
                length=22,
                memory_size=10,
                subjects=8,
                rounds=3,
                seed=1001,
                metadata={"edge_case": "low_subjects"},
            ),
        ],
    )

    return BenchmarkScenario(
        name="Default Benchmark Suite",
        description="Comprehensive benchmark covering baseline, self-play, stress, and edge scenarios.",
        suites=[baseline_suite, self_play_suite, stress_suite, edge_suite],
    )


SCENARIO_BUILDERS = {
    "default": build_default_scenario,
}
