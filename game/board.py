import random
import pprint

KING = "K"
HOUSE = "H"
NEUTRAL = "-"
MOUNTAIN = "M"


class Tile:

    def __init__(self, owner, type):
        self.owner = owner
        self.type = type


class Board:

    def __init__(self, M, N, players):
        kings = []
        for _ in range(players):
            x = random.randint(0, M*N-1)
            r, c = (x // N), (x % N)
            while (r, c) in kings:
                x = random.randint(0, M*N-1)
                r, c = (x // N), (x % N)
            kings.append((r, c))

        self.M = M
        self.N = N
        self.players = players
        self.kings = kings
        self.board = []
        k = 1
        for r in range(M):
            next_row = []
            for c in range(N):
                rand = random.uniform(0, 1)
                if (r, c) in self.kings:
                    next_row.append(Tile(k, KING))
                    k += 1
                elif rand < 0.05:
                    next_row.append(Tile(None, HOUSE))
                elif 0.05 <= rand < 0.20:
                    next_row.append(Tile(None, MOUNTAIN))
                else:
                    next_row.append(Tile(None, NEUTRAL))
            self.board.append(next_row)
    
    def print(self):
        for r in range(self.M):
            for c in range(self.N):
                print(self.board[r][c].type + " ", end="")
            print("\n")
