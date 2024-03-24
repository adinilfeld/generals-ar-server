import time, random
from player import Player
from board import Board


class Game:
    def __init__(self, timestep): 
        self.timestep = timestep
        self.p1 = Player(1)
        self.p2 = Player(2)
        self.board = Board(10, 10, 2) # 10x10 board, 2 players
        self.turn = 0
        self.round = 0


    def start(self):
        return
    

    # Every turn, first increment troops
    # Then pop the player moves and update the board
    def update(self):
        while True:
            time.sleep(self.timestep)
            self.turn += 1
            # Every 25 turns, increment the round (all troops)
            if self.turn % 25 == 0:
                self.round += 1
                self.board.increment_all_troops()
            # Otherwise only increment city troops
            else:
                self.board.increment_city_troops()
            
            # Randomize who goes first
            # Ensures fairness if both players want to take an empty tile with the same number of troops
            players = [self.p1, self.p2]
            random.shuffle(players)
            for player in players:
                if len(player.moves) > 0:
                    move = player.moves.popleft()
                    result = self.board.move(move)
                    if not result.valid:
                        player.moves.clear()
                    if result.gained_land:
                        player.land += 1
                        print(f"{player.id} gained land! Land count: {player.land}")
                    if result.won:
                        print(f"Player {player.id} won!")
                        return


if __name__ == "__main__":
    game = Game()
    game.start()
