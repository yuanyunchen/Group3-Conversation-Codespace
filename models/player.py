import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.item import Item


@dataclass(frozen=True)
class PlayerSnapshot:
	id: uuid.UUID
	preferences: tuple[int, ...]
	memory_bank: tuple[Item, ...]


class Player(ABC):
	def __init__(self, snapshot: PlayerSnapshot, conversation_length: int) -> None:
		self.id = snapshot.id
		self.preferences = list(snapshot.preferences)
		self.memory_bank = list(snapshot.memory_bank)
		self.conversation_length = conversation_length

	@abstractmethod
	def propose_item(self, history: list[Item]) -> Item | None:
		pass
