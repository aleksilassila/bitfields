from time import time

class Player:
	def __init__(self, playerId, ws, position, name, floor = 1, score = 0, money = 0, health = 1):
		now = time()

		self.playerId = playerId

		self.socket = ws
		self.position = position
		self.name = name

		self.floor = floor
		self.score = score
		self.money = money
		self.health = health
		
		self.dead = False
		self.facing = 0
		self.bouldersPicked = 0

		self.shootTime = now
		self.mineTime = now

		self.queue = {} 
		self.chunks = []