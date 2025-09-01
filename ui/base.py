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
WHITE = (255, 255, 255)
