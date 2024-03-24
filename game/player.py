from collections import deque

class Player: 

    def __init__(self, id):
        self.id = id
        self.land = 1
        self.troops = 1
        self.moves = deque()
        