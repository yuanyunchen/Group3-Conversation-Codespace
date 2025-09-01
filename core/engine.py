import random
import uuid
from typing import Optional, Type

from models.item import Item
from models.player import Player, PlayerSnapshot


class Engine:
	def __init__(
		self, players: int, subjects: int, memory_size: int, conversation_length: int, seed: int
	) -> None:
		random.seed(seed)

		self.subjects = [i for i in range(subjects)]
		self.memory_size = memory_size
		self.conversation_length = conversation_length
		self.players_count = players

		self.history: list[Optional[Item]] = []
		self.last_player_id: Optional[uuid.UUID] = None
		self.turn = 0
		self.consecutive_pauses = 0

		self.player_contributions: dict[uuid.UUID, int] = {}
		self.snapshots = self.__initialize_snapshots(players)

	def __initialize_snapshots(self, player_count) -> list[PlayerSnapshot]:
		snapshots = []

		for _ in range(player_count):
			id = uuid.uuid4()
			preferences = self.__generate_preference()
			memory_bank = self.__generate_items()

			snapshot = PlayerSnapshot(id=id, preferences=preferences, memory_bank=memory_bank)

			snapshots.append(snapshot)
			self.player_contributions[id] = 0

		return snapshots

	def __generate_preference(self) -> list[int]:
		return tuple(random.sample(self.subjects, len(self.subjects)))

	def __generate_items(self) -> tuple[Item, ...]:
		items: list[Item] = []

		for i in range(self.memory_size):
			samples = 1 if i < self.memory_size // 2 else 2

			importance = round(random.random(), 2)
			subjects = tuple(random.sample(self.subjects, samples))

			item = Item(id=uuid.uuid4(), importance=importance, subjects=subjects)
			items.append(item)

		return tuple(items)

	def __get_proposals(self, players: list[Player]) -> dict[uuid.UUID, Optional[Item]]:
		proposals = {}
		for player in players:
			proposals[player.id] = player.propose_item(self.history)
		return proposals

	def __select_speaker(
		self, proposals: dict[uuid.UUID, Optional[Item]]
	) -> tuple[Optional[uuid.UUID], Optional[Item]]:
		proposed_players = {uid: item for uid, item in proposals.items() if item}

		if not proposed_players:
			return None, None

		if self.last_player_id and self.last_player_id in proposed_players:
			if random.random() < 0.5:
				item = proposed_players[self.last_player_id]
				return self.last_player_id, item

		min_contributions = min(self.player_contributions[uid] for uid in proposed_players)
		eligible_speakers = [
			uid for uid in proposed_players if self.player_contributions[uid] == min_contributions
		]

		speaker_id = random.choice(eligible_speakers)
		item = proposed_players[speaker_id]

		return speaker_id, item

	def __calculate_importance_score(
		self, current_item: Item, unique_items: set[uuid.UUID]
	) -> float:
		if current_item.id in unique_items:
			return 0.0
		unique_items.add(current_item.id)
		return current_item.importance

	def run(self, players: list[Type[Player]]):
		player_instances = [
			player(snapshot=self.snapshots[i], conversation_length=self.conversation_length)
			for i, player in enumerate(players)
		]

		while self.turn < self.conversation_length:
			proposals = self.__get_proposals(player_instances)
			speaker, item = self.__select_speaker(proposals)

			if speaker:
				self.history.append(item)
				self.last_player_id = speaker
				self.consecutive_pauses = 0
				self.player_contributions[speaker] += 1
			else:
				self.history.append(None)
				self.last_player_id = None
				self.consecutive_pauses += 1

			if self.consecutive_pauses >= 3:
				break

			self.turn += 1

		scores = {}

		return self.history, scores
