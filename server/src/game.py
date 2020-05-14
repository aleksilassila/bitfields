import asyncio
import json
from random import randrange
from src.generator import Generator

PLAYER_CHAR = "@"
WALL_CHAR = "#"
BOULDER_CHAR = "O"
GRASS_CHAR = "."
GRASS_ALT_CHAR = "_"
LADDER_CHAR = "H"
BUSH_CHAR = "M"
EMPTY_CHAR = " "

class Game:
    def __init__(self):
        self.tickrate = 15 # 15 ticks per second
        self.players = {}
        self.bullets = {}
        self.bulletsIndex = 0
        """ players =
        playerId: {
            socket: websocket,
            position: (x, y),
            facing: 0,1,2,3,
            floor: 0,1,
            dead: False
        }
        """
        self.deadConnections = []
        self.isDeadConnections = False
        self.mapDimensions = (400, 200)
        gen = Generator(self.mapDimensions[0], self.mapDimensions[1], -200)

        self.map = [gen.getUnderworld(), gen.getOverworld()]
        self.bouldersMap = gen.getBoulders()

        # Create initial boulders
        for floor in [0, 1]:
            for boulder in self.bouldersMap[floor]:
                boulderx = boulder[0]
                bouldery = boulder[1]
                self.map[floor][bouldery][boulderx] = BOULDER_CHAR


    ## NETWORKING AND GAME
    async def start(self):
        while True:
            self.updateBullets()
            await self.updatePlayers()
            await asyncio.sleep(1/self.tickrate)

            if self.isDeadConnections:
                self.removeDeadConnections()
            self.updateBullets()
            await self.updatePlayers()
            await asyncio.sleep(1/self.tickrate)

    async def updatePlayers(self):
        players = {}
        bullets = {}

        for playerId in self.players:
            players[playerId] = {
                "p": self.players[playerId]["position"],
                "f": self.players[playerId]["floor"],
            }

        for bulletKey in self.bullets:
            bullets[bulletKey] = {
                "p": self.bullets[bulletKey]["position"],
                "f": self.bullets[bulletKey]["floor"]
            }

        for playerId in self.players:
            try:
                await self.players[playerId]["socket"].send(json.dumps({
                    "p": players, # Player positions
                    "i": playerId, # Self playerid
                    "f": self.players[playerId]["floor"], # Floor
                    "b": bullets # Bullets
                }))
            
            except Exception as e:
                print(f"[-] Dead connection for {playerId}")
                self.isDeadConnections = True
                self.deadConnections.append(playerId)

    def removeDeadConnections(self):
        for playerId in self.deadConnections:
            try:
                self.players.pop(playerId)
                print(f"[-] Removed player {playerId}")
            except:
                pass
        
        self.deadConnections = []
        self.isDeadConnections = False

    async def managePlayer(self, playerId):
        await self.players[playerId]["socket"].send(json.dumps({
            "map": self.map
        }))

        while True:
            try:
                data = await self.players[playerId]["socket"].recv()
                action = json.loads(data)

                if not self.players[playerId]["dead"]:

                    if "m" in action:
                        self.players[playerId]["facing"] = action["m"]
                        self.movePlayer(playerId, action["m"])

                    if "s" in action:
                        self.shoot(playerId)
                
            except Exception as e:
                print(f"[-] Dead connection for {playerId}")
                print(e)
                self.isDeadConnections = True
                self.deadConnections.append(playerId)
                break
    

    ## GAME LOGIC
    def getTitle(self, x, y, floor=1):
        char = self.map[floor][y][x]
        if char in [WALL_CHAR, BOULDER_CHAR]:
            return char

        # Check if other player is in title
        playerPositions = []
        for playerId in self.players:
            if self.players[playerId]["floor"] == floor:
                playerPositions.append(self.players[playerId]["position"])

        if (x, y) in playerPositions:
            return PLAYER_CHAR

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
            if self.getTitle(pos[0], pos[1], 1) not in [PLAYER_CHAR, BOULDER_CHAR, WALL_CHAR]:
                return pos

    def movePlayer(self, playerId, direction):
        player = self.players[playerId]
        
        pos = self.getNextPos(player["position"], player["facing"])

        if self.mapDimensions[0] - 1 >= pos[0] >= 0 and self.mapDimensions[1] - 1 >= pos[1] >= 0:
            title = self.getTitle(pos[0], pos[1], player["floor"])

            if title == LADDER_CHAR:
                player["floor"] = 0 if player["floor"] == 1 else 1

            if not title in [PLAYER_CHAR, BOULDER_CHAR, WALL_CHAR]:
                player["position"] = pos

    def shoot(self, playerId):
        index = self.bulletsIndex
        player = self.players[playerId]

        self.bulletsIndex += 1
        if self.bulletsIndex > 65535:
            self.bulletsIndex = 0

        pos = self.getNextPos(player["position"], player["facing"])

        for playerKey in self.players:
            if self.players[playerKey]["position"] == pos and player["floor"] == self.players[playerKey]["floor"]:
                self.kill(playerKey)
                return

        if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
            return
        elif self.getTitle(pos[0], pos[1], player["floor"]) in [BOULDER_CHAR, WALL_CHAR]:
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

            if self.mapDimensions[0] - 1 < pos[0] or pos[0] < 0 or self.mapDimensions[1] - 1 < pos[1] or pos[1] < 0:
                toRemove.append(bulletKey)

            elif self.getTitle(pos[0], pos[1], bullet["floor"]) in [BOULDER_CHAR, WALL_CHAR]:
                toRemove.append(bulletKey)

            else:
                for playerKey in self.players:
                    if self.players[playerKey]["position"] == pos and bullet["floor"] == self.players[playerKey]["floor"]:
                        toRemove.append(bulletKey)
                        self.kill(playerKey)

            bullet["position"] = pos

        # Garbage collect bullets
        for bulletKey in toRemove:
            self.bullets.pop(bulletKey)

    def kill(self, playerId):
        player = self.players[playerId]
        player["dead"] = True
        player["position"] = (None, None)
        player["floor"] = 1