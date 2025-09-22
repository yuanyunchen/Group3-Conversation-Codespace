"""Static tournament configuration for the benchmarking pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from players.player_mapping import PLAYER_CODE_TO_CLASS

# Fixed player pool for benchmarking (test player is added on top).
BENCHMARK_PLAYERS = [
    "p1",
    "p2",
    "p4",
    "p5",
    "p6",
    "p7",
    "p8",
    "p9",
    "p10",
    "pr",
]


@dataclass(frozen=True)
class Lineup:
    """Single tournament lineup definition."""

    name: str
    selection_method: str
    description: str
    player_counts: dict[str, int]

    @property
    def total_players(self) -> int:
        return sum(self.player_counts.values())


def _validate_player_code(code: str) -> None:
    if code not in PLAYER_CODE_TO_CLASS:
        raise ValueError(f"Unknown player preset '{code}'. Update player_mapping first.")


def _ordered_unique(codes: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return ordered


def _pool_without_test(test_player: str) -> list[str]:
    pool = [code for code in BENCHMARK_PLAYERS if code != test_player]
    if not pool:
        raise ValueError("Player pool can not be empty")
    return pool


def _pick_group(
    pool: list[str],
    desired: int,
    test_player: str,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> list[str]:
    include = include or []
    exclude_set = set(exclude or [])
    picked: list[str] = []

    for code in include:
        if code == test_player or code in picked:
            continue
        if code not in pool:
            pool = [code, *pool]
        picked.append(code)

    for code in pool:
        if code == test_player:
            continue
        if code in picked or code in exclude_set:
            continue
        picked.append(code)
        if len(picked) >= desired:
            break

    if len(picked) < desired:
        raise ValueError(
            f"Unable to select {desired} unique players for lineup (have {len(picked)})."
        )
    return picked[:desired]


def generate_lineups(test_player: str) -> list[Lineup]:
    """Return the tournament lineups for the requested test player."""

    _validate_player_code(test_player)

    pool = _pool_without_test(test_player)
    base_pool = _ordered_unique(pool)
    lineups: list[Lineup] = []

    # Selection method 2: 1v1 matchups against every other player in pool
    for opponent in base_pool:
        player_counts = {test_player: 1, opponent: 1}
        lineups.append(
            Lineup(
                name=f"1v1_vs_{opponent}",
                selection_method="2",
                description=f"{test_player} vs {opponent}",
                player_counts=player_counts,
            )
        )

    # Selection method 6: leave-one-out from a six-player core
    base_six = base_pool[:6]
    if len(base_six) >= 5:
        for omitted in base_six:
            players = [code for code in base_six if code != omitted]
            if len(players) != len(base_six) - 1:
                continue
            player_counts = {test_player: 1}
            for code in players:
                player_counts[code] = 1
            lineups.append(
                Lineup(
                    name=f"leave_one_out_without_{omitted}",
                    selection_method="6",
                    description=f"One of each (omit {omitted})",
                    player_counts=player_counts,
                )
            )

    # Selection method 10: one of each from broad pool
    group_of_nine = _pick_group(pool, min(9, len(base_pool)), test_player, include=["pr"])
    if group_of_nine:
        lineups.append(
            Lineup(
                name="one_of_each",
                selection_method="10",
                description="One instance of distinct opponents",
                player_counts={test_player: 1, **{code: 1 for code in group_of_nine}},
            )
        )

    # Selection method 11: include random variants (regular / pause)
    regular_mix = _pick_group(pool, min(9, len(base_pool)), test_player, include=["pr"])
    if regular_mix:
        lineup_counts = {test_player: 1, **{code: 1 for code in regular_mix}}
        lineups.append(
            Lineup(
                name="one_each_plus_random",
                selection_method="11",
                description="One of each opponent plus regular random player",
                player_counts=lineup_counts,
            )
        )

    # Selection method 12: both random players present
    dual_random_mix = _pick_group(pool, min(9, len(base_pool)), test_player, include=["pr"])
    if dual_random_mix:
        lineup_counts = {test_player: 1, **{code: 1 for code in dual_random_mix}}
        lineup_counts["pr"] = lineup_counts.get("pr", 0) + 1
        lineups.append(
            Lineup(
                name="one_each_plus_two_random",
                selection_method="12",
                description="One of each opponent plus two regular random players",
                player_counts=lineup_counts,
            )
        )

    # Selection method 20: double every participant in the ten-player mix
    ten_group = [test_player, *_pick_group(pool, min(9, len(base_pool)), test_player, include=["pr"])]
    if ten_group:
        lineups.append(
            Lineup(
                name="double_round_roster",
                selection_method="20",
                description="Two copies of each participant",
                player_counts={code: 2 for code in ten_group},
            )
        )

    # Selection method 34: mixed marathon and mono-class stress tests
    marathon_mix = _pick_group(pool, min(9, len(base_pool)), test_player, include=["pr"])
    if marathon_mix:
        mixed_counts: dict[str, int] = {test_player: 4}
        for code in marathon_mix[:6]:
            mixed_counts[code] = 4
        for code in marathon_mix[6:]:
            mixed_counts[code] = 2
        lineups.append(
            Lineup(
                name="mixed_marathon",
                selection_method="34",
                description="Large roster covering multiple archetypes",
                player_counts=mixed_counts,
            )
        )

    mono_candidates = _ordered_unique([test_player, *base_pool])
    for code in mono_candidates:
        lineups.append(
            Lineup(
                name=f"mono_{code}",
                selection_method="34",
                description=f"All participants use {code}",
                player_counts={code: 34},
            )
        )

    return lineups


CONVERSATION_LENGTHS = [10, 50, 200, 1000]
SUBJECT_COUNTS = [5, 10, 20, 50]
MEMORY_MULTIPLIERS = {
    "not_enough": 0.5,
    "just_enough": 1.0,
    "more_than_enough": 1.5,
    "way_more_than_enough": 10.0,
}


def derive_memory_size(length: int, player_total: int, multiplier: float) -> int:
    base = max(1, round(length / max(1, player_total)))
    memory = max(1, round(base * multiplier))
    return memory
