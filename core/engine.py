import random
import uuid
from collections import Counter
from typing import Optional, Type

from models.item import Item
from models.player import Player, PlayerSnapshot


class Engine:
	def __init__(
		self,
		players: list[Type[Player]],
		player_count: int,
		subjects: int,
		memory_size: int,
		conversation_length: int,
		seed: int,
	) -> None:
		random.seed(seed)

		self.subjects = [i for i in range(subjects)]
		self.memory_size = memory_size
		self.conversation_length = conversation_length
		self.players_count = player_count

		self.history: list[Optional[Item]] = []
		self.last_player_id: Optional[uuid.UUID] = None
		self.turn = 0
		self.consecutive_pauses = 0

		self.player_contributions: dict[uuid.UUID, list[Item]] = {}
		self.snapshots = self.__initialize_snapshots(player_count)
		self.players = [
			player(
				snapshot=self.snapshots[i],
				conversation_length=self.conversation_length,
			)
			for i, player in enumerate(players)
		]

		self.player_names = {player.id: player.name for player in self.players}

	def __initialize_snapshots(self, player_count) -> list[PlayerSnapshot]:
		snapshots = []

		for _ in range(player_count):
			id = uuid.uuid4()
			preferences = self.__generate_preference()
			memory_bank = self.__generate_items()

			snapshot = PlayerSnapshot(id=id, preferences=preferences, memory_bank=memory_bank)

			snapshots.append(snapshot)
			self.player_contributions[id] = []

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

	def __get_proposals(self) -> dict[uuid.UUID, Optional[Item]]:
		proposals = {}
		for player in self.players:
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

		min_contributions = min(len(self.player_contributions[uid]) for uid in proposed_players)
		eligible_speakers = [
			uid
			for uid in proposed_players
			if len(self.player_contributions[uid]) == min_contributions
		]

		speaker_id = random.choice(eligible_speakers)
		item = proposed_players[speaker_id]

		return speaker_id, item

	def __calculate_freshness_score(self, i: int, current_item: Item) -> float:
		if i == 0 or self.history[i - 1] is not None:
			return 0.0

		prior_items = (item for item in self.history[max(0, i - 6) : i - 1] if item is not None)
		prior_subjects = {s for item in prior_items for s in item.subjects}

		novel_subjects = [s for s in current_item.subjects if s not in prior_subjects]

		return float(len(novel_subjects))

	def __calculate_coherence_score(self, i: int, current_item: Item) -> float:
		context_items = []

		for j in range(i - 1, max(-1, i - 4), -1):
			if self.history[j] is None:
				break
			context_items.append(self.history[j])

		for j in range(i + 1, min(len(self.history), i + 4)):
			if self.history[j] is None:
				break
			context_items.append(self.history[j])

		context_subject_counts = Counter(s for item in context_items for s in item.subjects)
		score = 0.0

		if not all(subject in context_subject_counts for subject in current_item.subjects):
			score -= 1.0

		if all(context_subject_counts.get(s, 0) >= 2 for s in current_item.subjects):
			score += 1.0

		return score

	def __calculate_nonmonotonousness_score(
		self, i: int, current_item: Item, repeated: bool
	) -> float:
		if repeated:
			return -1.0

		if i < 3:
			return 0.0

		last_three_items = [self.history[j] for j in range(i - 3, i)]
		if all(
			item and any(s in item.subjects for s in current_item.subjects)
			for item in last_three_items
		):
			return -1.0

		return 0.0

	def __calculate_individual_score(self) -> dict[uuid.UUID, float]:
		individual_scores: dict[uuid.UUID, float] = {p.id: 0.0 for p in self.snapshots}

		for uid, contributed_items in self.player_contributions.items():
			snapshot = next(s for s in self.snapshots if s.id == uid)
			preferences = snapshot.preferences

			player_individual_score = 0.0
			for item in contributed_items:
				bonuses = [
					1 - preferences.index(s) / len(preferences)
					for s in item.subjects
					if s in preferences
				]
				if bonuses:
					player_individual_score += sum(bonuses) / len(bonuses)

			individual_scores[uid] = player_individual_score

		return individual_scores

	def __calculate_scores(self) -> tuple[float, dict[uuid.UUID, float]]:
		total_shared_score = 0.0
		unique_items: set[uuid.UUID] = set()

		for i, current_item in enumerate(self.history):
			if not current_item:
				continue

			if current_item.id in unique_items:
				total_shared_score += self.__calculate_nonmonotonousness_score(
					i, current_item, repeated=True
				)
			else:
				total_shared_score += current_item.importance
				total_shared_score += self.__calculate_coherence_score(i, current_item)
				total_shared_score += self.__calculate_freshness_score(i, current_item)
				total_shared_score += self.__calculate_nonmonotonousness_score(
					i, current_item, repeated=False
				)

			unique_items.add(current_item.id)

		individual_scores = self.__calculate_individual_score()

		return total_shared_score, individual_scores

	def final_scores(self) -> dict:
		shared_score, individual_scores = self.__calculate_scores()

		final_results = {}
		for uid in self.player_names:
			total_raw_score = shared_score + individual_scores.get(uid, 0.0)
			conversation_quality = (
				total_raw_score / self.conversation_length if self.conversation_length > 0 else 0
			)

			final_results[uid] = {
				'total': conversation_quality,
				'shared': shared_score,
				'individual': individual_scores.get(uid, 0.0),
			}

		return {
			'conversation_length': len(self.history),
			'pauses': self.history.count(None),
			'scores': final_results,
		}

	def __turn(self):
		proposals = self.__get_proposals()
		speaker, item = self.__select_speaker(proposals)

		if speaker:
			self.history.append(item)
			self.last_player_id = speaker
			self.consecutive_pauses = 0
			self.player_contributions[speaker].append(item)
		else:
			self.history.append(None)
			self.last_player_id = None
			self.consecutive_pauses += 1

		self.turn += 1
		return {
			'turn': self.turn,
			'speaker_id': speaker,
			'speaker_name': self.player_names.get(speaker, ''),
			'item': item,
			'proposals': proposals,
			'is_over': self.turn >= self.conversation_length or self.consecutive_pauses >= 3,
		}

	def step(self) -> Optional[dict]:
		if self.turn >= self.conversation_length or self.consecutive_pauses >= 3:
			return None

		return self.__turn()

	def run(self, players: list[Type[Player]]):
		while self.turn < self.conversation_length:
			self.__turn()

			if self.consecutive_pauses >= 3:
				break

		score_data = self.final_scores()
		scores = {pid: data['total'] for pid, data in score_data['scores'].items()}
		return self.history, scores
