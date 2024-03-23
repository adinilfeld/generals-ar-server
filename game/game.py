import time
from collections import deque

class Game:

    def __init__(self, timestep):
        self.timestep = timestep

        self.houses = 0
        self.soldiers = 0
        self.q = deque()

        # self.board = Board()

    
    def start(self):
        return


if __name__ == "__main__":
    game = Game()
    game.start()