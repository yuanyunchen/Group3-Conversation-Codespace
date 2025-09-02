from models.player import Item, Player, PlayerSnapshot


class PausePlayer(Player):
	def __init__(self, snapshot: PlayerSnapshot, name: str, conversation_length: int) -> None:  # noqa: F821
		super().__init__(snapshot, name, conversation_length)

	def propose_item(self, history: list[Item]):
		return None
