from random import randrange
from src.config import Config

PLAYER_CHAR = "@"
WALL_CHAR = "#"
BOULDER_CHAR = "O"
GRASS_CHAR = "."
GRASS_ALT_CHAR = "_"
LADDER_CHAR = "H"
BUSH_CHAR = "B"
GEYSIR_CHAR = "M"
DOOR_CHAR = "D"
FORTIFIED_CHAR = "▓"
EMPTY_CHAR = " "

class Bot:
	def __init__(self, game, pos, floor):
		self.game = game

		self.pos = pos
		self.floor = floor
		self.zombieToDir = 0

	def move(self):

		if randrange(0, Config.botRandomTurnChange) == 0:
			self.zombieToDir = randrange(0, 4)

		def tryMoving():
			newPos = self.game.getNextPos(self.pos, self.zombieToDir)

			if self.game.getTitle(newPos, floor = self.floor) in [EMPTY_CHAR, GRASS_CHAR]:
				self.pos = newPos

			else:
				self.zombieToDir = randrange(0, 4)
				tryMoving()

		tryMoving()