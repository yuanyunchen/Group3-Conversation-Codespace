import pygame as pg

from models.player import PlayerSnapshot
from ui.player_sidepanel.player_info import PlayerInfo


class PlayerSidepanel(pg.sprite.Sprite):
	def __init__(
		self, snapshots: list[PlayerSnapshot], x: int, y: int, width: int, height: int, *groups
	) -> None:
		pg.sprite.Sprite.__init__(self, *groups)
		self.snapshots = snapshots
		self.width = width
		self.height = height
		self.image = pg.Surface((width, height), pg.SRCALPHA)
		self.rect = self.image.get_rect(topleft=(x, y))

		self.cards = pg.sprite.Group()
		self.scroll_offset = 0

		self.create_cards()

	def create_cards(self):
		y_offset = 10
		for snapshot in self.snapshots:
			card = PlayerInfo(snapshot=snapshot, x=10, y=y_offset)
			y_offset += card.rect.height + 10

			self.cards.add(card)

		self.content_height = y_offset

	def handle_event(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				if event.button == 4:
					self.scroll_offset = min(self.scroll_offset + 20, 0)
				elif event.button == 5:
					max_scroll = max(0, self.content_height - self.height)
					self.scroll_offset = max(self.scroll_offset - 20, -max_scroll)

	def update(self):
		self.cards.update()
		self.image.fill(pg.Color(50, 50, 50))

		for card in self.cards:
			blit_x = card.rect.x
			blit_y = card.rect.y + self.scroll_offset

			temp_rect = card.rect.copy()
			temp_rect.top = blit_y

			if self.image.get_rect().colliderect(temp_rect):
				self.image.blit(card.image, (blit_x, blit_y))
