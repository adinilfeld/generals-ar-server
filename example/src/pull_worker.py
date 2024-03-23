import zmq, multiprocessing, threading, time, random, uuid
from util import parse_arguments, process_task


# Define a global multiprocessing lock for the socket
global socklock
global url
socklock = multiprocessing.Lock()


def get_task_from_dispatcher(socket,worker_id):
    # Indicate that worker is ready and get a task from dispatcher
    with socklock:
        socket.send_json({'status':'WORKER_READY', 'worker_id':worker_id})
        task = socket.recv_json()
        if task['status'] == 'TASK':
            return task
        elif task['status'] == 'NO_TASK':
            return None
        else:
            raise('Invalid status received from dispatcher.')


def send_to_dispatcher(socket, outcome):
    # Send task outcome to dispatcher
    with socklock:
        socket.send_json(outcome)
        response = socket.recv_json()
        assert response['status'] == 'LOGGED'


def run(url):
    # Run function to be ran in the multiprocessing pool
    worker_id = str(uuid.uuid4())
    print(f'Worker started: {worker_id}.')
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(url)

    # Register worker
    with socklock:
        socket.send_json({'status':'REGISTER', 'worker_id':worker_id})
        socket.recv_json()

    # Helper function to send heartbeat, run on a separate thread
    def send_heartbeat():
        while True:
            time.sleep(random.randint(10, 15))
            with socklock:
                socket.send_json({'status':'HEARTBEAT', 'worker_id':worker_id})
                response = socket.recv_json()
                assert response['status'] == 'HEARTBEAT_BACK'
    threading.Thread(target=send_heartbeat).start()

    # Get tasks from dispatcher and process them
    while True:
        try:
            task = get_task_from_dispatcher(socket,worker_id)
            if task:
                outcome = process_task(task)
                outcome['worker_id'] = worker_id
                send_to_dispatcher(socket, outcome)
        except Exception as e:
            print(f'Exiting with error: {e}')
            socket.close()
            context.term()
            break


if __name__ == '__main__':
    args = parse_arguments('Pull Worker')
    pool = multiprocessing.Pool(args.num_workers)
    pool.starmap_async(run,[(args.url,) for _ in range(args.num_workers)])
    pool.close()
    pool.join()
    print('All pull workers exiting...')