import pygame as pg

from ui.base import BLACK, WHITE, font


class Leaderboard(pg.sprite.Sprite):
	def __init__(
		self,
		scores: dict,
		player_names: dict,
		x: int,
		y: int,
		width: int,
		height: int,
		*groups,
	):
		super().__init__(*groups)
		self.scores = scores
		self.player_names = player_names
		self.image = pg.Surface((width, height), pg.SRCALPHA)
		self.rect = self.image.get_rect(topleft=(x, y))
		self.title_font = pg.font.SysFont(None, 36, bold=True)
		self.font = font

		self._render()

	def _render(self):
		self.image.fill(WHITE)
		pg.draw.rect(self.image, BLACK, self.image.get_rect(), width=2, border_radius=10)

		title_surface = self.title_font.render('Final Scores', True, BLACK)
		title_rect = title_surface.get_rect(centerx=self.rect.width / 2, top=20)
		self.image.blit(title_surface, title_rect)

		sorted_scores = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)

		y_offset = title_rect.bottom + 20
		for player_id, score in sorted_scores:
			player_name = self.player_names.get(player_id, 'Unknown Player')
			score_text = f'{player_name}: {score:.2f}'

			score_surface = self.font.render(score_text, True, BLACK)
			score_rect = score_surface.get_rect(centerx=self.rect.width / 2, top=y_offset)
			self.image.blit(score_surface, score_rect)

			y_offset += score_surface.get_height() + 10

	def draw(self, surface: pg.Surface):
		surface.blit(self.image, self.rect)
