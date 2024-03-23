import time
from collections import deque
from board import Board

M = 10
N = 10
players = 2

class Game:

    def __init__(self, timestep):
        self.timestep = timestep

        self.houses = 0
        self.soldiers = 0
        self.q1 = deque()
        self.q2 = deque()

        self.board = Board(M, N, players)

    
    def start(self):
        return
    
    # every timestep second, pop the q1 and q2 and update the board
    def update(self):
        while True:
            if len(self.q1) > 0:
                move = self.q1.popleft()
                self.board.move(move)
            if len(self.q2) > 0:
                move = self.q2.popleft()
                self.board.move(move)
            time.sleep(self.timestep)


if __name__ == "__main__":
    game = Game()
    game.start()