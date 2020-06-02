import asyncio
import json
from random import randrange
from time import time

from src.config import Config
from src.generator import Generator
from src.bullet import Bullet
from src.gameStructures import Door, Fortified, Geyser

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

# Cant shoot nor move through
FULL_SOLID = [WALL_CHAR, BOULDER_CHAR, FORTIFIED_CHAR, DOOR_CHAR]

class Game:
    def __init__(self):

        self.logging = True

        # Game logic
        self.players = {}

        self.bullets = {}
        self.bulletsIndex = 0

        self.geysers = {}
        self.geysersIndex = 0

        self.doors = {}
        self.doorsIndex = 0

        self.fortified = {}
        self.fortifyIndex = 0

        # Game managment
        self.titlesToUpdate = []
        self.deadConnections = []
        self.mapDimensions = (61, 45)
        gen = Generator(self.mapDimensions[0], self.mapDimensions[1], -200)

        self.map = [gen.getUnderworld(), gen.getOverworld()]
        self.bouldersMap = gen.getBoulders()

        # Create initial boulders
        for floor in [0, 1]:
            for boulder in self.bouldersMap[floor]:
                boulderx = boulder[0]
                bouldery = boulder[1]
                self.map[floor][bouldery][boulderx] = BOULDER_CHAR


    ## NETWORKING AND GAME MANAGMENT
    async def start(self):
        async def tick():
            if tickCount % Config.tickrate == 0: # Every around second
                await self.updateStats()
                self.revivePlayers()

            self.updateBullets()
            await self.updatePlayers()
            await asyncio.sleep(1/Config.tickrate)

            if len(self.deadConnections) > 0:
                self.removeDeadConnections()


        tickCount = 1
        while True:
            await tick()

            if tickCount >= Config.tickrate:
                tickCount = 1
            else: tickCount += 1

    async def updatePlayers(self, scores = False):
        players = {}
        bullets = {}
        updates = []
        geysers = {}

        # player positions
        for playerId in self.players:
            players[playerId] = {
                "p": self.players[playerId].position,
                "f": self.players[playerId].floor
            }

        # Bullet positions
        for bulletKey in self.bullets:
            bullets[bulletKey] = {
                "p": self.bullets[bulletKey].position,
                "f": self.bullets[bulletKey].floor
            }

        # Geysirs
        for geyserId in self.geysers:
            state = 0
            diff = time() - self.geysers[geyserId].lastCollected
            if diff > 6 * Config.minute: state = 2
            elif diff > 3 * Config.minute: state = 1
            geysers[geyserId] = {
                "p": self.geysers[geyserId].position,
                "f": self.geysers[geyserId].floor,
                "s": state
            }

        # Title updates
        for pos in self.titlesToUpdate:
            updates.append({ "p": pos, "c": self.getTitle((pos[0], pos[1]), pos[2]) })
        self.titlesToUpdate = []

        for playerId in self.players:
            try:
                await self.players[playerId].socket.send(json.dumps({
                    "p": players, # Player positions
                    "i": playerId, # Self playerid
                    "f": self.players[playerId].floor, # Floor
                    "b": bullets, # Bullets
                    "u": updates,
                    "g": geysers
                }))
            
            except Exception as e:
                if self.logging: print(e)
                print(f"[-] Dead connection for {playerId}")
                self.deadConnections.append(playerId)

    async def updateStats(self):
        stats = {}

        # player positions
        for playerId in self.players:
            stats[playerId] = {
                "n": self.players[playerId].name,
                "s": self.players[playerId].score,
                "m": self.players[playerId].money,
                "b": self.players[playerId].bouldersPicked,
                "h": self.players[playerId].health,
                "p": self.players[playerId].position
            }

        for playerId in self.players:
            try:
                await self.players[playerId].socket.send("s" + json.dumps(stats))
            
            except Exception as e:
                if self.logging: print(e)
                print(f"[-] Dead connection for {playerId}")
                self.deadConnections.append(playerId)

    async def sendAnimation(self, animation, pos, floor):
        payload = {
            "a": animation,
            "p": pos,
            "f": floor
        }

        print(f"Sent animation {pos} {floor}")

        for playerId in self.players:
            try:
                await self.players[playerId].socket.send("a" + json.dumps(payload))

            
            except Exception as e:
                if self.logging: print(e)
                print(f"[-] Dead connection for {playerId}")
                self.deadConnections.append(playerId)

    def removeDeadConnections(self):
        for playerId in self.deadConnections:
            try:
                # Keep amount of boulders the same
                self.createRandomBoulder(self.players[playerId].bouldersPicked)
                self.players.pop(playerId)
                print(f"[-] Removed player {playerId}")
                
                self.deadConnections = []
            except Exception as e:
                if self.logging: print(e)
                print(e)
        

    async def managePlayer(self, playerId):
        try:
            player = self.players[playerId]

            # Do handshake
            handshake = json.loads(await player.socket.recv())

            if "name" in handshake:
                if handshake["name"] != "" and len(handshake["name"]) <= Config.nameMaxLen:
                    player.name = handshake["name"]
            else:
                raise Exception("No name provided")

            mapToSend = self.map

            for doorId in self.doors:
                pos = self.doors[doorId].position
                floor = self.doors[doorId].floor
                mapToSend[floor][pos[1]][pos[0]] = DOOR_CHAR

            for fortifyId in self.fortified:
                pos = self.fortified[fortifyId].position
                floor = self.fortified[fortifyId].floor
                mapToSend[floor][pos[1]][pos[0]] = FORTIFIED_CHAR


            await player.socket.send(json.dumps({
                "map": mapToSend,
                "tickrate": Config.tickrate,
                "playerId": playerId
            }))

            while True:
                data = await player.socket.recv()
                
                action = json.loads(data)

                # Check for speedhacks
                if time() - player.recvTime > (1/(Config.tickrate + Config.ticksForgiven)):
                    player.recvTime = time()
                    if not player.dead:

                        if "m" in action:
                            player.facing = action["m"]
                            self.movePlayer(playerId, action["m"])

                        if "s" in action:
                            self.shoot(playerId)

                        if "a" in action:
                            await self.action(playerId)

                        if "d" in action:
                            self.placeDoor(playerId)

                        if "f" in action:
                            self.fortify(playerId)

                else:
                    print(f"[?] Throttled {playerId}")
                
        except Exception as e:
            if self.logging: print(e)
            print(f"[-] Dead connection for {playerId}")
            self.deadConnections.append(playerId)
    
    def revivePlayers(self):
        for playerId in self.players:
            player = self.players[playerId]

            if player.dead:
                player.position = self.getSpawnPosition()
                player.dead = False


    ## GAME LOGIC
    def getTitle(self, pos, floor=1):

        if pos[0] < 0 or pos[0] >= self.mapDimensions[0]:
            return False
        if pos[1] < 0 or pos[1] >= self.mapDimensions[1]:
            return False

        char = self.map[floor][pos[1]][pos[0]]
        if char in [WALL_CHAR, BOULDER_CHAR]:
            return char

        # Check if other player is in title
        playerPositions = []
        for playerId in self.players:
            if self.players[playerId].floor == floor:
                playerPositions.append(self.players[playerId].position)

        if pos in playerPositions:
            return PLAYER_CHAR

        # Check if geyser is in title
        geyserPositions = []
        for geyserId in self.geysers:
            if self.geysers[geyserId].floor == floor:
                geyserPositions.append(self.geysers[geyserId].position)

        if pos in geyserPositions:
            return GEYSIR_CHAR

        # Check for doors
        doorPositions = []
        for doorId in self.doors:
            if self.doors[doorId].floor == floor:
                doorPositions.append(self.doors[doorId].position)

        # Check for fortified boulders
        fortifiedPositions = []
        for fortifyId in self.fortified:
            if self.fortified[fortifyId].floor == floor:
                fortifiedPositions.append(self.fortified[fortifyId].position)

        if pos in doorPositions:
            return DOOR_CHAR

        if pos in fortifiedPositions:
            return FORTIFIED_CHAR

        if char in [LADDER_CHAR, GRASS_CHAR, GRASS_ALT_CHAR, BUSH_CHAR]:
            return char

        return EMPTY_CHAR

    def getNextPos(self, pos, direction):
        if direction == 0:
            nextPos = (pos[0], pos[1] - 1)
        elif direction == 1:
            nextPos = (pos[0] + 1, pos[1])
        elif direction == 2:
            nextPos = (pos[0], pos[1] + 1)
        else:
            nextPos = (pos[0] - 1, pos[1])

        return nextPos

    def getSpawnPosition(self):
        while True:
            pos = (randrange(self.mapDimensions[0]), randrange(self.mapDimensions[1]))
            if self.getTitle(pos, 1) not in [PLAYER_CHAR, BOULDER_CHAR, WALL_CHAR]:
                return pos

    def movePlayer(self, playerId, direction):
        player = self.players[playerId]
        
        pos = self.getNextPos(player.position, player.facing)

        if self.mapDimensions[0] - 1 >= pos[0] >= 0 and self.mapDimensions[1] - 1 >= pos[1] >= 0:
            title = self.getTitle(pos, player.floor)

            if title == LADDER_CHAR:
                player.floor = 0 if player.floor == 1 else 1

            # Check if door is owned by you
            elif title == DOOR_CHAR:
                for doorId in self.doors:
                    if self.doors[doorId].position == pos:
                        if self.doors[doorId].ownerId != playerId:
                            return
                        break


            if not title in [PLAYER_CHAR, BOULDER_CHAR, WALL_CHAR, GEYSIR_CHAR, FORTIFIED_CHAR]:
                player.position = pos

    def shoot(self, playerId):
        index = self.bulletsIndex
        player = self.players[playerId]

        now = time()
        if now - player.shootTime < Config.shootDelay:
            return

        player.shootTime = now

        self.bulletsIndex += 1
        if self.bulletsIndex > 65535:
            self.bulletsIndex = 0

        pos = self.getNextPos(player.position, player.facing)

        for playerKey in self.players:
            if self.players[playerKey].position == pos and player.floor == self.players[playerKey].floor:
                self.kill(playerKey, playerId)
                return

        if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
            return
        elif self.getTitle(pos, player.floor) in FULL_SOLID:
            return

        self.bullets[index] = Bullet(index, playerId, pos, player.floor, player.facing)

    def updateBullets(self):
        toRemove = []
        for bulletKey in self.bullets:
            bullet = self.bullets[bulletKey]
            pos = self.getNextPos(bullet.position, bullet.direction)

            # Check if bullet is in playarea
            if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
                toRemove.append(bulletKey)

            # Check for collisions
            elif self.getTitle(pos, bullet.floor) in FULL_SOLID:
                toRemove.append(bulletKey)

            # Check for kills
            else:
                for playerKey in self.players:
                    if self.players[playerKey].position == pos and bullet.floor == self.players[playerKey].floor:
                        toRemove.append(bulletKey)
                        self.kill(playerKey, bullet.owner)

            bullet.position = pos

        # Garbage collect bullets
        for bulletKey in toRemove:
            try:
                self.bullets.pop(bulletKey)
            except:
                pass

    def kill(self, playerId, ownerId):
        player = self.players[playerId]
        owner = self.players[ownerId]

        if player.health < 2:
            player.dead = True
            player.position = (None, None)
            player.floor = 1
        else: player.health -= 1

        owner.score += 100
        owner.money += 100

    def createRandomBoulder(self, count):
        for i in range(count):
            while True:
                pos = (randrange(0, self.mapDimensions[0]), randrange(0, self.mapDimensions[1]))
                floor = randrange(0, len(self.map))

                if self.getTitle(pos, floor) == EMPTY_CHAR:
                    self.map[floor][pos[1]][pos[0]] = BOULDER_CHAR
                    self.titlesToUpdate.append((pos[0], pos[1], floor))
                    break

    def pick(self, player, pos):
        player.bouldersPicked += 1
        self.map[player.floor][pos[1]][pos[0]] = EMPTY_CHAR
        self.titlesToUpdate.append((pos[0], pos[1], player.floor))

    def place(self, player, pos):
        player.bouldersPicked -= 1
        self.map[player.floor][pos[1]][pos[0]] = BOULDER_CHAR
        self.titlesToUpdate.append((pos[0], pos[1], player.floor))

    async def mineWall(self, player, pos, title):
        now = time()
        if now - player.mineTime < Config.mineDelay:
            return

        player.mineTime = now

        if title == WALL_CHAR:
            if randrange(0, Config.geyserChange) == 0: # 1/15 Change of finding a geyser
                self.map[player.floor][pos[1]][pos[0]] = EMPTY_CHAR

                geyserId = self.geysersIndex
                self.geysersIndex += 1

                self.geysers[geyserId] = Geyser(geyserId, pos, player.floor)

            else: # Just break the wall
                self.map[player.floor][pos[1]][pos[0]] = BOULDER_CHAR
                self.titlesToUpdate.append((pos[0], pos[1], player.floor))
        elif title == DOOR_CHAR:
            for doorId in self.doors:
                if pos == self.doors[doorId].position:
                    door = self.doors[doorId]
                    door.health -= 1
                    
                    if door.health <= 0:
                        self.doors.pop(doorId)
                        self.titlesToUpdate.append((pos[0], pos[1], player.floor))
                    else:
                        await self.sendAnimation("b", pos, player.floor)

                    break

        elif title == FORTIFIED_CHAR:
            for fortifyId in self.fortified:
                if pos == self.fortified[fortifyId].position:
                    fortified = self.fortified[fortifyId]
                    fortified.health -= 1
                    
                    if fortified.health <= 0:
                        self.fortified.pop(fortifyId)
                        self.titlesToUpdate.append((pos[0], pos[1], player.floor))
                    else:
                        await self.sendAnimation("b", pos, player.floor)

                    break

    async def action(self, playerId):
        player = self.players[playerId]
        pos = self.getNextPos(player.position, player.facing)
        title = self.getTitle(pos, player.floor)

        if title == False:
            return

        if title == EMPTY_CHAR and player.bouldersPicked > 0:
            self.place(player, pos)
        elif title == BOULDER_CHAR and player.bouldersPicked < 2:
            self.pick(player, pos)
        elif title in [WALL_CHAR, DOOR_CHAR, FORTIFIED_CHAR]:
            await self.mineWall(player, pos, title)
        elif title == GEYSIR_CHAR:
            for geyserId in self.geysers:
                if self.geysers[geyserId].position == pos:
                    self.collectGeysir(playerId, geyserId)
                    break

    def collectGeysir(self, playerId, geyserId):
        geyser = self.geysers[geyserId]
        now = time()
        diff = round(now - geyser.lastCollected)
        gain = diff if diff <= Config.minute * 8 else Config.minute * 6

        self.players[playerId].money += gain
        self.players[playerId].score += gain

        if geyser.deathTime < now:
            self.geysers.pop(geyserId)

        geyser.lastCollected = now

    def placeDoor(self, playerId):
        player = self.players[playerId]
        pos = self.getNextPos(player.position, player.facing)
        title = self.getTitle(pos, player.floor)

        if player.money < Config.doorCost:
            return

        if title == EMPTY_CHAR:
            doorId = self.doorsIndex
            self.doorsIndex += 1

            self.doors[doorId] = Door(pos, player.floor, playerId)

            player.money -= Config.doorCost
            self.titlesToUpdate.append((pos[0], pos[1], player.floor))

    def fortify(self, playerId):
        player = self.players[playerId]
        pos = self.getNextPos(player.position, player.facing)
        title = self.getTitle(pos, player.floor)

        if player.money < Config.fortifyCost:
            return

        if title == BOULDER_CHAR:
            self.map[player.floor][pos[1]][pos[0]] = EMPTY_CHAR

            fortifyId = self.fortifyIndex
            self.fortifyIndex += 1

            self.fortified[fortifyId] = Fortified(pos, player.floor)

            player.money -= Config.fortifyCost
            self.titlesToUpdate.append((pos[0], pos[1], player.floor))
