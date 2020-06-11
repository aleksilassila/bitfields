import asyncio
import websockets
from time import sleep, time

from config import Config
from src.game import Game
from src.player import Player

playerId = 0

async def handleClient(ws, path):
	global playerId
	thisPlayerId = playerId

	game.players[thisPlayerId] = Player(thisPlayerId, ws, game.getSpawnPosition(), Config.defaultName)

	playerId += 1
	print(f"[+] Connection from {ws.remote_address}")
	print(f"[+] Assigned player id {thisPlayerId}")

	try:
		asyncio.create_task(await game.managePlayer(thisPlayerId))

	except Exception as e:
		print(f"[-] Dead connection for {thisPlayerId}")
		if Config.logging: print(f"Error: {e}")
		game.isDeadConnections = True
		game.deadConnections.append(thisPlayerId)

game = Game()

address = Config.serverAddress if Config.serverAddress != None else "0.0.0.0"
ip = int(Config.serverIp) if Config.serverIp != None else 8765

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
	websockets.serve(handleClient, address, ip),
	game.start()
))
loop.run_forever()
