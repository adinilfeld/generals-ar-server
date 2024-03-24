import random
from typing import Tuple


KING = "♛"
CITY = "⌂"
NEUTRAL = "-"
MOUNTAIN = "⛰"
DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}
ADJACENT = [(-1,-1), (-1,0), (-1,1), 
            (0, -1), (0, 0), (0, 1), 
            (1, -1), (1, 0), (1, 1)]


class Tile:
    def __init__(self, owner:int, type:str):
        self.owner = owner
        self.type = type
        self.p1_visible = False
        self.p2_visible = False
        self.troops = 0
        if type == KING:
            self.troops = 1 # Kings start with 1 troop
        if type == CITY:
            self.troops = random.randint(20, 30) # Troops needed to capture city


class Move:
    def __init__(self, player:int, direction:str, r:int, c:int):
        self.player = player
        self.tile = (r, c)
        self.direction = direction


class MoveResult:
    def __init__(self):
        self.valid = False
        self.gained_land = False
        self.won = False


class Board:
    # Initialize the board with M rows and N columns
    def __init__(self, M:int, N:int):
        # Randomly place kings on the board
        kings = []
        for _ in range(2):
            x = random.randint(0, M * N - 1)
            r, c = (x // N), (x % N)
            while (r, c) in kings:
                x = random.randint(0, M * N - 1)
                r, c = (x // N), (x % N)
            kings.append((r, c))

        self.M = M # Number of rows
        self.N = N # Number of columns
        self.kings = kings # King locations
        self.conquered_land = [] # Land (excluding cities) conquered by players
        self.conquered_cities = kings # Cities conquered by players
        self.board = [] # The board itself

        player = 1
        for r in range(M):
            next_row = []
            for c in range(N):
                rand = random.uniform(0, 1)
                if (r, c) in self.kings:
                    next_row.append(Tile(player, KING))
                    player += 1
                elif rand < 0.05:
                    next_row.append(Tile(None, CITY))
                elif 0.05 <= rand < 0.20:
                    next_row.append(Tile(None, MOUNTAIN))
                else:
                    next_row.append(Tile(None, NEUTRAL))
            self.board.append(next_row)
        
        for r, c in kings:
            self.make_visible(self.board[r][c].owner, r, c)


    # Make all adjacent tiles visible
    def make_visible(self, player:int, r:int, c:int):
        self.print()
        # loop through all 8 directions
        for dr, dc in ADJACENT:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.M and 0 <= nc < self.N:
                if player == 1:
                    self.board[nr][nc].p1_visible = True
                else:
                    self.board[nr][nc].p2_visible = True


    # Check if an adjacent tile is occupied by the player
    def adjacent_occupied(self, player:int, r:int, c:int) -> bool:
        for dr, dc in ADJACENT:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.M and 0 <= nc < self.N:
                if self.board[nr][nc].owner == player:
                    return True
        return False
    

    # Make tiles invisible when losing a tile
    def make_invisible(self, player:int, r:int, c:int):
        for dr, dc in ADJACENT:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.M and 0 <= nc < self.N:
                if player == 1 and not self.adjacent_occupied(1, nr, nc):
                    self.board[nr][nc].p1_visible = False
                elif player == 2 and not self.adjacent_occupied(2, nr, nc):
                    self.board[nr][nc].p2_visible = False


    # Increment the troops of all cities
    def increment_troops(self, all:bool=False) -> Tuple[int, int]:
        p1_increment = 0
        p2_increment = 0
        conquered = self.conquered_cities
        if all:
            conquered += self.conquered_land
        for city in conquered:
            r, c = city
            self.board[r][c].troops += 1
            if self.board[r][c].owner == 1:
                p1_increment += 1
            else:
                p2_increment += 1
        return p1_increment, p2_increment


    # Frontend will check if the move is "technically" valid
    # i.e. within the board, not a mountain, only selecting your own troops
    # check_valid_move checks if a move is valid at the time of execution
    def check_valid_move(self, move:Move) -> bool:
        r, c = move.tile
        # Check if tile belongs to an opponent
        if self.board[r][c].owner != move.player:
            return False
        # Check if tile has at least two troops
        if self.board[r][c].troops <= 1:
            return False
        return True


    # Move a player in a direction
    def move(self, move:Move):
        r, c = move.tile
        result = MoveResult()
        if not self.check_valid_move(move):
            return result

        # Leave one troop behind
        troops_to_move = self.board[r][c].troops - 1
        self.board[r][c].troops = 1 

        # Move the troops
        dr, dc = DIRECTIONS[move.direction]
        r += dr
        c += dc

        # Mountain
        if self.board[r][c].type == MOUNTAIN:
            return result
        
        # Keep track of move status
        valid = True
        gained_land = False
        won = False

        # If already occupied by yourself
        if self.board[r][c].owner == move.player:
            self.board[r][c].troops += troops_to_move

        # If occupied by an opponent
        elif self.board[r][c].owner is not None:
            # Opponent has more troops
            if self.board[r][c].troops > troops_to_move:
                self.board[r][c].troops -= troops_to_move
            # Opponent has less troops
            elif self.board[r][c].troops < troops_to_move:
                self.board[r][c].owner = move.player
                self.board[r][c].troops = troops_to_move - self.board[r][c].troops
                self.make_visible(move.player, r, c)
                self.make_invisible(3 - move.player, r, c)
                gained_land = True
            # Equal troops, nothing happends
            else:
                valid = False
            # If captured opponent king, game over
            if gained_land and self.board[r][c].type == KING:
                won = True
            
        # If unoccupied
        else:
            # Neutral land
            if self.board[r][c].type == NEUTRAL:
                self.board[r][c].owner = move.player
                self.board[r][c].troops = troops_to_move
                gained_land = True
                self.conquered_land.append((r, c))
                self.make_visible(move.player, r, c)

            # City
            elif self.board[r][c].type == CITY:
                if troops_to_move > self.board[r][c].troops:
                    self.board[r][c].owner = move.player
                    self.board[r][c].troops = troops_to_move - self.board[r][c].troops
                    gained_land = True
                    self.conquered_cities.append((r, c))
                    self.make_visible(move.player, r, c)
                else: 
                    self.board[r][c].troops -= troops_to_move
                    valid = False

        # Return move result
        result.valid = valid
        result.gained_land = gained_land
        result.won = won
        return result
        
    
    # Prints the board
    def print(self):
        for r in range(self.M):
            for c in range(self.N):
                if self.board[r][c].type == NEUTRAL and self.board[r][c].owner is not None:
                    print(self.board[r][c].owner, end=" ")
                print(self.board[r][c].type, end=" ")
            print("\n")
