"""Player registry used by benchmarking pipeline."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Tuple, Type

from models.player import Player
from players.pause_player import PausePlayer
from players.random_player import RandomPlayer
from players.zipper_player.player import ZipperPlayer
from players.player_3.player import Player3
from players.bayesian_tree_search_player.greedy_players import (
    BalancedGreedyPlayer,
    SelfishGreedyPlayer,
    SelflessGreedyPlayer,
)
from players.bayesian_tree_search_player.bst_players import (
    BayesTreeBeamHigh,
    BayesTreeBeamLow,
    BayesTreeBeamMedium,
    BayesTreeDynamicDepth,
    BayesTreeDynamicHigh,
    BayesTreeDynamicStandard,
    BayesTreeDynamicWidth,
)


PlayerFactory = Callable[..., Player]


class PlayerRegistry:
    """Registry for mapping short codes to player classes."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Player]] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        self.register("pr", RandomPlayer)
        self.register("pp", PausePlayer)
        self.register("p3", Player3)
        self.register("p_zipper", ZipperPlayer)
        self.register("p_balanced_greedy", BalancedGreedyPlayer)
        self.register("p_selfish_greedy", SelfishGreedyPlayer)
        self.register("p_selfless_greedy", SelflessGreedyPlayer)
        self.register("p_bst_low", BayesTreeBeamLow)
        self.register("p_bst_medium", BayesTreeBeamMedium)
        self.register("p_bst_high", BayesTreeBeamHigh)
        self.register("p_bst_dynamic", BayesTreeDynamicStandard)
        self.register("p_bst_dynamic_width", BayesTreeDynamicWidth)
        self.register("p_bst_dynamic_depth", BayesTreeDynamicDepth)
        self.register("p_bst_dynamic_high", BayesTreeDynamicHigh)

    def register(self, code: str, player_cls: Type[Player]) -> None:
        if code in self._registry:
            raise ValueError(f"Player code '{code}' already registered")
        self._registry[code] = player_cls

    def get(self, code: str) -> Type[Player]:
        if code not in self._registry:
            available = ", ".join(sorted(self._registry))
            raise KeyError(f"Unknown player code '{code}'. Known codes: {available}")
        return self._registry[code]

    def items(self) -> Iterable[Tuple[str, Type[Player]]]:
        return self._registry.items()

    def codes(self) -> Iterable[str]:
        return self._registry.keys()

    def __contains__(self, code: str) -> bool:  # pragma: no cover - convenience
        return code in self._registry


DEFAULT_PLAYER_REGISTRY = PlayerRegistry()


def get_player_class(code: str) -> Type[Player]:
    return DEFAULT_PLAYER_REGISTRY.get(code)


def available_player_codes() -> Iterable[str]:
    return DEFAULT_PLAYER_REGISTRY.codes()
