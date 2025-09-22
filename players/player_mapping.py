"""Shared mapping from preset codes to player classes."""

from players.bayesian_tree_search_player.bst_players import (
    BayesTreeBeamHigh,
    BayesTreeBeamLow,
    BayesTreeBeamMedium,
    BayesTreeDynamicStandard,
    BayesTreeDynamicWidth,
)
from players.bayesian_tree_search_player.greedy_players import (
    BalancedGreedyPlayer,
    SelfishGreedyPlayer,
    SelflessGreedyPlayer,
)
from players.pause_player import PausePlayer
from players.player_3.player import Player3
from players.random_player import RandomPlayer
from players.zipper_player.player import ZipperPlayer

PLAYER_CODE_TO_CLASS = {
    "pr": RandomPlayer,
    "pp": PausePlayer,
    "p3": Player3,
    "p_zipper": ZipperPlayer,
    "p_balanced_greedy": BalancedGreedyPlayer,
    "p_selfless_greedy": SelflessGreedyPlayer,
    "p_selfish_greedy": SelfishGreedyPlayer,
    "p_bst_low": BayesTreeBeamLow,
    "p_bst_medium": BayesTreeBeamMedium,
    "p_bst_high": BayesTreeBeamHigh,
    "p_bst_dynamic": BayesTreeDynamicStandard,
    "p_bst_dynamic_width": BayesTreeDynamicWidth,
    "p_bst_dynamic_depth": BayesTreeDynamicWidth,
}

__all__ = ["PLAYER_CODE_TO_CLASS"]
