import requests, logging, time, random
from .serialize import serialize, deserialize

base_url = 'http://127.0.0.1:8000/'

valid_statuses = ['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED']


def test_fn_registration_invalid():
    # Using a non-serialized payload data
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'hello',
                               'payload': 'payload'})
    assert resp.status_code in [500, 400]


def double(x):
    return x * 2


def test_fn_registration():
    # Using a real serialized function
    serialized_fn = serialize(double)
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'double',
                               'payload': serialized_fn})
    assert resp.status_code in [200, 201]
    assert 'function_id' in resp.json()


def test_execute_fn_invalid():
    # Using a non-serialized payload data
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'hello',
                               'payload': serialize(double)})
    fn_info = resp.json()
    assert 'function_id' in fn_info
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': fn_info['function_id'],
                               'payload': 'payload'})
    assert resp.status_code in [500, 400]


def test_execute_fn_id_not_found():
    # Using a non-existent function ID
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'hello',
                               'payload': serialize(double)})
    fn_info = resp.json()
    assert 'function_id' in fn_info
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': '1234',
                               'payload': 'payload'})
    assert resp.status_code in [404, 422]
    

def test_execute_fn():
    # Using a real function ID
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'hello',
                               'payload': serialize(double)})
    fn_info = resp.json()
    assert 'function_id' in fn_info
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': fn_info['function_id'],
                               'payload': serialize(((2,), {}))})
    print(resp)
    assert resp.status_code == 200 or resp.status_code == 201
    assert 'task_id' in resp.json()
    task_id = resp.json()['task_id']
    resp = requests.get(f'{base_url}status/{task_id}')
    print(resp.json())
    assert resp.status_code == 200
    assert resp.json()['task_id'] == task_id
    assert resp.json()['status'] in valid_statuses


def test_task_id_not_found():
    # Using a real function ID
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'hello',
                               'payload': serialize(double)})
    fn_info = resp.json()
    assert 'function_id' in fn_info
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': fn_info['function_id'],
                               'payload': serialize(((2,), {}))})
    print(resp)
    assert resp.status_code == 200 or resp.status_code == 201
    assert 'task_id' in resp.json()
    task_id = '1234'
    resp = requests.get(f'{base_url}status/{task_id}')
    print(resp.json())
    assert resp.status_code == 404
    resp = requests.get(f'{base_url}result/{task_id}')
    print(resp.json())
    assert resp.status_code == 404



def test_roundtrip():
    # Everything should work properly
    resp = requests.post(base_url + 'register_function',
                         json={'name': 'double',
                               'payload': serialize(double)})
    fn_info = resp.json()
    number = random.randint(0, 10000)
    resp = requests.post(base_url + 'execute_function',
                         json={'function_id': fn_info['function_id'],
                               'payload': serialize(((number,), {}))})
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
            if s_result['status'] == 'COMPLETED':
                result = deserialize(s_result['result'])
                assert result == number * 2
                print(resp.json())
                print(f'Original number: {number}, Result: {result}')
            break
        time.sleep(1)