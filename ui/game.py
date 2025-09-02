import sys

import pygame as pg

from core.engine import Engine
from ui.base import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from ui.conversation_history.conversation_history import ConversationHistory
from ui.player_sidepanel.player_sidepanel import PlayerSidepanel
from ui.turn_display import TurnDisplay


class Game:
	def __init__(self, engine: Engine):
		pg.init()
		pg.display.set_caption('Conversations')

		self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
		self.engine = engine
		self.player_names = {
			str(self.engine.snapshots[0].id): 'Alice',
			str(self.engine.snapshots[1].id): 'Bob',
		}

		side_panel_x = 50
		side_panel_y = 25
		side_panel_width = SCREEN_WIDTH * 0.2
		side_panel_height = SCREEN_HEIGHT * 0.9

		chatbox_x = side_panel_x + side_panel_width + 10
		chatbox_y = 25
		chatbox_width = SCREEN_WIDTH * 0.35
		chatbox_height = SCREEN_HEIGHT * 0.7

		turn_display_x = chatbox_x + chatbox_width + 10
		turn_display_y = 25
		turn_display_width = SCREEN_WIDTH * 0.35
		turn_display_height = SCREEN_HEIGHT * 0.7

		self.sidepanel = PlayerSidepanel(
			snapshots=engine.snapshots,
			x=side_panel_x,
			y=side_panel_y,
			width=side_panel_width,
			height=side_panel_height,
		)
		self.conversation_history = ConversationHistory(
			x=chatbox_x,
			y=chatbox_y,
			width=chatbox_width,
			max_height=chatbox_height,
		)

		self.turn_display = TurnDisplay(
			turn_display_x, turn_display_y, turn_display_width, turn_display_height
		)

		self.running = True

	def run(self):
		while self.running:
			self._handle_events()
			self._draw()
			pg.display.flip()

		pg.quit()
		sys.exit()

	def _handle_events(self):
		for event in pg.event.get():
			if event.type == pg.QUIT:
				self.running = False

			self.sidepanel.handle_event(event)
			self.conversation_history.handle_event(event)

			if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
				turn_result = self.engine.step()
				self.turn_display.update_info(turn_result)

				if turn_result is not None and turn_result['item'] is not None:
					speaker_name = self.player_names.get(str(turn_result['speaker']), 'Unknown')
					self.conversation_history.add_message(turn_result['item'], speaker_name)

	def _draw(self):
		self.screen.fill(WHITE)
		self.sidepanel.update()
		self.sidepanel.draw(self.screen)
		self.turn_display.draw(self.screen)
		self.conversation_history.draw(self.screen)
