from models.player import GameContext, PlayerSnapshot
from players.bayesian_tree_search_player.bst_player_presets import BayesianTreeBeamSearchPlayer


class BayesTreeBeamLow(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=2,
			breadth=4,
		)


class BayesTreeBeamMedium(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=3,
			breadth=16,
		)


class BayesTreeBeamHigh(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=6,
			breadth=128,
		)


class BayesTreeDynamicStandard(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=3,
			breadth_rate=0.5,
		)


class BayesTreeDynamicWidth(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=3,
			breadth_rate=4,
		)


class BayesTreeDynamicDepth(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
			depth=6,
			breadth_rate=0.5,
		)


class BayesTreeDynamicHigh(BayesianTreeBeamSearchPlayer):
	def __init__(
		self,
		snapshot: PlayerSnapshot,
		ctx: GameContext,
	) -> None:
		# breadth = 4 * |B|
		super().__init__(
			snapshot=snapshot,
			ctx=ctx,
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
