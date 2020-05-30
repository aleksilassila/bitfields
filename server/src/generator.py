import noise
from math import sin

class Generator:
    def __init__(self, width=int, height=int, seed=int):
        self.height = height
        self.width = width
        self.overworld = []
        self.underworld = []
        self.offset = seed * sin(seed / width)

        self.tpc = { # Teleport config
            "s": -0.5,
            "sc": 0.02,
            "o": 5,
            "p": 1,
            "c": "H"
        }

    def getOverworld(self):
        self.overworld = self.generateHeights(sensitivity=0.3, scale=0.02, octaves=2, persistence=1)
        grass = self.generateDepths(sensitivity=-0.1, scale=0.02, octaves=2, persistence=1)
        teleports = self.generateDepths(sensitivity=self.tpc["s"], scale=self.tpc["sc"], octaves=self.tpc["o"], persistence=self.tpc["p"], char=self.tpc["c"]) 

        # Merge layers
        for y in range(0, self.height):
            for x in range(0, self.width):
                if teleports[y][x] == "H":
                    self.overworld[y][x] = "H"
                elif grass[y][x] == ".":
                    self.overworld[y][x] = "."

        return self.overworld

    def getUnderworld(self):
        self.underworld = self.generateHeights(sensitivity=-0.2, scale=0.02, octaves=2, persistence=1)
        caves = self.generateHeights(sensitivity=-0.3, octaves=2, scale=0.03)
        grass = self.generateDepths(sensitivity=-0.4, scale=0.02, octaves=2, persistence=1, char="_")
        teleports = self.generateDepths(sensitivity=self.tpc["s"], scale=self.tpc["sc"], octaves=self.tpc["o"], persistence=self.tpc["p"], char=self.tpc["c"]) 

        # Merge layers
        for y in range(0, self.height):
            for x in range(0, self.width):
                if caves[y][x] == " ":
                    self.underworld[y][x] = " "

                if teleports[y][x] == "H":
                    self.underworld[y][x] = "H"
                elif grass[y][x] == "_":
                    self.underworld[y][x] = "_"

        return self.underworld

    def getBoulders(self, octaves=1, persistence=0.5, lacunarity=2.0, sensitivity=0.65, scale=0.05):
        boulders = [[], []] 

        for y in range(0, self.height):
            for x in range(0, self.width):
                if noise.snoise2(x * scale * 3, y * scale * 3, persistence=persistence,lacunarity=lacunarity, octaves=octaves) > sensitivity:
                    if not self.overworld[y][x] in ["#", "H"]:
                        boulders[1].append((x, y))
                    if not self.underworld[y][x] in ["#", "H"]:
                        boulders[0].append((x, y))

        return boulders

    def generateHeights(self, octaves=1, persistence=0.5, lacunarity=2.0, sensitivity=0.3, scale=0.05, char="#"):
        noiseMap = []

        for y in range(0, self.height):
            noiseMap.append([])

            for x in range(0, self.width):
                if noise.snoise2(x * scale + (250000), y * scale + (250000), persistence=persistence,lacunarity=lacunarity, octaves=octaves) > sensitivity:
                    noiseMap[y].append(char)
                else:
                    noiseMap[y].append(" ")

        return noiseMap

    def generateDepths(self, octaves=1, persistence=0.5, lacunarity=2.0, sensitivity=0.3, scale=0.05, char="."):
        noiseMap = []

        for y in range(0, self.height):
            noiseMap.append([])

            for x in range(0, self.width):
                if noise.snoise2(x * scale + (250000), y * scale + (250000), persistence=persistence,lacunarity=lacunarity, octaves=octaves) < sensitivity:
                    noiseMap[y].append(char)
                else:
                    noiseMap[y].append(" ")

        return noiseMap

    # Testing
    def test(self, o=1, p=0.5, l=2.0, s=0.3, sc=0.05):
        noiseMap = []
        
        def printMap(noiseMap):
            for line in range(0, len(noiseMap) - 1):
                print(noiseMap[line])

        for y in range(0, self.height):
            noiseMap.append("")

            for x in range(0, self.width):
                if noise.snoise2(x * sc, y * sc, persistence=p,lacunarity=l, octaves=o) > s:
                    noiseMap[y] += "#"
                else:
                    noiseMap[y] += " "

        printMap(noiseMap)

if __name__ == "__main__":
    g = Generator(180, 50, -300)
    g.test(o=3)
"""
from MapGeneration.generator import Generator

For caves
g.test(s=-0.3, o=2, sc=0.03)
For underworld
g.test(s=0, sc=0.02, o=2, p=1)
For overworld
g.test(s=3, sc=0.02, o=2, p=1)
"""