import zmq, multiprocessing, threading, time, random, json, uuid
from util import parse_arguments, process_task


def run(url):
    # Run function to be ran in the multiprocessing pool
    worker_id = str(uuid.uuid4())
    print(f'Worker started: {worker_id}.')
    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt_string(zmq.IDENTITY, worker_id)
    socket.connect(url)

    # Register worker
    socket.send_json({'status':'REGISTER'})

    # Helper function to send heartbeat, run on a separate thread
    def send_heartbeat():
        while True:
            time.sleep(random.randint(10, 15))
            socket.send_json({'status':'HEARTBEAT'})
    threading.Thread(target=send_heartbeat).start()

    # Get tasks from dispatcher and process them
    while True:
        try:
            response= json.loads(socket.recv_multipart()[0].decode())
            if response['status'] == 'TASK':
                outcome = process_task(response)
                socket.send_json(outcome)
            elif response['status'] == 'HEARTBEAT_BACK':
                pass
            elif response['status'] == 'REGISTERED':
                pass
        except Exception as e:
            print(f'Error: {e}')
            socket.close()
            context.term()
            break


if __name__ == '__main__':
    args = parse_arguments('Push Worker')
    pool = multiprocessing.Pool(args.num_workers)
    pool.starmap_async(run,[(args.url,) for _ in range(args.num_workers)])
    pool.close()
    pool.join()
    print('All push workers exiting...')