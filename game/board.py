import random

KING = "KING"
HOUSE = "HOUSE"
NEUTRAL = "NEUTRAL"


class Tile:

    def __init__(self, type):
        self.owner = None
        self.type = type


class Board:

    def __init__(self, M, N, players):
        kings = []
        for _ in players:
            x = random.randint(0, M*N-1)
            r, c = (x // N), (x % N)
            while (r, c) in kings:
                x = random.randint(0, M*N-1)
                r, c = (x // N), (x % N)
            kings.append((r, c))

        self.kings = [(r, c)]
        self.board = []
        for r in range(M):
            for c in range(N):
                if self.board in self.kings:
                    self.board()
                if random.uniform(0, 1) < 0.1:
                    pass
                    # self.
        self.board = [[Tile() for _ in range(N)] for _ in range(M)]
        abc = KING
