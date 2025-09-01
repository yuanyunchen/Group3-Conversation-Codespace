import pygame as pg

from models.player import PlayerSnapshot
from ui.base import BLACK, WHITE, font


class PlayerInfo(pg.sprite.Sprite):
	def __init__(self, snapshot: PlayerSnapshot, x: int, y: int, *groups) -> None:
		pg.sprite.Sprite.__init__(self, *groups)
		self.snapshot = snapshot
		self.card_width = 200
		self.card_height = 60
		self.image = pg.Surface((self.card_width, self.card_height), pg.SRCALPHA)
		self.rect = self.image.get_rect(topleft=(x, y))

	def update(self):
		self.image.fill(WHITE)

		pg.draw.rect(
			surface=self.image, color=BLACK, rect=(0, 0, self.card_width, self.card_height), width=2
		)

		text = font.render(f'Player: {str(self.snapshot.id)[:6]}', True, BLACK)
		text_rect = text.get_rect(center=(self.card_width // 2, self.card_height // 2))
		self.image.blit(text, text_rect)
