import asyncio
import websockets
from time import sleep, time

from src.game import Game

playerId = 0

async def handleClient(ws, path):
	global playerId
	thisPlayerId = playerId

	now = time()

	game.players[thisPlayerId] = {
		"socket": ws,
		"position": game.getSpawnPosition(),
		"facing": 0,
		"floor": 1,
		"dead": False,
		"score": 0,
		"money": 0,
		"health": 1,
		"bouldersPicked": 0,
		"name": game.config["defaultName"],
		"recvTime": now,
		"shootTime": now,
		"mineTime": now
	}
	playerId += 1
	print(f"[+] Added player {thisPlayerId}")

	try:
		asyncio.create_task(await game.managePlayer(thisPlayerId))

	except Exception as e:
		print(f"[-] Dead connection for {thisPlayerId}")
		game.isDeadConnections = True
		game.deadConnections.append(thisPlayerId)

game = Game({
	"logging": True,
	"tickrate": 15,
	"ticksForgiven": 5,
	"minute": 60, # Make 30 to make game run 2x faster
	"shootDelay": 0.2, # Seconds
	"mineDelay": 2, # Seconds
	"geyserChange": 15, # 1/15 change
	"defaultName": "An unnamed bit",
	"nameMaxLen": 20
})

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
	websockets.serve(handleClient, "0.0.0.0", 8765),
	game.start()
))
loop.run_forever()
