import asyncio
import json
from random import randrange
from src.generator import Generator
from time import time

PLAYER_CHAR = "@"
WALL_CHAR = "#"
BOULDER_CHAR = "O"
GRASS_CHAR = "."
GRASS_ALT_CHAR = "_"
LADDER_CHAR = "H"
BUSH_CHAR = "B"
GEYSIR_CHAR = "M"
EMPTY_CHAR = " "

class Game:
    def __init__(self, config):
        self.config = config

        self.logging = True
        # Game logic
        self.tickrate = 15 # 15 ticks per second
        self.players = {}
        """ players =
        playerId: {
            socket: websocket,
            position: (x, y),
            facing: 0,1,2,3,
            floor: 0,1,
            dead: False
        }
        """
        self.bullets = {}
        self.bulletsIndex = 0

        self.geysers = {}
        self.geysersIndex = 0

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
            if tickCount % self.tickrate == 0: # Every around second
                await self.updateStats()
                self.revivePlayers()

            self.updateBullets()
            await self.updatePlayers()
            await asyncio.sleep(1/self.tickrate)

            if len(self.deadConnections) > 0:
                self.removeDeadConnections()


        tickCount = 1
        while True:
            await tick()

            if tickCount >= self.tickrate:
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
                "p": self.players[playerId]["position"],
                "f": self.players[playerId]["floor"]
            }

        # Bullet positions
        for bulletKey in self.bullets:
            bullets[bulletKey] = {
                "p": self.bullets[bulletKey]["position"],
                "f": self.bullets[bulletKey]["floor"]
            }

        # Geysirs
        for geyserId in self.geysers:
            state = 0
            diff = time() - self.geysers[geyserId]["lastCollected"]
            if diff > 6 * self.config["minute"]: state = 2
            elif diff > 3 * self.config["minute"]: state = 1
            geysers[geyserId] = {
                "p": self.geysers[geyserId]["position"],
                "f": self.geysers[geyserId]["floor"],
                "s": state
            }

        # Title updates
        for pos in self.titlesToUpdate:
            updates.append({ "p": pos, "c": self.getTitle((pos[0], pos[1]), pos[2]) })
        self.titlesToUpdate = []

        for playerId in self.players:
            try:
                await self.players[playerId]["socket"].send(json.dumps({
                    "p": players, # Player positions
                    "i": playerId, # Self playerid
                    "f": self.players[playerId]["floor"], # Floor
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
                "n": self.players[playerId]["name"],
                "s": self.players[playerId]["score"],
                "m": self.players[playerId]["money"]
            }

        for playerId in self.players:
            try:
                await self.players[playerId]["socket"].send("s" + json.dumps(stats))
            
            except Exception as e:
                if self.logging: print(e)
                print(f"[-] Dead connection for {playerId}")
                self.deadConnections.append(playerId)

    def removeDeadConnections(self):
        for playerId in self.deadConnections:
            try:
                # Keep amount of boulders the same
                self.createRandomBoulder(self.players[playerId]["bouldersPicked"])
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
            handshake = json.loads(await player["socket"].recv())

            if "name" in handshake:
                if handshake["name"] != "" and len(handshake["name"]) <= self.config["nameMaxLen"]:
                    player["name"] = handshake["name"]
            else:
                raise Exception("No name provided")

            await player["socket"].send(json.dumps({
                "map": self.map,
                "tickrate": self.tickrate,
                "playerId": playerId
            }))

            while True:
                data = await player["socket"].recv()
                
                action = json.loads(data)

                # Check for speedhacks
                if time() - player["recvTime"] > (1/(self.tickrate + self.config["ticksForgiven"])):
                    player["recvTime"] = time()
                    if not player["dead"]:

                        if "m" in action:
                            player["facing"] = action["m"]
                            self.movePlayer(playerId, action["m"])

                        if "s" in action:
                            self.shoot(playerId)

                        if "a" in action:
                            self.action(playerId)

                else:
                    print(f"[?] Throttled {playerId}")
                
        except Exception as e:
            if self.logging: print(e)
            print(f"[-] Dead connection for {playerId}")
            self.deadConnections.append(playerId)
    
    def revivePlayers(self):
        for playerId in self.players:
            player = self.players[playerId]

            if player["dead"]:
                player["position"] = self.getSpawnPosition()
                player["dead"] = False


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
            if self.players[playerId]["floor"] == floor:
                playerPositions.append(self.players[playerId]["position"])

        # Check if geyser is in title
        geyserPositions = []
        for geyserId in self.geysers:
            if self.geysers[geyserId]["floor"] == floor:
                geyserPositions.append(self.geysers[geyserId]["position"])

        if pos in playerPositions:
            return PLAYER_CHAR

        if pos in geyserPositions:
            return GEYSIR_CHAR

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
        
        pos = self.getNextPos(player["position"], player["facing"])

        if self.mapDimensions[0] - 1 >= pos[0] >= 0 and self.mapDimensions[1] - 1 >= pos[1] >= 0:
            title = self.getTitle(pos, player["floor"])

            if title == LADDER_CHAR:
                player["floor"] = 0 if player["floor"] == 1 else 1

            if not title in [PLAYER_CHAR, BOULDER_CHAR, WALL_CHAR, GEYSIR_CHAR]:
                player["position"] = pos

    def shoot(self, playerId):
        index = self.bulletsIndex
        player = self.players[playerId]

        now = time()
        if now - player["shootTime"] < self.config["shootDelay"]:
            return

        player["shootTime"] = now

        self.bulletsIndex += 1
        if self.bulletsIndex > 65535:
            self.bulletsIndex = 0

        pos = self.getNextPos(player["position"], player["facing"])

        for playerKey in self.players:
            if self.players[playerKey]["position"] == pos and player["floor"] == self.players[playerKey]["floor"]:
                self.kill(playerKey, playerId)
                return

        if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
            return
        elif self.getTitle(pos, player["floor"]) in [BOULDER_CHAR, WALL_CHAR]:
            return

        self.bullets[index] = {
            "owner": playerId,
            "position": pos,
            "floor": player["floor"],
            "direction": player["facing"]
        }

    def updateBullets(self):
        toRemove = []
        for bulletKey in self.bullets:
            bullet = self.bullets[bulletKey]
            pos = self.getNextPos(bullet["position"], bullet["direction"])

            # Check if bullet is in playarea
            if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
                toRemove.append(bulletKey)

            # Check for collisions
            elif self.getTitle(pos, bullet["floor"]) in [BOULDER_CHAR, WALL_CHAR]:
                toRemove.append(bulletKey)

            # Check for kills
            else:
                for playerKey in self.players:
                    if self.players[playerKey]["position"] == pos and bullet["floor"] == self.players[playerKey]["floor"]:
                        toRemove.append(bulletKey)
                        self.kill(playerKey, bullet["owner"])

            bullet["position"] = pos

        # Garbage collect bullets
        for bulletKey in toRemove:
            try:
                self.bullets.pop(bulletKey)
            except:
                pass

    def kill(self, playerId, ownerId):
        player = self.players[playerId]
        owner = self.players[ownerId]

        if player["health"] < 2:
            player["dead"] = True
            player["position"] = (None, None)
            player["floor"] = 1
        else: player["health"] -= 1

        owner["score"] += 100

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
        player["bouldersPicked"] += 1
        self.map[player["floor"]][pos[1]][pos[0]] = EMPTY_CHAR
        self.titlesToUpdate.append((pos[0], pos[1], player["floor"]))

    def place(self, player, pos):
        player["bouldersPicked"] -= 1
        self.map[player["floor"]][pos[1]][pos[0]] = BOULDER_CHAR
        self.titlesToUpdate.append((pos[0], pos[1], player["floor"]))

    def mineWall(self, player, pos):
        now = time()
        if now - player["mineTime"] < self.config["mineDelay"]:
            return

        player["mineTime"] = now

        if randrange(0, self.config["geyserChange"]) == 0: # 1/15 Change of finding a geyser
            self.map[player["floor"]][pos[1]][pos[0]] = EMPTY_CHAR

            geyserId = self.geysersIndex
            self.geysersIndex += 1

            self.geysers[geyserId] = {
                "lastCollected": time(),
                "deathTime": time() + 10 * self.config["minute"],
                "position": pos,
                "floor": player["floor"]
            }

        else: # Just break the wall
            self.map[player["floor"]][pos[1]][pos[0]] = BOULDER_CHAR
            self.titlesToUpdate.append((pos[0], pos[1], player["floor"]))
        

    def action(self, playerId):
        player = self.players[playerId]
        pos = self.getNextPos(player["position"], player["facing"])
        title = self.getTitle(pos, player["floor"])

        if title == False:
            return

        if title == EMPTY_CHAR and player["bouldersPicked"] > 0:
            self.place(player, pos)
        elif title == BOULDER_CHAR and player["bouldersPicked"] < 2:
            self.pick(player, pos)
        elif title == WALL_CHAR:
            self.mineWall(player, pos)
        elif title == GEYSIR_CHAR:
            for geyserId in self.geysers:
                if self.geysers[geyserId]["position"] == pos:
                    self.collectGeysir(playerId, geyserId)
                    break

    def collectGeysir(self, playerId, geyserId):
        geyser = self.geysers[geyserId]
        now = time()
        diff = round(now - geyser["lastCollected"])
        gain = diff if diff <= self.config["minute"] * 8 else self.config["minute"] * 6

        self.players[playerId]["money"] += gain
        self.players[playerId]["score"] += gain

        if geyser["deathTime"] < now:
            print("Removing a geyser")
            self.geysers.pop(geyserId)

        print(f"Gain: {gain}")

        geyser["lastCollected"] = now
