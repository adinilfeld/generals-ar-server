from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
# from game import Game

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, world!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

# game = Game(10, 10, 2)

# @app.post("/execute_move/", response_model=Move, status_code=201)
# def execute_move(move: Move):
#     global game


