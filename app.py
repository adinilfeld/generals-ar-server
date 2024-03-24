from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from game.game import Game
from game.board import NEUTRAL, Move, Board
from typing import List, Tuple
from threading import Thread


DIRECTIONS = {
    (-1, 0): "up",
    (1, 0): "down",
    (0, -1): "left",
    (0, 1): "right"
}


game = Game(1)
gamethread = Thread(target = game.update)
gamethread.start()
app = FastAPI()


class GetReply(BaseModel):
    # board: List[List[Tuple[int, str, int, bool]]] # 2D list of (owner, type, troops, visible)
    board: List[List[Tuple[int, str, int]]]
    land: int # Number of tiles owned by player
    army: int # Number of troops owned by player

class GetReplyFlat(BaseModel):
    # board: List[List[Tuple[int, str, int, bool]]] # 2D list of (owner, type, troops, visible)
    board: List[int|str]
    land: int # Number of tiles owned by player
    army: int # Number of troops owned by player

class PostArgs(BaseModel):
    moves: List[Tuple[int, int, int, int]] # List of (r1, c1, r2, c2)
    playerid: int


@app.middleware("http")
async def log_requests(request:Request, call_next:callable) -> None:
    # print(request.headers)
    # print(await request.body())
    response = await call_next(request)
    return response


@app.get("/")
async def read_root() -> dict:
    return {"Hello": "World"}


def serialize_board(board:Board, playerid:int) -> List[List[Tuple[int, str, int]]]:
    b = board.board
    print(game.playerids)
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
            # visible = True
            if not visible:
                owner = -1
                # if type == NEUTRAL: 
                troops = 0
            next_row.append((owner, type, troops))
        ret.append(next_row)
    return ret

def flatten(board: List[List[Tuple[int, str, int]]]) -> List[int|str|int]:
    out = []
    for row in board:
        for square in row:
            out.append(square[0])
            out.append(square[1])
            out.append(square[2])

    return out

@app.get("/board/")
async def get_boardstate(playerid:int):
    # Assign playerid to player 1 or 2 at beginning of game
    if playerid not in game.playerids:
        if len(game.playerids) == 0:
            game.playerids[playerid] = game.p1
        elif len(game.playerids) == 1:
            game.playerids[playerid] = game.p2
        else:
            raise HTTPException(status_code=400, detail="Game is full")
    # Serialize the board state for the player
    # serialized_board = serialize_board(game.board, playerid)
    # reply = GetReply(board=serialized_board,
    #                  land=game.playerids[playerid].land,
    #                  army=game.playerids[playerid].army)
    print("HTTP SERVER NUM TROOPS", game.p1.army)
    serialized_board = flatten(serialize_board(game.board, playerid))
    reply = GetReplyFlat(board=serialized_board,
                     land=game.playerids[playerid].land,
                     army=game.playerids[playerid].army)
    return reply


@app.post("/move/")
async def add_moves(args:PostArgs):
    print("HERE HERE HERE")
    print("HERE HERE HERE")
    print("HERE HERE HERE")
    moves = []
    player = game.playerids[args.playerid].player
    for r1, c1, r2, c2 in args.moves:
        print("MOVE COORDS", (r1,c1,r2,c2))
        dr = -(r2 - r1)
        dc = -(c2 - c1)
        direction = DIRECTIONS[(dr, dc)]
        moves.append(Move(player, direction, r2, c2))
    if player == 1:
        print("ADDING MOVES")
        game.p1.moves.extend(moves)
    else:
        print("ADDING MOVES")
        game.p2.moves.extend(moves)
