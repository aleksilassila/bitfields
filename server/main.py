import asyncio
import websockets
from time import sleep, time

from src.game import Game
from src.config import Config
from src.player import Player

playerId = 0

async def handleClient(ws, path):
	global playerId
	thisPlayerId = playerId

	game.players[thisPlayerId] = Player(thisPlayerId, ws, game.getSpawnPosition(), Config.defaultName, money = 5000)

	playerId += 1
	print(f"[+] Added player {thisPlayerId}")

	try:
		asyncio.create_task(await game.managePlayer(thisPlayerId))

	except Exception as e:
		print(f"[-] Dead connection for {thisPlayerId}")
		game.isDeadConnections = True
		game.deadConnections.append(thisPlayerId)

game = Game()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
	websockets.serve(handleClient, "0.0.0.0", 8765),
	game.start()
))
loop.run_forever()
