import requests, time, random
from .serialize import serialize, deserialize

base_url = 'http://127.0.0.1:8000/'

valid_statuses = ['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED']


def multiply(x, y=1):
    # Sleeps for 10 seconds to test parallelism
    import time
    time.sleep(10)
    return x * y


def parallel_execution(num_tasks):
    start_time = time.time()
    task_ids = {}
    numbers = []
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'multiply',
                               'payload': serialize(multiply)})
    fn_info = resp.json()
    for _ in range(num_tasks):
        number = random.randint(0, 10000)
        numbers.append(number)
        resp = requests.post(base_url + 'execute_function',
                            json={'function_id': fn_info['function_id'],
                                'payload': serialize(((number,), {'y':2}))})
        assert resp.status_code in [200, 201]
        assert 'task_id' in resp.json()
        task_id = resp.json()['task_id']
        task_ids[task_id] = None

    num_done = 0
    task_keys = list(task_ids.keys())
    for _ in range(20 * num_tasks//3):
        for i in range(num_tasks):
            task_id = task_keys[i]
            if task_ids[task_id] is None:
                resp = requests.get(f'{base_url}result/{task_id}')
                assert resp.status_code == 200
                assert resp.json()['task_id'] == task_id
                if resp.json()['status'] in ['COMPLETED', 'FAILED']:
                    s_result = resp.json()
                    num_done += 1
                    task_ids[task_id] = time.time() - start_time
                    if s_result['status'] == 'COMPLETED':
                        result = deserialize(s_result['result'])
                        assert result == numbers[i] * 2
        if num_done == num_tasks:
            break
        time.sleep(1)

    time_taken = time.time() - start_time
    # Check that each process takes less than 20 * num_tasks/3 seconds
    # This is a loose upper bound, so check the output to see if the time is around 10 * num_tasks/3 seconds
    assert time_taken < 20 * num_tasks//3
    assert num_done == num_tasks
    print(f'Total time taken: {time_taken}')
    task_ids = {k: v for k, v in sorted(task_ids.items(), key=lambda item: item[1])}
    for task_id in task_ids:
        print(f'Task ID: {task_id}, Time taken: {task_ids[task_id]}')


def test_parallel_execution_3():
    print('\nTesting parallel execution with 3 tasks (~1 per worker)')
    parallel_execution(3)

def test_parallel_execution_9():
    print('\nTesting parallel execution with 9 tasks (~3 per worker)')
    parallel_execution(9)

def test_parallel_execution_15():
    print('\nTesting parallel execution with 15 tasks (~5 per worker)')
    parallel_execution(15)