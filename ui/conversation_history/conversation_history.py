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
		self.title_font = pg.font.SysFont(None, 24, bold=True)

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

		title_text = 'Conversation History'
		title_surface = self.title_font.render(title_text, True, BLACK)
		title_x = self.x + (self.width - title_surface.get_width()) / 2
		title_y = self.y + 5
		surface.blit(title_surface, (title_x, title_y))

		title_height_offset = title_surface.get_height() + 10
		messages_rect = pg.Rect(
			self.x, self.y + title_height_offset, self.width, self.max_height - title_height_offset
		)

		messages_content_surface = pg.Surface(
			(messages_rect.width, messages_rect.height), pg.SRCALPHA
		)

		y_offset = self.scroll_offset
		for message in self.messages:
			messages_content_surface.blit(message.image, (message.rect.x - self.x, y_offset))
			y_offset += message.rect.height + 5

		surface.blit(messages_content_surface, messages_rect.topleft)

	def clear(self):
		self.messages.clear()
		self._total_height = 0
