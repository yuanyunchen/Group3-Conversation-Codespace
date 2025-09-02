import pygame as pg

from ui.base import BLACK, WHITE


class TurnDisplay(pg.sprite.Sprite):
	def __init__(self, x: int, y: int, width: int, height: int, *groups) -> None:
		pg.sprite.Sprite.__init__(self, *groups)
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.rect = pg.Rect(x, y, width, height)
		self.font = pg.font.SysFont(None, 20)
		self.turn_info = {}
		self.image = pg.Surface((width, height), pg.SRCALPHA)
		self.update_display()

	def update_info(self, turn_info: dict):
		self.turn_info = turn_info
		self.update_display()

	def update_display(self):
		self.image.fill(WHITE)
		pg.draw.rect(self.image, BLACK, self.image.get_rect(), width=2, border_radius=10)

		info_texts = []

		if not self.turn_info:
			pause_text = self.font.render('--- PAUSE ---', True, BLACK)
			info_texts.append(pause_text)
		else:
			turn_text = f'Turn: {self.turn_info.get("turn", 0)}'
			info_texts.append(self.font.render(turn_text, True, BLACK))

			speaker_name = 'N/A'
			if self.turn_info.get('speaker'):
				speaker_name = self.turn_info.get('speaker')
			speaker_text = f'Speaker: {speaker_name}'
			info_texts.append(self.font.render(speaker_text, True, BLACK))

			item_id = 'N/A'
			if self.turn_info.get('item'):
				item_id = str(self.turn_info['item'].id).split('-')[0]
			item_text = f'Item ID: {item_id}'
			info_texts.append(self.font.render(item_text, True, BLACK))

		y_offset = 10
		for text_surface in info_texts:
			text_rect = text_surface.get_rect(centerx=self.width / 2, top=y_offset)
			self.image.blit(text_surface, text_rect)
			y_offset += text_surface.get_height() + 5

	def draw(self, surface: pg.Surface):
		surface.blit(self.image, self.rect)
