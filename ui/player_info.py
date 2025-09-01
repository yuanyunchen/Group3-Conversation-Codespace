import pygame as pg

from models.player import PlayerSnapshot
from ui.base import ACCENT_GREEN, CARD_BLUE, CARD_HOVER_BLUE, TEXT_WHITE, font


class PlayerInfo(pg.sprite.Sprite):
	def __init__(self, snapshot: PlayerSnapshot, x: int, y: int, *groups) -> None:
		pg.sprite.Sprite.__init__(self, *groups)

		self.snapshot = snapshot
		self.is_expanded = False
		self.is_hovered = False

		self.card_width = 300
		self.card_height = 80

		self.image = pg.Surface((self.card_width, self.card_height), pg.SRCALPHA)
		self.rect = self.image.get_rect(topleft=(x, y))

	def handle_event(self, event: pg.event.Event) -> None:
		# Check for mouse click on the base card
		if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
			if self.rect.collidepoint(event.pos):
				self.is_expanded = not self.is_expanded
		# Check for mouse hover
		elif event.type == pg.MOUSEMOTION:
			self.is_hovered = self.rect.collidepoint(event.pos)

	def update(self) -> None:
		# Re-draw the sprite's image based on its state
		self.image.fill((0, 0, 0, 0))  # Clear the surface

		# Determine card color based on hover state
		card_color = CARD_HOVER_BLUE if self.is_hovered else CARD_BLUE

		# Draw the card's background
		pg.draw.rect(
			self.image, card_color, (0, 0, self.card_width, self.card_height), border_radius=10
		)
		pg.draw.rect(
			self.image,
			ACCENT_GREEN,
			(0, 0, self.card_width, self.card_height),
			width=2,
			border_radius=10,
		)

		# Draw player ID text
		player_id_text = f'Player ID: {str(self.snapshot.id)[:8]}'
		text_surface = font.render(player_id_text, True, TEXT_WHITE)
		text_rect = text_surface.get_rect(center=(self.card_width // 2, self.card_height // 2))
		self.image.blit(text_surface, text_rect)
