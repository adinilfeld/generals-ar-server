import time, random
from .player import Player
from .board import Board


class Game:
    def __init__(self, timestep:int): 
        self.timestep = timestep
        self.p1 = Player(1)
        self.p2 = Player(2)
        self.playerids = {}
        self.board = Board(10, 10) # 10x10 board
        self.turn = 0
        self.round = 0


    def start(self):
        self.update()
        return
    

    # Every turn, first increment troops
    # Then pop the player moves and update the board
    def update(self):
        print("UPDATE")
        while True:
            time.sleep(self.timestep)
            # Every turn, increment city troops
            # Every 25 turns, increment the round (all troops)
            self.turn += 1
            p1_increment, p2_increment = self.board.increment_troops((self.turn % 25) == 0)
            self.p1.army += p1_increment
            self.p2.army += p2_increment
            
            # Randomize who goes first
            # Ensures fairness if both players want to take an empty tile with the same number of troops
            players = [self.p1, self.p2]
            random.shuffle(players)
            for player in players:
                if len(player.moves) > 0:
                    print("MAKING MOVE")
                    move = player.moves.popleft()
                    print(move)
                    result = self.board.move(move)
                    if not result.valid:
                        print("MOVE INVALID")
                        player.moves.clear()
                    if result.gained_land:
                        print("MOVE GAINED LAND")
                        player.land += 1
                    if result.won:
                        print(f"Player {player.id} won!")
                        return
                else:
                    print("NO MOVE")
            print(f"Turn {self.turn} completed")
            print(f"Player 1: {self.p1.land} land, {self.p1.army} troops")
            print(f"Player 2: {self.p2.land} land, {self.p2.army} troops")


if __name__ == "__main__":
    game = Game(1)
    game.start()
