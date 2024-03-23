import redis, argparse, time, json, multiprocessing, zmq
from queue import Queue, Empty
from threading import Thread
from tests.serialize import serialize, deserialize


# Initialize Redis connection and task queue
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
global tasks_queue
tasks_queue = Queue()
global listener_flag
listener_flag = True

# Store registered workers
global worker_dict
worker_dict = {}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Task Dispatcher')
    parser.add_argument(
        '-m',
        '--mode',
        choices=['local', 'pull', 'push'],
        required=True,
        help='Mode of operation: local, pull, or push'
    )
    parser.add_argument(
        '-p',
        '--port',
        default=7777,
        type=int,
        required=False,
        help='Port number'
    )
    parser.add_argument(
        '-w',
        '--num_workers',
        type=int,
        default=1,
        required=False,
        help='Number of worker processors'
    )
    args = parser.parse_args()
    return args
            

def listen_for_tasks():
    # Listen for tasks from Redis Pubsub
    pubsub = redis_client.pubsub()
    pubsub.subscribe('Tasks')
    while listener_flag:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            task_id = message['data']
            tasks_queue.put(task_id)
            print(f'Received and queued task: {task_id}\n')
        time.sleep(0.001)


def check_heartbeats():
    # Check for worker heartbeats
    while listener_flag:
        for worker_id in worker_dict:
            prev_task,prev_time= worker_dict[worker_id]
            if prev_task == False:
                continue
            # Deregister the worker if it hasn't sent a heartbeat in 60 seconds
            if time.time() - prev_time > 30:
                deregister_worker(worker_id)
        time.sleep(30)


def apply_serialized_function(task_id, function, parameters): 
    # Apply serialized function, get serialized result for local worker
    redis_client.hset(task_id, 'status', 'RUNNING')
    function = deserialize(function)
    parameters = deserialize(parameters)
    args = parameters[0]
    kwargs = parameters[1]
    try:
        result = function(*args,**kwargs)
        print('Task finished succesfully, sending to Redis.\n')
        return {'task_id':task_id, 'result':serialize(result), 'status':'COMPLETED'}
    except Exception as e:
        print(f'Task failed: {e}\n')
        return {'task_id':task_id, 'result':None, 'status':'FAILED'}
    

def send_to_redis(task):
    # Send task result to Redis
    task_id = task['task_id']
    result = task['result']
    status = task['status']
    redis_client.hset(task_id, 'status', status)
    if status == 'COMPLETED':
        redis_client.hset(task_id, 'result', result)
    elif status == 'FAILED':
        print(f'Task ID: {task_id} failed. Requeued.\n')
    else:
        print('Invalid status for task result.\n')


def fetch_task(timeout=1, blocking=False):
    # Fetch task from queue
    print('Attempting to fetch task from queue.\n')
    try:
        if blocking:
            task_id = tasks_queue.get()
        else:
            task_id = tasks_queue.get(timeout=timeout)
        function_id = redis_client.hget(task_id, 'function_id')
        function = redis_client.hget(function_id, 'payload')
        parameters = redis_client.hget(task_id, 'payload')
        return True, task_id, function, parameters
    except Empty:
        print('No tasks in queue.\n')
        return False, None, None, None


def requeue_task(task_id):
    # Requeue task given a task ID
    redis_client.hset(task_id, 'status', 'QUEUED')
    tasks_queue.put(task_id)
    print(f'Requeueing task: {task_id}\n')


def handle_local(num_workers):
    # Handle local workers using a local multiprocessing pool
    pool = multiprocessing.Pool(num_workers)
    while True:
        try:
            _, task_id, function, parameters = fetch_task(blocking=True)
            try:
                pool.apply_async(apply_serialized_function, args=(task_id, function, parameters), callback=send_to_redis)
            except Exception as e:
                requeue_task(task_id)

        except KeyboardInterrupt as e:
            print('Keyboard interrupt, exiting...')
            pool.close()
            pool.join()
            break
        except Exception as e:
            print('Error: ', e)


def register_worker(worker_id):
    # Register worker in worker dictionary
    # Workers are registered as (task_id, time) tuples
    # If task_id is True, then the worker is available
    # If task_id is False, then the worker is unavailable
    # If task_id is a string (the task ID), then the worker is busy
    worker_dict[worker_id] = (True, time.time())
    print(f'Registered worker {worker_id}.\n')


def deregister_worker(worker_id):
    # Deregister worker in worker dictionary (mark as False)
    # Requeue task if worker was busy
    if worker_id in worker_dict:
        prev_task, prev_time = worker_dict[worker_id]
        if isinstance(prev_task, str):
            print(f'Requeued task {prev_task} from worker {worker_id}.\n')
            requeue_task(prev_task)
        worker_dict[worker_id] = (False, prev_time)
        print(f'Deregistered worker {worker_id}.\n')
    else:
        print(f'Worker {worker_id} not deregistered, not in dict.\n')


def update_worker_heartbeat(worker_id):
    # Update worker heartbeat in worker dictionary
    if worker_id in worker_dict:
        prev_task, _ = worker_dict[worker_id]
        worker_dict[worker_id] = (prev_task, time.time())
    else:
        register_worker(worker_id)


def handle_pull(port):
    # Handle pull workers using ZMQ REQ/REP sockets
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    url = f'tcp://127.0.0.1:{port}'
    socket.bind(url)
    print('Done initializing for pull mode.\n')

    # Listen for worker requests
    while True:
        try:
            worker_req = socket.recv_json()

            # Register worker upon worker initialization
            if worker_req['status'] == 'REGISTER':
                register_worker(worker_req['worker_id'])
                socket.send_json({'status':'REGISTERED'})

            # Update worker heartbeat upon worker heartbeat
            elif worker_req['status'] == 'HEARTBEAT':
                update_worker_heartbeat(worker_req['worker_id'])
                socket.send_json({'status':'HEARTBEAT_BACK'})

            # We get a worker requesting work, send task as JSON
            elif worker_req['status'] == 'WORKER_READY':
                got_task, task_id, function, parameters = fetch_task()
                if got_task:
                    worker_dict[worker_req['worker_id']] = (task_id, time.time())
                    print('Sending task to worker.\n')
                    try:
                        socket.send_json({
                            'status': 'TASK',
                            'task_id': task_id,
                            'function': function,
                            'parameters': parameters
                        })
                        redis_client.hset(task_id, 'status', 'RUNNING')
                    except zmq.error.ZMQError as e:
                        deregister_worker(worker_req['worker_id'])
                else:
                    update_worker_heartbeat(worker_req['worker_id'])
                    socket.send_json({'status':'NO_TASK'})

            # We get a worker sending back result or failure, send result to Redis
            elif worker_req['status'] == 'COMPLETED' or worker_req['status'] == 'FAILED':
                print('Sending result to Redis.\n')
                worker_dict[worker_req['worker_id']] = (True, time.time())
                send_to_redis(worker_req)
                socket.send_json({'status':'LOGGED'})
            else:
                raise('Received invalid status from worker.\n')
            
        except KeyboardInterrupt as e:
            print('Keyboard interrupt, exiting...')
            socket.close()
            context.term()
            break
        except zmq.error.ZMQError as e:
            print(f'ZMQ error on receiving worker request: {e}')
            break
        except Exception as e:
            print('Error: ', e)


def handle_push(port):
    # Handle push workers using ZMQ ROUTER/DEALER sockets

    def choose_worker():
        # Helper function to choose a worker from available workers
        for w in worker_dict:
            prev_task, _ = worker_dict[w]
            if prev_task == True:
                return w
        return None
    
    context = zmq.Context()
    socket= context.socket(zmq.ROUTER)
    socket.bind(f'tcp://127.0.0.1:{port}')
    print('Done initializing for push mode.\n')
    socket.setsockopt(zmq.RCVTIMEO, 1000)

    # Listen for workers
    while True:
        try:
            load = socket.recv_multipart()
            worker_id, worker_req = load[0].decode(), json.loads(load[1])

            # Register worker upon worker initialization
            if worker_req['status'] == 'REGISTER':
                register_worker(worker_id)
                socket.send_multipart([worker_id.encode(), json.dumps({'status':'REGISTERED'}).encode()])

            # Update worker heartbeat upon worker heartbeat
            elif worker_req['status'] == 'HEARTBEAT':
                update_worker_heartbeat(worker_id)
                socket.send_multipart([worker_id.encode(), json.dumps({'status':'HEARTBEAT_BACK'}).encode()])

            # We get a worker sending back result or failure, send result to Redis
            elif worker_req['status'] == 'COMPLETED' or worker_req['status'] == 'FAILED':
                send_to_redis(worker_req)
                worker_dict[worker_id] = (True, time.time())

        # Push task to worker if available
        except zmq.Again:
            got_task,task_id,function,parameters = fetch_task(timeout=1)
            if got_task:
                worker_id = choose_worker()
                if worker_id:
                    worker_dict[worker_id] = (task_id, time.time())
                    print(f'Sending task {task_id} to worker {worker_id}.\n')
                    try:
                        socket.send_multipart([worker_id.encode(), json.dumps({
                            'status': 'TASK',
                            'task_id': task_id,
                            'function': function,
                            'parameters': parameters
                        }).encode()])
                        redis_client.hset(task_id, 'status', 'RUNNING')
                    except zmq.error.ZMQError as e:
                        print(f'ZMQ error on sending task to worker: {e}\n')
                        deregister_worker(worker_id)
                else:
                    print(f'No workers available, requeueing {task_id}.\n')
                    requeue_task(task_id)

        except KeyboardInterrupt as e:
            print('Keyboard interrupt, exiting...')
            socket.close()
            context.term()
            break
        except zmq.error.ZMQError as e:
            print(f'ZMQ error on receiving worker request: {e}')
        except Exception as e:
            print('Error: ', e)
    

if __name__ == '__main__':
    args = parse_arguments()

    # Start task listener on seperate thread
    listener_thread = Thread(target=listen_for_tasks)
    listener_thread.start()

    # Start local workers
    if args.mode == 'local':
        handle_local(args.num_workers)

    # Start heartbeat checker on seperate thread for PULL and PUSH modes
    elif args.mode == 'pull':
        check_heartbeats_thread = Thread(target=check_heartbeats)
        check_heartbeats_thread.start()
        handle_pull(args.port)
    elif args.mode == 'push':
        check_heartbeats_thread = Thread(target=check_heartbeats)
        check_heartbeats_thread.start()
        handle_push(args.port)

    listener_flag = False
    listener_thread.join()