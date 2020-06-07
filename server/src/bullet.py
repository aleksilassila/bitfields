class Bullet:
	def __init__(self, bulletId, owner, position, floor, direction):
		self.bulletId = bulletId
		self.owner = owner
		self.position = position
		self.lastPosition = position
		self.floor = floor
		self.direction = direction