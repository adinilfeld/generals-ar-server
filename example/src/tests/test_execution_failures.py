import requests, logging, time, random
from .serialize import serialize

base_url = 'http://127.0.0.1:8000/'

valid_statuses = ['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED']


def failed_roundtrip(function, args):
    # Simulates a failed roundtrip given a function and its arguments
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'function',
                               'payload': serialize(function)})
    fn_info = resp.json()
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': fn_info['function_id'],
                               'payload': serialize(args)})
    assert resp.status_code in [200, 201]
    assert 'task_id' in resp.json()
    task_id = resp.json()['task_id']
    for _ in range(20):
        resp = requests.get(f'{base_url}result/{task_id}')
        assert resp.status_code == 200
        assert resp.json()['task_id'] == task_id
        if resp.json()['status'] in ['COMPLETED', 'FAILED']:
            logging.warning(f'Task is now in {resp.json()["status"]}')
            s_result = resp.json()
            logging.warning(s_result)
            print(resp.json())
            assert resp.json()['status'] == 'FAILED'
            break
        time.sleep(1)


def test_too_many_args():
    def double(x):
        return x * 2
    x = random.randint(0, 10000)
    args = ((x, x,), {})
    failed_roundtrip(double, args)


def test_too_little_args():
    def multiply(x, y):
        return x * y
    x = random.randint(0, 10000)
    args = ((x,), {})
    failed_roundtrip(multiply, args)


def test_too_many_kwargs():
    def multiply(x, y=1):
        return x * y
    x = random.randint(0, 10000)
    y= random.randint(0, 10000)
    args = ((x,), {'y': y, 'z': y})
    failed_roundtrip(multiply, args)


def test_wrong_kwargs():
    def multiply(x, y=1):
        return x * y
    x = random.randint(0, 10000)
    y = random.randint(0, 10000)
    args = ((x,), {'z': y})
    failed_roundtrip(multiply, args)


def test_error_in_function():
    def divide_by_zero(x):
        return x / 0
    args = ((1,), {})
    failed_roundtrip(divide_by_zero, args)


def test_function_import_error():
    def random_integer():
        return np.random.randint(0, 10000)
    args = ((), {})
    failed_roundtrip(random_integer, args)