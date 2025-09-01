import pygame as pg

pg.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption('Minimal Player Card Demo')

# Fonts
font = pg.font.Font(None, 24)
small_font = pg.font.Font(None, 18)

# Colors
BLACK = (0, 0, 0)
NEON_GREEN = (0, 255, 0)
BG_DARK = (20, 20, 40)
CARD_BLUE = (35, 35, 70)
CARD_HOVER_BLUE = (45, 45, 80)
ACCENT_GREEN = (0, 255, 128)
ACCENT_PURPLE = (150, 50, 255)
TEXT_WHITE = (255, 255, 255)
