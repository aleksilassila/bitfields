import asyncio
import json
from random import randrange
from time import time
from math import floor, ceil

from config import *
from src.generator import Generator
from src.gameStructures import Geyser
from src.ai import Bot

class Game:
    def __init__(self):
        self.logging = True

        # Game logic
        self.players = {}
        self.bots = {}
        self.botsInactive = {}

        self.bullets = {}
        self.bulletsIndex = 0

        self.geysers = {}
        self.geysersInactive = {}
        self.geysersIndex = 0

        self.doors = {}
        self.doorsIndex = 0

        self.fortified = {}
        self.fortifyIndex = 0

        # Game managment
        self.titlesToUpdate = []
        self.deadConnections = []
        self.mapDimensions = MAPDIMENSIONS
        gen = Generator(self.mapDimensions[0], self.mapDimensions[1], -200)

        self.map = [gen.getUnderworld(), gen.getOverworld()]
        self.bouldersMap = gen.getBoulders()

        # Create initial boulders
        for floor in [0, 1]:
            for boulder in self.bouldersMap[floor]:
                boulderx = boulder[0]
                bouldery = boulder[1]
                self.map[floor][bouldery][boulderx] = BOULDER_CHAR

        # Create initial bots
        botId = 0
        for x in range(0, round(BOTAMOUNT)):

            if x % 2 == 0: # 1/2 of bot amount in overworld
                self.botsInactive[botId] = Bot(self, self.getSpawnPosition(), 1)
                botId += 1

            self.botsInactive[botId] = Bot(self, self.getSpawnPosition(floor = 0), 0)
            botId += 1


    ## NETWORKING AND GAME MANAGMENT
    async def start(self):
        async def tick():
            nonlocal lastChunks

            self.moveBullets()

            if tickCount % (2 * TICKRATE) == 0: # Every around 2 seconds
                await self.updateStats()
                self.revivePlayers()

            chunksActivated = []
            chunks = []

            # Player loop
            for playerId in self.players:
                player = self.players[playerId]

                # Do actions
                if "m" in player.queue and player.position[0] != None: # Fix this
                    player.move()

                if "s" in player.queue:
                    player.shoot()

                if "a" in player.queue:
                    await player.action()

                if "d" in player.queue:
                    player.placeDoor()

                if "f" in player.queue:
                    player.fortifyBoulder()

                # Create chunk map of activated
                for chunk in player.chunks:
                    if not chunk in lastChunks:
                        chunksActivated.append(chunk)

                    chunks.append(chunk)

                for bulletId in dict(self.bullets):
                    bullet = self.bullets[bulletId]

                    if player.position == bullet.position and player.floor == bullet.floor and not bullet.owner == playerId:
                        self.kill(playerId, bullet.owner)
                        self.bullets.pop(bulletId)
                        break

                lastChunks = chunks

            # Active bots
            for botId in dict(self.botsInactive):
                if self.botsInactive[botId].chunk in chunksActivated:
                    self.bots[botId] = self.botsInactive.pop(botId)
                    if LOGGING: print(f"[G] Active bot: {botId}")

            # Bot loop
            for botId in dict(self.bots):
                bot = self.bots[botId]

                if not bot.chunk in chunks:
                    self.botsInactive[botId] = self.bots.pop(botId)
                    if LOGGING: print(f"[G] Disabled bot: {botId}")

                else:
                    lastBotPos = bot.pos
                    bot.move()

                    # Check if bot was killed
                    for bulletId in dict(self.bullets):
                        bullet = self.bullets[bulletId]

                        if bullet.position == bot.pos and bullet.floor == bot.floor:
                            self.kill(botId, bullet.owner, botKilled = True)
                            self.bullets.pop(bulletId)
                            break

                        elif bullet.lastPosition == bot.pos and lastBotPos == bullet.position and bullet.floor == bot.floor:
                            self.kill(botId, bullet.owner, botKilled = True)
                            self.bullets.pop(bulletId)
                            break

            if len(self.deadConnections) > 0:
                self.removeDeadConnections()

            await self.updatePlayers()
            await asyncio.sleep(1/TICKRATE)

        tickCount = 1
        print("Server started.")
        while True:
            lastChunks = []
            await tick()

            if tickCount >= TICKRATE * 2:
                tickCount = 1
            else: tickCount += 1

    async def updatePlayers(self, scores = False):
        players = {}
        bots = {}
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
            if diff > 6 * MINUTE: state = 2
            elif diff > 3 * MINUTE: state = 1
            geysers[geyserId] = {
                "p": self.geysers[geyserId].position,
                "f": self.geysers[geyserId].floor,
                "s": state
            }

        # Title updates
        for pos in self.titlesToUpdate:
            updates.append({ "p": pos, "c": self.getTitle((pos[0], pos[1]), pos[2]) })
        self.titlesToUpdate = []

        # Bots
        for botId in self.bots:
            bots[botId] = {
                "p": self.bots[botId].pos,
                "f": self.bots[botId].floor
            }

        for playerId in self.players:
            try:
                await self.players[playerId].socket.send(json.dumps({
                    "p": players, # Player positions
                    "n": bots, # NPC positions
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
        

    async def managePlayer(self, playerId):
        try:
            player = self.players[playerId]

            # Do handshake
            handshake = json.loads(await player.socket.recv())

            if "name" in handshake:
                if handshake["name"] != "" and len(handshake["name"]) <= MAXNAMELENGTH:
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
                "tickrate": TICKRATE,
                "playerId": playerId
            }))

            player.chunks = self.getChunksAround(player.position)

            while True:
                data = await player.socket.recv()
                
                action = json.loads(data)
                player.queue = {}

                if not player.dead:

                    if "m" in action:
                        player.facing = action["m"]
                        player.queue["m"] = action["m"]

                    if "s" in action:
                        player.queue["s"] = 1

                    if "a" in action:
                        player.queue["a"] = 1

                    if "d" in action:
                        player.queue["d"] = 1

                    if "f" in action:
                        player.queue["f"] = 1
                
        except Exception as e:
            if self.logging: print(e)
            print(f"[-] Dead connection for {playerId}")
            self.deadConnections.append(playerId)
    
    def revivePlayers(self):
        for playerId in self.players:
            player = self.players[playerId]

            if player.dead:
                player.position = self.getSpawnPosition()
                player.chunks = self.getChunksAround(player.position)
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
            return GEYSER_CHAR

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

    def getChunk(self, pos, axis = None):
        if axis == "x":
            return floor(pos[0] / CHUNKSIZE)

        elif axis == "y":
            return floor(pos[1] / CHUNKSIZE)

        return (floor(pos[0] / CHUNKSIZE), floor(pos[1] / CHUNKSIZE))

    def getChunksAround(self, pos):
        output = []

        topLeftCorner = [
            pos[0] - floor(CLIENTDIMENSIONS[0]/2),
            pos[1] - floor(CLIENTDIMENSIONS[1]/2)
        ]

        if topLeftCorner[0] < 0: topLeftCorner[0] = 0
        if topLeftCorner[1] < 0: topLeftCorner[1] = 0
        if topLeftCorner[0] + CLIENTDIMENSIONS[0] >= MAPDIMENSIONS[0]:
            topLeftCorner[0] = MAPDIMENSIONS[0] - CLIENTDIMENSIONS[0]
        if topLeftCorner[1] + CLIENTDIMENSIONS[1] >= MAPDIMENSIONS[1]:
            topLeftCorner[1] = MAPDIMENSIONS[1] - CLIENTDIMENSIONS[1]

        maxAmountOfChunksX = ceil(CLIENTDIMENSIONS[0] / CHUNKSIZE) + 1
        maxAmountOfChunksY = ceil(CLIENTDIMENSIONS[1] / CHUNKSIZE) + 1

        for y in range(maxAmountOfChunksY):
            for x in range(maxAmountOfChunksX):
                chunk = self.getChunk((topLeftCorner[0] + x * CHUNKSIZE, topLeftCorner[1] + y * CHUNKSIZE))
                output.append(chunk)

        return output

    def getSpawnPosition(self, floor = 1):
        while True:
            pos = (randrange(4, self.mapDimensions[0] - 4), randrange(4, self.mapDimensions[1] - 4))
            
            if self.getTitle(pos, floor = floor) in PLAYER_CAN_MOVE_THROUGH:
                return pos

    def moveBullets(self):
        for bulletId in dict(self.bullets):
            bullet = self.bullets[bulletId]
            pos = self.getNextPos(bullet.position, bullet.direction)

            title = self.getTitle(pos, bullet.floor)

            # Check if bullet is in playarea
            if title == PLAYER_CHAR:
                pass

            elif self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
                self.bullets.pop(bulletId)
                continue

            # Check for collisions
            elif not title in PLAYER_CAN_MOVE_THROUGH:
                self.bullets.pop(bulletId)
                continue

            bullet.lastPosition = bullet.position
            bullet.position = pos

    def kill(self, killedId, killerId, botKilled = False):
        if botKilled:
            self.bots[killedId].pos = self.getSpawnPosition(floor = self.bots[killedId].floor)
            self.players[killerId].score += 80
            self.players[killerId].money += 100
            return

        killed = self.players[killedId]
        owner = self.players[killerId] if killerId != None else False 

        if killed.health < 2:
            killed.dead = True
            killed.position = (None, None)
            killed.floor = 1

        else: killed.health -= 1

        if owner:
            owner.score += 120
            owner.money += 150
        
        killed.money = killed.money - (20 if killerId != None else 10)
        if killed.money < 0: killed.money = 0

    def createRandomBoulder(self, count):
        for i in range(count):
            while True:
                pos = (randrange(0, self.mapDimensions[0]), randrange(0, self.mapDimensions[1]))
                floor = randrange(0, len(self.map))

                if self.getTitle(pos, floor) == EMPTY_CHAR:
                    self.map[floor][pos[1]][pos[0]] = BOULDER_CHAR
                    self.titlesToUpdate.append((pos[0], pos[1], floor))
                    break

    def createGeyser(self, pos, floor):
        self.map[floor][pos[1]][pos[0]] = EMPTY_CHAR

        geyserId = self.geysersIndex
        self.geysersIndex += 1

        self.geysers[geyserId] = Geyser(geyserId, pos, floor)
