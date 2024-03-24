from fastapi import FastAPI, Request
from pydantic import BaseModel
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
    player = game.playerids[playerid]
    M, N = len(b), len(b[0])
    ret = []
    for r in range(M):
        next_row = []
        for c in range(N):
            tile = b[r][c]
            owner = tile.owner or 0
            type = tile.type
            troops = tile.troops or 0
            visible = tile.p1_visible if player.player == 1 else tile.p2_visible
            next_row.append((owner, type, troops, visible))
        ret.append(next_row)
    return ret


@app.get("/board/")
async def get_boardstate(playerid: int):
    serialized_board = serialize_board(game.board, playerid)
    # Assign playerid to player 1 or 2 at beginning of game
    if playerid not in game.playerids:
        if len(game.playerids) == 0:
            game.playerids[playerid] = game.p1
        elif len(game.playerids) == 1:
            game.playerids[playerid] = game.p2
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
