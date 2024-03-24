from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from game.board import Board
from game.game import Game
from typing import List, Dict, Tuple


game = Game(1)
app = FastAPI()

# Define a Pydantic model for the item
class SBoard(BaseModel):
    board: List[List[Tuple[int, str, int]]] # 2D list of (owner, type, troops)

class SMoves(BaseModel):
    moves: Tuple[int, int, int, int]

@app.get("/")
async def read_root():
    return {"Hello": "World"}


def serialize_board(board):
    b = board.board
    M, N = len(b), len(b[0])
    ret = []
    for r in range(M):
        next_row = []
        for c in range(N):
            tile = b[r][c]
            owner = tile.owner or -1
            type = tile.type
            troops = tile.troops or 0
            next_row.append((owner, type, troops))
        ret.append(next_row)
    return ret


@app.get("/board")
async def get_boardstate():
    serialized_board = serialize_board(game.board)
    return SBoard(board=serialized_board)

@app.post("/move")
async def update_item(moves: SMoves):
    # Make the move
    
    print(moves)
