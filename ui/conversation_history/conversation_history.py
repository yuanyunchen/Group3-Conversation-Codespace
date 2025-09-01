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
		self.scroll_offset = 0
		self.rect = pg.Rect(x, y, width, max_height)
		self.message_spacing = 5

	def add_message(self, item: Item, sender: str):
		new_message = Message(
			item=item,
			sender=sender,
			x=self.x + self.message_spacing,
			y=0,
			max_width=self.width - self.message_spacing * 2,
		)

		if self.messages:
			last_message = self.messages[-1]
			new_y = last_message.rect.bottom + self.message_spacing
			new_message.rect.y = new_y
		else:
			new_message.rect.y = self.y + self.message_spacing

		self.messages.append(new_message)
		self._total_height += new_message.rect.height + self.message_spacing

		if self._total_height > self.max_height:
			self.scroll_offset = self.max_height - self._total_height

	def handle_event(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				if event.button == 4:
					self.scroll_offset = min(self.scroll_offset + 20, 0)
				elif event.button == 5:
					max_scroll = max(0, self._total_height - self.max_height)
					self.scroll_offset = max(self.scroll_offset - 20, -max_scroll)

	def draw(self, surface: pg.Surface):
		pg.draw.rect(surface, BLACK, self.rect, width=2)

		message_surface = pg.Surface((self.width, self.max_height), pg.SRCALPHA)

		for message in self.messages:
			message_surface.blit(
				message.image,
				(message.rect.x - self.x, message.rect.y - self.y + self.scroll_offset),
			)

		surface.blit(message_surface, self.rect)

	def clear(self):
		self.messages.clear()
		self._total_height = 0
