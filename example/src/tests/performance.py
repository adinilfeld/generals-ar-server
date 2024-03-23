import requests, time, random, sys, dill, codecs, os
import pandas as pd

def serialize(obj) -> str:
    return codecs.encode(dill.dumps(obj), "base64").decode()
def deserialize(obj: str):
    return dill.loads(codecs.decode(obj.encode(), "base64"))


base_url = 'http://127.0.0.1:8000/'

valid_statuses = ['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED']


def multiply(x, y=1):
    import time
    time.sleep(3)
    return x * y


def parallel_execution(num_workers, tasks_per_worker):
    num_tasks = num_workers * tasks_per_worker
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
    while True:
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
        time.sleep(0.1)

    time_taken = time.time() - start_time
    return time_taken


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 performance.py <num_workers> <worker_type>')
        sys.exit(1)
    NUM_WORKERS = int(sys.argv[1])
    WORKER_TYPE = sys.argv[2]

    results = pd.DataFrame()
    for tasks_per_worker in [1, 3]:
        print(f'Running {NUM_WORKERS} workers with {tasks_per_worker} tasks per worker')
        times = []
        for _ in range(5):
            times.append(parallel_execution(NUM_WORKERS,tasks_per_worker))
        results[str(tasks_per_worker)] = times
        print(f'Average time taken: {sum(times)/len(times)}\n')
    
    os.makedirs('results', exist_ok=True)
    results.to_csv(f'results/{WORKER_TYPE}_{NUM_WORKERS}.csv', index=False)