import pygame as pg

from models.item import Item
from ui.base import BLACK, WHITE
from ui.conversation_history.message import Message


class ConversationHistory(pg.sprite.Sprite):
	def __init__(self, x: int, y: int, width: int, max_height: int, *groups):
		pg.sprite.Sprite.__init__(self, *groups)
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
		self.title_height_offset = self.title_font.get_height() + 10

	def add_message(self, item: Item, sender: str):
		new_message = Message(
			item=item,
			sender=sender,
			x=self.x + self.message_spacing * 2,
			y=0,
			max_width=self.width - self.message_spacing * 4,
		)

		self.messages.insert(0, new_message)
		self._total_height = sum(m.rect.height + self.message_spacing for m in self.messages)
		self.scroll_offset = 0

	def handle_event(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				messages_rect_height = self.max_height - self.title_height_offset
				max_scroll = max(0, self._total_height - messages_rect_height)

				if event.button == 4:
					self.scroll_offset = min(self.scroll_offset + 20, max_scroll)
				elif event.button == 5:
					self.scroll_offset = max(self.scroll_offset - 20, 0)

	def draw(self, surface: pg.Surface):
		surface_with_styling = pg.Surface((self.width, self.max_height), pg.SRCALPHA)
		surface_with_styling.fill(WHITE)
		pg.draw.rect(
			surface_with_styling, BLACK, surface_with_styling.get_rect(), width=2, border_radius=10
		)

		title_text = 'Conversation History'
		title_surface = self.title_font.render(title_text, True, BLACK)
		title_x = (self.width - title_surface.get_width()) / 2
		title_y = 5
		surface_with_styling.blit(title_surface, (title_x, title_y))

		messages_rect = pg.Rect(
			10,
			self.title_height_offset,
			self.width - 20,
			self.max_height - self.title_height_offset - 10,
		)

		messages_content_surface = pg.Surface(
			(messages_rect.width, messages_rect.height), pg.SRCALPHA
		)

		y_offset = 0 - self.scroll_offset
		for message in self.messages:
			messages_content_surface.blit(
				message.image,
				(0, y_offset),
			)
			y_offset += message.rect.height + self.message_spacing

		surface_with_styling.blit(messages_content_surface, messages_rect.topleft)
		surface.blit(surface_with_styling, self.rect.topleft)

	def clear(self):
		self.messages.clear()
		self._total_height = 0
		self.scroll_offset = 0
