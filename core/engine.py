import random
import uuid

from models.item import Item


class Engine:
	def __init__(
		self, players: int, subjects: int, memory_size: int, conversation_length: int
	) -> None:
		self.players = players
		self.subjects = [i for i in range(subjects)]
		self.memory_size = memory_size
		self.conversation_length = conversation_length

		self.history: list[Item] = []
		self.last_player = None
		self.turn = 0

	def generate_preference(self) -> list[int]:
		return random.sample(self.subjects, len(self.subjects))

	def generate_items(self) -> tuple[Item, ...]:
		items: list[Item] = []

		for i in range(self.memory_size):
			samples = 2 if i < self.memory_size // 2 else 1

			importance = round(random.random(), 2)
			subjects = tuple(random.sample(self.subjects, samples))

			item = Item(id=uuid.uuid4(), importance=importance, subjects=subjects)
			items.append(item)

		return tuple(items)
