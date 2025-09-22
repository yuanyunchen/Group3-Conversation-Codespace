from models.player import GameContext, Item, Player, PlayerSnapshot


class Player8(Player):
	def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext) -> None:  # noqa: F821
		super().__init__(snapshot, ctx)

	@staticmethod
	def was_last_round_pause(history: list[Item]) -> bool:
		return len(history) >= 1 and history[-1] is None

	@staticmethod
	def get_last_n_subjects(history: list[Item], n: int) -> set[int]:
		return set(
			subject for item in history[-n:] if item is not None for subject in item.subjects
		)

	@staticmethod
	def subjects_from_items(items: list[Item]) -> set[int]:
		return {subject for item in items if item is not None for subject in item.subjects}

	@staticmethod
	def filter_unused(items: list[Item], history: list[Item]) -> list[Item]:
		return [item for item in items if item not in history]

	def get_fresh_items(self, history: list[Item]) -> list[Item]:
		fresh_items = []
		prev_subjects = self.get_last_n_subjects(history, 5)
		for item in self.memory_bank:
			for subject in item.subjects:
				fresh_subject = subject not in prev_subjects
				used = item in history
				if fresh_subject and not used and item not in fresh_items:
					fresh_items.append(item)
		return fresh_items

	def get_most_important_item(self, items: list[Item]) -> Item | None:
		if not items:
			return None
		return max(items, key=lambda item: item.importance)

	"""
		These subjects have already appeared twice before and are best to avoid, on the current try
	"""

	def monotonic_subjects(self, history: list[Item]) -> list[Item]:
		sub1, sub2 = set(), set()

		if len(history) >= 2:
			sub1 = set(self.subjects_from_items(history[-1:]))
			sub2 = set(self.subjects_from_items(history[-2:-1]))

		monotonic_subjects = list(sub1 & sub2)
		return monotonic_subjects

	def get_on_subject_items(
		self, items: list[Item], history: list[Item], monotonic_subjects: list[int]
	) -> list[Item]:
		context_subjects = self.get_last_n_subjects(history, 3)
		on_subject_items = []

		for item in items:
			for subject in item.subjects:
				item_has_current_subject = subject in context_subjects
				item_is_monotonic = subject in monotonic_subjects

				if (
					item_has_current_subject
					and not item_is_monotonic
					and item not in on_subject_items
				):
					on_subject_items.append(item)

		return on_subject_items

	def get_preferred_item_order(self) -> list[Item]:
		S = len(self.preferences)

		ranked_items = []
		for item in self.memory_bank:
			if not item.subjects:
				continue
			avg_bonus = sum(1 - (self.preferences[s] / S) for s in item.subjects) / len(
				item.subjects
			)
			if avg_bonus > 0.5:
				ranked_items.append((avg_bonus, item))

		ranked_items.sort(reverse=True, key=lambda x: x[0])
		return [item for _, item in ranked_items]

	def get_first_unused_item(self, items: list[Item], history: list[Item]) -> Item | None:
		return next(iter(self.filter_unused(items, history)), None)

	@staticmethod
	def filter_monotonic_items(subjects: list[int], items: list[Item]) -> list[Item]:
		return [item for item in items if not (set(subjects) & set(item.subjects))]

	def compute_item_bonus(self, item: Item, history: list[Item]) -> float:
		bonus = 0.0
		S = len(self.preferences)
		monotonic_subjects = set()

		if len(history) >= 3:
			last_three_items = history[-3:]  # last 3 items in order
			last_three_subjects_sets = [
				self.subjects_from_items([item]) for item in last_three_items
			]
			monotonic_subjects = set.intersection(
				*last_three_subjects_sets
			)  # subjects repeated in all 3

		if not item:
			return bonus

		# 1. Importance
		bonus += item.importance

		# 2. Individual preference
		if item.subjects:
			bonus += sum(1 - self.preferences[s] / S for s in item.subjects) / len(item.subjects)

		# 3. Freshness
		if self.was_last_round_pause(history):
			prev_subjects = self.get_last_n_subjects(history, 5)
			for subject in item.subjects:
				if subject not in prev_subjects:
					bonus += 1.0

		# 4. Monotony (subjects repeated in all last 3 items)
		for subject in item.subjects:
			if subject in monotonic_subjects:
				bonus -= 3

		# 5. Non-repetition
		if item in history:
			bonus -= 1.0

		# 6. Coherence
		context_window = history[-3:]  # last 3 items
		context_subjects = set()
		for ctx_item in context_window:
			if ctx_item is not None:
				context_subjects.update(ctx_item.subjects)

		# Only consider non-monotonic subjects for coherence
		coherent_subjects = set(item.subjects) & (context_subjects - monotonic_subjects)

		if len(coherent_subjects) == len(item.subjects):
			# Fully coherent
			bonus += 1.0
		elif len(coherent_subjects) > 0:
			# Partially coherent
			bonus += 1
		else:
			# Not coherent at all
			bonus -= 3

		return bonus

	def propose_item(self, history: list[Item]) -> Item | None:
		unused_items = self.filter_unused(self.memory_bank, history)
		preferred_item_order = self.get_preferred_item_order()
		monotonic_subjects = self.monotonic_subjects(history)

		candidates = [
			# 1. Most important on-subject
			lambda: self.get_most_important_item(
				self.get_on_subject_items(unused_items, history, monotonic_subjects)
			),
			# 2. Fresh item after pause
			lambda: self.get_most_important_item(self.get_fresh_items(history))
			if self.was_last_round_pause(history)
			else None,
			# 3. Fresh preferred
			lambda: self.get_first_unused_item(
				self.filter_monotonic_items(monotonic_subjects, preferred_item_order),
				history,
			),
			# 4. Most important unused
			lambda: self.get_most_important_item(
				self.filter_monotonic_items(monotonic_subjects, unused_items)
			),
			# 5. Most important overall
			lambda: self.get_most_important_item(
				self.filter_monotonic_items(monotonic_subjects, self.memory_bank)
			),
		]

		# Evaluate candidates and compute their bonuses once
		evaluated_items = [
			(item, self.compute_item_bonus(item, history))
			for candidate in candidates
			if (item := candidate()) is not None
		]

		if not evaluated_items:
			return None

		# Pick the candidate with the highest bonus
		best_item, best_bonus = max(evaluated_items, key=lambda x: x[1])

		# Only return it if bonus > 0
		return best_item if best_bonus >= 0 else None
