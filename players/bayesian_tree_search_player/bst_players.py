from models.player import PlayerSnapshot, GameContext
from players.bayesian_tree_search_player.bst_player_presets import BayesianTreeBeamSearchPlayer

# Global threshold for all presets
GLOBAL_BST_THRESHOLD = 0.5
GLOBAL_COMPETITION_RATE = 0.5


class BayesTreeBeamLow(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=2,
			breadth=4,
   			static_threhold=GLOBAL_BST_THRESHOLD
		)
  

class BayesTreeBeamMedium(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=3,
			breadth=16,
			static_threhold=GLOBAL_BST_THRESHOLD
		)
  
class BayesTreeBeamHigh(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=6,
			breadth=128,
			static_threhold=GLOBAL_BST_THRESHOLD
		)
  

class BayesTreeDynamicStandard(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=3,
			breadth_rate=0.5,
		)
  
  
class BayesTreeDynamicWidth(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=3,
			breadth_rate=4,
		)


class BayesTreeDynamicDepth(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=6,
			breadth_rate=0.5,
		)


class BayesTreeDynamicHigh(BayesianTreeBeamSearchPlayer):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext, initial_competition_rate: float = GLOBAL_COMPETITION_RATE) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			initial_competition_rate=initial_competition_rate,
			depth=6,
			breadth_rate=8,
		)

# hyperparameter tuning:
# P, B, L, S, T, history --> competition rate +  speack_pubishnishment

# threhold mechanism:
# history -> expectation of next rounds' shared score based on discounted average(parameter: discount_rate, context_length )

# test environment implementation:
# design the algorithm to generate test case: sample the global setting hyperparameters
# implement the benchmarking 
# test the test player with  -> cauculate the 