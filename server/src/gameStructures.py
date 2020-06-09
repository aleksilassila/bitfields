from time import time
from config import Config

class Geyser:
	def __init__(self, geyserId, position, floor):
		now = time()
		
		self.geyserId = geyserId
		self.position = position
		self.floor = floor

		self.lastCollected = now
		self.deathTime = now + Config.geyserLifespan * Config.minute


class Door:
	def __init__(self, position, floor, ownerId):
		self.position = position
		self.floor = floor
		self.ownerId = ownerId

		self.health = Config.doorHealth

class Fortified:
	def __init__(self, position, floor):
		self.position = position
		self.floor = floor

		self.health = Config.fortifyHealth