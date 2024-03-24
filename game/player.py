from collections import deque

class Player: 

    def __init__(self, player:int):
        self.player = player
        self.land = 1
        self.army = 1
        self.moves = deque()
        