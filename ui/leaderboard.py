import pygame as pg

from ui.base import BLACK, WHITE


class Leaderboard(pg.sprite.Sprite):
	def __init__(
		self,
		score_data: dict,
		player_names: dict,
		x: int,
		y: int,
		width: int,
		height: int,
		*groups,
	):
		pg.sprite.Sprite.__init__(self, *groups)
		self.score_data = score_data
		self.player_names = player_names
		self.image = pg.Surface((width, height), pg.SRCALPHA)
		self.rect = self.image.get_rect(topleft=(x, y))

		self.title_font = pg.font.SysFont(None, 48, bold=True)
		self.header_font = pg.font.SysFont(None, 30, bold=True)
		self.data_font = pg.font.SysFont(None, 28)
		self.stats_font = pg.font.SysFont(None, 24)

		self._render()

	def _render(self):
		self.image.fill(WHITE)
		pg.draw.rect(self.image, BLACK, self.image.get_rect(), width=3, border_radius=15)

		title_surface = self.title_font.render('Conversation Results', True, BLACK)
		title_rect = title_surface.get_rect(centerx=self.rect.width / 2, top=25)
		self.image.blit(title_surface, title_rect)

		stats_text = (
			f'Conversation Length: {self.score_data["conversation_length"]} turns '
			f'({self.score_data["pauses"]} pauses)'
		)
		stats_surface = self.stats_font.render(stats_text, True, (100, 100, 100))
		stats_rect = stats_surface.get_rect(centerx=self.rect.width / 2, top=title_rect.bottom + 10)
		self.image.blit(stats_surface, stats_rect)

		padding = 40
		y_offset = stats_rect.bottom + 30
		col_width = (self.rect.width - padding * 2) / 4

		headers = ['Player', 'Total Score', 'Shared Score', 'Individual Score']
		for i, header in enumerate(headers):
			header_surface = self.header_font.render(header, True, BLACK)
			header_rect = header_surface.get_rect(
				centerx=padding + col_width * (i + 0.5), y=y_offset
			)
			self.image.blit(header_surface, header_rect)

		y_offset += header_surface.get_height() + 10
		pg.draw.line(
			self.image,
			(200, 200, 200),
			(padding, y_offset),
			(self.rect.width - padding, y_offset),
			2,
		)
		y_offset += 10

		scores = self.score_data['scores']
		sorted_players = sorted(scores.keys(), key=lambda pid: scores[pid]['total'], reverse=True)

		for player_id in sorted_players:
			player_name = self.player_names.get(player_id, 'Unknown')
			player_scores = scores[player_id]

			data_points = [
				player_name,
				f'{player_scores["total"]:.2f}',
				f'{player_scores["shared"]:.2f}',
				f'{player_scores["individual"]:.2f}',
			]

			for i, data in enumerate(data_points):
				data_surface = self.data_font.render(data, True, (50, 50, 50))
				data_rect = data_surface.get_rect(
					centerx=padding + col_width * (i + 0.5), y=y_offset
				)
				self.image.blit(data_surface, data_rect)

			y_offset += data_surface.get_height() + 15

	def draw(self, surface: pg.Surface):
		surface.blit(self.image, self.rect)
