from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('iotest.html')

def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)  # Use socketio.sleep, not time.sleep!
        count += 1
        socketio.emit('message', 'heartbeat', namespace='/')
        print("Message sent from the server.")

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    send(message)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('after connect',  {'data':'Lets dance'})
    socketio.start_background_task(background_task)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
