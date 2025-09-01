import random
import uuid

from models.item import Item
from models.player import PlayerSnapshot


class Engine:
	def __init__(
		self, players: int, subjects: int, memory_size: int, conversation_length: int
	) -> None:
		self.subjects = [i for i in range(subjects)]
		self.memory_size = memory_size
		self.conversation_length = conversation_length

		self.history: list[Item] = []
		self.last_player = None
		self.turn = 0

		self.snapshots = self.__initlize_snapshots(players)

	def __initlize_snapshots(self, player_count) -> list[PlayerSnapshot]:
		snapshots = []

		for _ in range(player_count):
			id = uuid.uuid4()
			preferences = self.__generate_preference()
			memory_bank = self.__generate_items()

			snapshot = PlayerSnapshot(id=id, preferences=preferences, memory_bank=memory_bank)

			snapshot.append(snapshot)

		return snapshots

	def __generate_preference(self) -> list[int]:
		return tuple(random.sample(self.subjects, len(self.subjects)))

	def __generate_items(self) -> tuple[Item, ...]:
		items: list[Item] = []

		for i in range(self.memory_size):
			samples = 2 if i < self.memory_size // 2 else 1

			importance = round(random.random(), 2)
			subjects = tuple(random.sample(self.subjects, samples))

			item = Item(id=uuid.uuid4(), importance=importance, subjects=subjects)
			items.append(item)

		return tuple(items)
