from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pydantic import BaseModel
from game.board import Board, Move
from game.game import Game
from typing import List, Dict, Tuple


game = Game(1)
app = FastAPI()

class GetReply(BaseModel):
    board: List[List[Tuple[int, str, int]]] # 2D list of (owner, type, troops)

class PostArgs(BaseModel):
    moves: List[Tuple[int, int, int, int]]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(request.headers)
    print(await request.body())
    response = await call_next(request)
    return response

@app.get("/")
async def read_root():
    return {"Hello": "World"}

def serialize_board(board, playerid):

    b = board.board
    M, N = len(b), len(b[0])
    ret = []
    for r in range(M):
        next_row = []
        for c in range(N):
            tile = b[r][c]
            owner = tile.owner or 0
            type = tile.type
            troops = tile.troops or 0
            next_row.append((owner, type, troops))
        ret.append(next_row)
    return ret

@app.get("/board/")
async def get_boardstate(playerid: int):
    serialized_board = serialize_board(game.board, playerid)
    return GetReply(board=serialized_board)

@app.post("/move/")
async def update_item(args: PostArgs):
    moves = []
    #     directions = {
    #         "up": (-1, 0): 
    #         "down": (1, 0),
    #         "left": (0, -1),
    #         "right": (0, 1)
    #     }
    # for r1, c1, r2, c2 in args.moves:

    #     game.p1.moves.append(Move(1, ))
    # game.p1.moves.extend(m)
