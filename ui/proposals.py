import pygame as pg

from ui.base import BLACK, WHITE
from ui.conversation_history.message import Message


class Proposals(pg.sprite.Sprite):
	def __init__(self, x: int, y: int, width: int, height: int, *groups) -> None:
		pg.sprite.Sprite.__init__(self, *groups)
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.rect = pg.Rect(x, y, width, height)
		self.image = pg.Surface((width, height), pg.SRCALPHA)
		self.proposals_title_font = pg.font.SysFont(None, 24, bold=True)
		self.scroll_offset = 0
		self.messages: list[Message] = []
		self._total_height = 0
		self.turn_info = {}
		self.player_names = {}

		self.update_display()

	def update_info(self, turn_info: dict, player_names: dict):
		self.turn_info = turn_info
		self.player_names = player_names
		self.update_display()

	def update_display(self):
		self.messages = []
		self._total_height = 0

		# TODO: Handle None
		if 'proposals' in self.turn_info:
			y_offset = 0
			for player_id, item in self.turn_info['proposals'].items():
				if item:
					speaker_name = self.player_names[player_id]
					message = Message(item, speaker_name, self.x, y_offset, self.width - 20)
					self.messages.append(message)
					y_offset += message.rect.height + 5
			self._total_height = y_offset

		self.image.fill(WHITE)
		pg.draw.rect(self.image, BLACK, self.image.get_rect(), width=2, border_radius=10)

		proposals_title = self.proposals_title_font.render('Proposals', True, BLACK)
		proposals_title_rect = proposals_title.get_rect(centerx=self.width / 2, top=10)
		self.image.blit(proposals_title, proposals_title_rect)

		title_height_offset = proposals_title.get_height() + 10
		messages_rect = pg.Rect(
			10, title_height_offset, self.width - 20, self.height - title_height_offset - 10
		)

		messages_content_surface = pg.Surface(
			(messages_rect.width, messages_rect.height), pg.SRCALPHA
		)

		y_offset = 0 - self.scroll_offset
		for message in self.messages:
			messages_content_surface.blit(message.image, (message.rect.x - self.x, y_offset))
			y_offset += message.rect.height + 5

		self.image.blit(messages_content_surface, messages_rect.topleft)

	def handle_event(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				title_height_offset = self.proposals_title_font.get_height() + 10
				messages_rect_height = self.height - title_height_offset - 10

				max_scroll = max(0, self._total_height - messages_rect_height)

				if event.button == 4:
					self.scroll_offset = max(self.scroll_offset - 20, 0)
					self.update_display()
				elif event.button == 5:
					self.scroll_offset = min(self.scroll_offset + 20, max_scroll)
					self.update_display()

	def draw(self, surface: pg.Surface):
		surface.blit(self.image, self.rect)
