class Config:
	chunkSize = 16
	mapDimensions = (chunkSize * 5, chunkSize * 5) # Min 61*39
	clientDimensions = (61, 39)
	defaultName = "An unnamed bit"
	nameMaxLen = 20

	logging = True
	tickrate = 15
	ticksForgiven = 5

	minute = 60 # Make 30 to make game run 2x faster
	shootDelay = 2/(tickrate + 3) # Seconds
	mineDelay = 2 # Seconds
	

	geyserChange = 15 # 1/15 change
	
	class geyser:
		lifespan = 20 # min
		gain = 2 # Per minute
		maxGain = minute * 8

	doorCost = 1000
	doorHealth = 3
	fortifyCost = 300
	fortifyHealth = 3

	botRandomTurnChange = 20
	botSniffRange = 10
	botAmount = (mapDimensions[0] * mapDimensions[1]) / (60**2) # 1 bot per 60^2 area
