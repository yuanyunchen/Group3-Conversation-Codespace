import sys

import pygame as pg

from core.engine import Engine
from ui.base import BG_DARK, screen
from ui.player_info import PlayerInfo


def run_gui(engine: Engine):
	player_card = PlayerInfo(snapshot=engine.snapshots[0], x=100, y=100)

	all_sprites = pg.sprite.Group()
	all_sprites.add(player_card)

	running = True
	while running:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False

			# Handle events for the player card
			player_card.handle_event(event)

		# Update the card's state
		all_sprites.update()

		# Drawing
		screen.fill(BG_DARK)
		all_sprites.draw(screen)

		pg.display.flip()

	pg.quit()
	sys.exit()
