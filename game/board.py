import random


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


class Tile:
    def __init__(self, owner, type):
        self.owner = owner
        self.type = type
        self.troops = 0
        if type == KING:
            self.troops = 1 # Kings start with 1 troop
        if type == CITY:
            self.troops = 20 # Troops needed to capture city


class Move:
    def __init__(self, player, direction, r, c):
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
    def __init__(self, M, N, players):
        # Randomly place kings on the board
        kings = []
        for _ in range(players):
            x = random.randint(0, M * N - 1)
            r, c = (x // N), (x % N)
            while (r, c) in kings:
                x = random.randint(0, M * N - 1)
                r, c = (x // N), (x % N)
            kings.append((r, c))

        self.M = M # Number of rows
        self.N = N # Number of columns
        self.players = players # Number of players
        self.kings = kings # King locations
        self.conquered_cities = kings # Cities already conquered
        self.conquered_land = kings # Land already conquered
        self.board = [] # The board itself

        k = 1
        for r in range(M):
            next_row = []
            for c in range(N):
                rand = random.uniform(0, 1)
                if (r, c) in self.kings:
                    next_row.append(Tile(k, KING))
                    k += 1
                elif rand < 0.05:
                    next_row.append(Tile(None, CITY))
                    self.conquered_cities.append((r, c))
                elif 0.05 <= rand < 0.20:
                    next_row.append(Tile(None, MOUNTAIN))
                else:
                    next_row.append(Tile(None, NEUTRAL))
            self.board.append(next_row)


    # Increment the troops of all cities
    def increment_city_troops(self):
        for city in self.conquered_cities:
            r, c = city
            self.board[r][c].troops += 1
    

    # Increment the troops of all land
    def increment_all_troops(self):
        for land in self.conquered_land:
            r, c = land
            self.board[r][c].troops += 1


    # Frontend will check if the move is "technically" valid
    # i.e. within the board, not a mountain, only selecting your own troops
    # check_valid_move checks if a move is valid at the time of execution
    def check_valid_move(self, move):
        r, c = move.tile
        # Check if tile belongs to an opponent
        if self.board[r][c].owner != move.player:
            return False
        # Check if tile has at least two troops
        if self.board[r][c].troops <= 1:
            return False
        return True


    # Move a player in a direction
    def move(self, move):
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
            # City
            elif self.board[r][c].type == CITY:
                if troops_to_move > self.board[r][c].troops:
                    self.board[r][c].owner = move.player
                    self.board[r][c].troops = troops_to_move - self.board[r][c].troops
                    gained_land = True
                    self.conquered_cities.append((r, c))
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
