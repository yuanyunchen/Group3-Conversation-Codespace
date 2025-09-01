import pygame as pg

from models.item import Item
from ui.base import BLACK
from ui.conversation_history.message import Message


class ConversationHistory:
	def __init__(self, x: int, y: int, width: int, max_height: int):
		self.x = x
		self.y = y
		self.width = width
		self.max_height = max_height
		self.messages: list[Message] = []
		self._total_height = 0

	def add_message(self, item: Item, sender: str):
		new_message = Message(
			item=item,
			sender=sender,
			x=self.x,
			y=0,
			max_width=self.width,
		)

		if self.messages:
			last_message = self.messages[-1]
			new_y = last_message.rect.bottom + 5
			new_message.rect.y = new_y
		else:
			new_message.rect.y = self.y

		self.messages.append(new_message)
		self._total_height = new_message.rect.bottom

		if self._total_height > self.max_height:
			scroll_offset = self._total_height - self.max_height
			for msg in self.messages:
				msg.rect.y -= scroll_offset
			self._total_height = self.max_height

	def draw(self, surface: pg.Surface):
		pg.draw.rect(surface, BLACK, (self.x, self.y, self.width, self.max_height), 2)
		for message in self.messages:
			surface.blit(message.image, message.rect)

	def clear(self):
		self.messages.clear()
		self._total_height = 0
