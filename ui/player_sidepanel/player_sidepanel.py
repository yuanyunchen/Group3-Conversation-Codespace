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

	def update(self):
		self.cards.update()
		self.image.fill(pg.Color(50, 50, 50))

		for card in self.cards:
			card_rect = card.rect.copy()
			card_rect.top += self.scroll_offset

			self.image.blit(card.image, card_rect.topleft)
