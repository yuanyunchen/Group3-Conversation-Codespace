"""
Scoring functions and EWMA tracking for Player10.

This module contains the canonical delta scorer and player performance tracking
using exponential weighted moving averages (EWMA).
"""

import uuid
from collections import Counter
from collections.abc import Sequence

from models.item import Item

from ..config import (
	COHERENCE_WEIGHT,
	COHERENCE_WINDOW,
	EWMA_ALPHA,
	FRESHNESS_WEIGHT,
	FRESHNESS_WINDOW,
	IMPORTANCE_WEIGHT,
	MIN_SAMPLES_PID,
	MONOTONY_WEIGHT,
	MONOTONY_WINDOW,
)


class PlayerPerformanceTracker:
	"""
	Tracks player performance using EWMA for both global and per-player statistics.
	"""

	def __init__(self):
		# Global EWMA
		self.mu_global: float = 0.0
		self.count_global: int = 0

		# Per-player EWMA
		self.mu_by_pid: dict[uuid.UUID, float] = {}
		self.count_by_pid: dict[uuid.UUID, int] = {}

	def update(self, player_id: uuid.UUID, delta: float) -> None:
		"""
		Update both global and per-player EWMA with a new delta value.

		Args:
			player_id: The player who contributed the item
			delta: The delta score for this turn
		"""
		# Update global EWMA
		if self.count_global == 0:
			self.mu_global = delta
		else:
			self.mu_global = self.mu_global + EWMA_ALPHA * (delta - self.mu_global)
		self.count_global += 1

		# Update per-player EWMA
		if player_id not in self.mu_by_pid:
			self.mu_by_pid[player_id] = delta
			self.count_by_pid[player_id] = 1
		else:
			self.mu_by_pid[player_id] = self.mu_by_pid[player_id] + EWMA_ALPHA * (
				delta - self.mu_by_pid[player_id]
			)
			self.count_by_pid[player_id] += 1

	def get_trusted_mean(self, player_id: uuid.UUID) -> float:
		"""
		Get the trusted mean for a player (per-player if enough samples, else global).

		Args:
			player_id: The player to get the mean for

		Returns:
			The trusted mean delta for this player
		"""
		if self.count_by_pid.get(player_id, 0) >= MIN_SAMPLES_PID:
			return self.mu_by_pid.get(player_id, self.mu_global)
		return self.mu_global


def calculate_canonical_delta(
	item: Item, turn_idx: int, history: Sequence[Item | None], is_repeated: bool = False
) -> float:
	"""
	Calculate the canonical delta score for an item.

	Δ = importance + coherence + freshness - monotony

	Args:
		item: The item to score
		turn_idx: The turn index this item would be played at
		history: The conversation history
		is_repeated: Whether this item has been played before

	Returns:
		The canonical delta score
	"""
	if item is None:
		return 0.0

	# Importance component
	importance = float(getattr(item, 'importance', 0.0)) * IMPORTANCE_WEIGHT

	if is_repeated:
		# Repeated items only contribute to monotony (negative)
		coherence = 0.0
		freshness = 0.0
		monotony = -1.0 * MONOTONY_WEIGHT
	else:
		# Calculate all components for non-repeated items
		coherence = calculate_coherence_score(turn_idx, item, history) * COHERENCE_WEIGHT
		freshness = calculate_freshness_score(turn_idx, item, history) * FRESHNESS_WEIGHT
		monotony = calculate_monotony_score(turn_idx, item, history) * MONOTONY_WEIGHT

	return importance + coherence + freshness - monotony


def calculate_freshness_score(turn_idx: int, item: Item, history: Sequence[Item | None]) -> float:
	"""
	Calculate freshness score for an item.

	Only awards freshness if the previous turn was a pause.
	"""
	if turn_idx == 0:
		return 0.0

	# Only award freshness if previous turn was a pause
	if turn_idx > 0 and history[turn_idx - 1] is not None:
		return 0.0

	# Look back FRESHNESS_WINDOW turns before the pause
	prior_items = [
		item
		for item in history[max(0, turn_idx - FRESHNESS_WINDOW - 1) : turn_idx - 1]
		if item is not None
	]
	prior_subjects = {s for item in prior_items for s in item.subjects}
	novel_subjects = [s for s in item.subjects if s not in prior_subjects]

	return float(len(novel_subjects))


def calculate_coherence_score(turn_idx: int, item: Item, history: Sequence[Item | None]) -> float:
	"""
	Calculate coherence score for an item following official game rules.

	Official rule: For every item I, the (up to) 3 preceding items and (up to) 3 following
	items are collected into a set C_I of context items. The window defining C_I does not
	extend beyond the start of the conversation or any pauses.

	OLD VERSION (INCORRECT - stops at first pause):
	# Past context (up to COHERENCE_WINDOW, stop at pause)
	# for j in range(turn_idx - 1, max(-1, turn_idx - COHERENCE_WINDOW - 1), -1):
	#     if j < 0 or history[j] is None:
	#         break
	#     context_items.append(history[j])

	NEW VERSION (CORRECT - includes items up to but not across pause boundaries):
	"""
	context_items = []

	# Past context (up to COHERENCE_WINDOW, but don't extend across pause boundaries)
	# Look back up to 3 items, but stop if we hit a pause or start of conversation
	for j in range(turn_idx - 1, max(-1, turn_idx - COHERENCE_WINDOW - 1), -1):
		if j < 0:
			break
		if history[j] is None:
			# Hit a pause - stop here but don't include the pause
			# This means we don't extend across pause boundaries
			break
		context_items.append(history[j])

	# Future context (usually empty at proposal time, but follow same rules)
	for j in range(turn_idx + 1, min(len(history), turn_idx + COHERENCE_WINDOW + 1)):
		if history[j] is None:
			# Hit a pause - stop here but don't include the pause
			break
		context_items.append(history[j])

	if not context_items:
		# No context items means all subjects are not in context -> penalty
		return -1.0

	context_subject_counts = Counter(s for item in context_items for s in item.subjects)
	score = 0.0

	# Penalty if any subject not in context
	if not all(subject in context_subject_counts for subject in item.subjects):
		score -= 1.0

	# Bonus if all subjects mentioned at least twice in context
	if all(context_subject_counts.get(s, 0) >= 2 for s in item.subjects):
		score += 1.0

	return score


def calculate_monotony_score(turn_idx: int, item: Item, history: Sequence[Item | None]) -> float:
	"""
	Calculate monotony score for an item.

	Penalizes items that would continue a subject streak.

	OLD VERSION (INCORRECT):
		- Shadowed the candidate variable name by reusing `item` in a list
			comprehension/loop, making the condition effectively tautological:
			any(s in item.subjects for s in item.subjects)
			This always evaluates True when `item.subjects` is non-empty.
		- Did not explicitly ensure we were checking the last three non-pause
			items, which can under/over-count around pauses.

		Reference (commented out for posterity):
			# if turn_idx < MONOTONY_WINDOW:
			#     return 0.0
			# last_items = [history[j] for j in range(turn_idx - MONOTONY_WINDOW, turn_idx)]
			# if all(
			#     item is not None and any(s in item.subjects for s in item.subjects)
			#     for item in last_items
			# ):
			#     return 1.0
			# return 0.0

	CORRECT APPROACH (this implementation):
		- Look back over the last MONOTONY_WINDOW non-pause items.
		- Apply the spec: if ANY subject of the candidate appears in EACH of the
			last three non-pause items, return 1.0 (penalty). Otherwise 0.0.
	"""
	if turn_idx < MONOTONY_WINDOW:
		return 0.0

	# Consider only the last MONOTONY_WINDOW non-pause items
	last_items: list[Item] = []
	for j in range(turn_idx - 1, max(-1, turn_idx - MONOTONY_WINDOW - 1), -1):
		prev = history[j]
		if prev is None:
			continue
		last_items.append(prev)
		if len(last_items) >= MONOTONY_WINDOW:
			break

	# Not enough prior non-pause items to incur a penalty
	if len(last_items) < MONOTONY_WINDOW:
		return 0.0

	# Penalty if ANY subject of the candidate appears in EACH of the last
	# MONOTONY_WINDOW non-pause items
	candidate_subjects = tuple(getattr(item, 'subjects', ()) or ())
	if not candidate_subjects:
		return 0.0

	for subj in candidate_subjects:
		if all(subj in getattr(prev, 'subjects', ()) for prev in last_items):
			return 1.0

	return 0.0


def is_pause(item: Item | None) -> bool:
	"""
	Check if an item represents a pause.
	"""
	if item is None:
		return True

	is_pause_attr = getattr(item, 'is_pause', None)
	if isinstance(is_pause_attr, bool):
		return is_pause_attr

	subjects = getattr(item, 'subjects', None)
	return subjects is None or len(subjects) == 0


def subjects_of(item: Item) -> tuple[int, ...]:
	"""
	Extract subjects from an item.
	"""
	subjects = getattr(item, 'subjects', ())
	return tuple(subjects or ())


def is_repeated(item: Item, history: Sequence[Item | None]) -> bool:
	"""
	Check if an item has been played before in the history.
	"""
	item_id = getattr(item, 'id', None)
	if item_id is None:
		return False

	for hist_item in history:
		if is_pause(hist_item):
			continue
		if getattr(hist_item, 'id', None) == item_id:
			return True

	return False
