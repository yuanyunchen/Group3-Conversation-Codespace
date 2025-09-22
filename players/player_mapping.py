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
from players.player_1.player import Player1
from players.player_2.player import Player2
from players.player_3.player import Player3
from players.player_4.player import Player4
from players.player_5.player import Player5
from players.player_6.player import Player6
from players.player_7.player import Player7
from players.player_8.player import Player8
from players.player_9.player import Player9
from players.player_10_RL.agent.player import Player10
from players.random_player import RandomPlayer
from players.zipper_player.player import ZipperPlayer

PLAYER_CODE_TO_CLASS = {
    "pr": RandomPlayer,
    "pp": PausePlayer,
    "p1": Player1,
    "p2": Player2,
    "p3": Player3,
    "p4": Player4,
    "p5": Player5,
    "p6": Player6,
    "p7": Player7,
    "p8": Player8,
    "p9": Player9,
    "p10": Player10,
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
