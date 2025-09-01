import sys

import pygame as pg

from core.engine import Engine
from ui.base import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, screen
from ui.player_sidepanel.player_sidepanel import PlayerSidepanel


def run_gui(engine: Engine):
	sidepanel = PlayerSidepanel(
		snapshots=engine.snapshots,
		x=50,
		y=25,
		width=SCREEN_WIDTH * 0.2,
		height=SCREEN_HEIGHT * 0.9,
	)

	all_sprites = pg.sprite.Group()
	all_sprites.add(sidepanel)

	running = True
	while running:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			sidepanel.handle_event(event)

		all_sprites.update()

		screen.fill(WHITE)
		all_sprites.draw(screen)

		pg.display.flip()

	pg.quit()
	sys.exit()
