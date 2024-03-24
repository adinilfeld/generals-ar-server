from fastapi import FastAPI, Request
from pydantic import BaseModel
from game.game import Game
from game.board import Move, Board, DIRECTIONS
from game.player import Player
from typing import List, Tuple


game = Game(1)
app = FastAPI()


class GetReply(BaseModel):
    board: List[List[Tuple[int, str, int, bool]]] # 2D list of (owner, type, troops, visible)
    land: int # Number of tiles owned by player
    army: int # Number of troops owned by player


class PostArgs(BaseModel):
    moves: List[Tuple[int, int, int, int]] # List of (r1, c1, r2, c2)
    playerid: int


@app.middleware("http")
async def log_requests(request:Request, call_next:callable) -> None:
    print(request.headers)
    print(await request.body())
    response = await call_next(request)
    return response


@app.get("/")
async def read_root() -> dict:
    return {"Hello": "World"}


def serialize_board(board:Board, playerid:int) -> List[List[Tuple[int, str, int, bool]]]:
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
async def get_boardstate(playerid:int):
    # Assign playerid to player 1 or 2 at beginning of game
    if playerid not in game.playerids:
        if len(game.playerids) == 0:
            game.playerids[playerid] = game.p1
        elif len(game.playerids) == 1:
            game.playerids[playerid] = game.p2
    # Serialize the board state for the player
    serialized_board = serialize_board(game.board, playerid)
    reply = GetReply(board=serialized_board,
                     land=game.playerids[playerid].land,
                     army=game.playerids[playerid].army)
    return reply


@app.post("/move/")
async def add_moves(args:PostArgs):
    pass
    # moves = []
    # for r1, c1, r2, c2 in args.moves:

    #     game.p1.moves.append(Move(1, ))
    # game.p1.moves.extend(m)
