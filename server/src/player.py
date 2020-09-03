from time import time
from random import randrange

from config import *
from src.bullet import Bullet
from src.gameStructures import Door, Fortified

class Player:
    def __init__(self, game, playerId, ws, position, name, floor = 1, score = 0, money = 0, health = 1):
        now = time()

        self.game = game

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

    def move(self):
        pos = self.game.getNextPos(self.position, self.facing)

        if self.game.mapDimensions[0] - 1 >= pos[0] >= 0 and self.game.mapDimensions[1] - 1 >= pos[1] >= 0:
            title = self.game.getTitle(pos, self.floor)

            if title == LADDER_CHAR:
                self.floor = 0 if self.floor == 1 else 1

            # Check if door is owned by you
            elif title == DOOR_CHAR:
                for doorId in self.game.doors:
                    if self.game.doors[doorId].position == pos and self.game.doors[doorId].floor == self.floor:
                        if self.game.doors[doorId].ownerId != self.playerId:
                            return
                        break

            # Check if killed by bot
            for botId in self.game.bots:
                if self.game.bots[botId].pos == pos and self.game.bots[botId].floor == self.floor:
                    self.game.kill(self.playerId, None)

            if title in PLAYER_CAN_MOVE_THROUGH:
                self.position = pos

                # if pos[0] % CHUNKSIZE == 0 or pos[1] % CHUNKSIZE == 0:
                self.chunks = self.game.getChunksAround(pos)

    def shoot(self):
        index = self.game.bulletsIndex

        now = time()
        if now - self.shootTime < SHOOTDELAY:
            return

        self.shootTime = now

        self.game.bulletsIndex += 1
        if self.game.bulletsIndex > 65535:
            self.game.bulletsIndex = 0

        pos = self.game.getNextPos(self.position, self.facing)

        for playerKey in self.game.players:
            if self.game.players[playerKey].position == pos and self.floor == self.game.players[playerKey].floor:
                self.game.kill(playerKey, self.playerId)
                return

        if self.game.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.game.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
            return
        elif not self.game.getTitle(pos, self.floor) in PLAYER_CAN_MOVE_THROUGH:
            return

        self.game.bullets[index] = Bullet(index, self.playerId, pos, self.floor, self.facing)

    def pickBoulder(self, pos):
        self.bouldersPicked += 1
        self.game.map[self.floor][pos[1]][pos[0]] = EMPTY_CHAR
        self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))

    def placeBoulder(self, pos):
        self.bouldersPicked -= 1
        self.game.map[self.floor][pos[1]][pos[0]] = BOULDER_CHAR
        self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))


    async def mineWall(self, pos, title):
        now = time()
        if now - self.mineTime < MINEDELAY:
            return

        self.mineTime = now

        if title == WALL_CHAR:
            if randrange(0, GEYSERCHANCE) == 0: # 1/15 Change of finding a geyser
                self.game.createGeyser(pos, self.floor)

            else: # Just break the wall
                self.game.map[self.floor][pos[1]][pos[0]] = BOULDER_CHAR
                self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))

        elif title == DOOR_CHAR:
            for doorId in self.game.doors:
                if pos == self.game.doors[doorId].position:
                    door = self.game.doors[doorId]
                    door.health -= 1
                    
                    if door.health <= 0:
                        self.game.doors.pop(doorId)
                        self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))
                    else:
                        await self.game.sendAnimation("b", pos, self.floor)

                    break

        elif title == FORTIFIED_CHAR:
            for fortifyId in self.game.fortified:
                if pos == self.game.fortified[fortifyId].position:
                    fortified = self.game.fortified[fortifyId]
                    fortified.health -= 1
                    
                    if fortified.health <= 0:
                        self.game.fortified.pop(fortifyId)
                        self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))
                    else:
                        await self.game.sendAnimation("b", pos, self.floor)

                    break

    async def action(self):
        pos = self.game.getNextPos(self.position, self.facing)
        title = self.game.getTitle(pos, self.floor)

        if title == False:
            return

        if title == EMPTY_CHAR and self.bouldersPicked > 0:
            self.placeBoulder(pos)
        elif title == BOULDER_CHAR and self.bouldersPicked < 2:
            self.pickBoulder(pos)
        elif title in [WALL_CHAR, DOOR_CHAR, FORTIFIED_CHAR]:
            await self.mineWall(pos, title)
        elif title == GEYSER_CHAR:
            for geyserId in self.game.geysers:
                if self.game.geysers[geyserId].position == pos:
                    self.collectGeysir(geyserId)
                    break

    def collectGeysir(self, geyserId):
        geyser = self.game.geysers[geyserId]
        now = time()
        diff = round(now - geyser.lastCollected)
        gain = diff * GEYSERGAIN if diff * GEYSERGAIN <= GEYSERMAXGAIN else GEYSERMAXGAIN

        self.money += gain
        self.score += gain

        if geyser.deathTime < now:
            self.game.geysers.pop(geyserId)

        geyser.lastCollected = now

    def placeDoor(self):
        pos = self.game.getNextPos(self.position, self.facing)
        title = self.game.getTitle(pos, self.floor)

        if self.money < DOORCOST:
            return

        if title == EMPTY_CHAR:
            doorId = self.game.doorsIndex
            self.game.doorsIndex += 1

            self.game.doors[doorId] = Door(pos, self.floor, self.playerId)

            self.money -= DOORCOST
            self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))

    def fortifyBoulder(self):
        pos = self.game.getNextPos(self.position, self.facing)
        title = self.game.getTitle(pos, self.floor)

        if self.money < FORTIFYCOST:
            return

        if title == BOULDER_CHAR:
            self.game.map[self.floor][pos[1]][pos[0]] = EMPTY_CHAR

            fortifyId = self.game.fortifyIndex
            self.game.fortifyIndex += 1

            self.game.fortified[fortifyId] = Fortified(pos, self.floor)

            self.money -= FORTIFYCOST
            self.game.titlesToUpdate.append((pos[0], pos[1], self.floor))
