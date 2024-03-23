import requests, argparse, time, random
from tests.serialize import serialize, deserialize


# Test function
def double(x):
    import time
    time.sleep(10)
    return x * 2


X = random.randint(0, 10000)
STATUSES = ['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED']


parser = argparse.ArgumentParser(description='Client to register and execute functions.')
parser.add_argument('-p', '--port', type=str, help='Port number of the API server')


if __name__ == '__main__':
    args = parser.parse_args()
    base_url = f'http://127.0.0.1:{args.port}/'

    # Register the function and get its ID
    register_function = {
        'name': 'double',
        'payload': serialize(double)
    }
    response = requests.post(f'{base_url}register_function', json=register_function)
    assert response.status_code == 201
    assert 'function_id' in response.json()
    function_id = response.json()['function_id']
    print('Function ID:', function_id)

    # Register the task and get its ID
    execute_function = {
        'function_id': function_id,
        'payload': serialize(((X,), {}))
    }
    response = requests.post(f'{base_url}execute_function', json=execute_function)
    assert response.status_code == 201
    assert 'task_id' in response.json()
    task_id = response.json()['task_id']
    print('Task ID:', task_id)

    # Retrieve the initial task status
    response = requests.get(f'{base_url}status/{task_id}')
    status = response.json()['status']
    assert response.status_code == 200
    assert response.json()['task_id'] == task_id
    assert status in STATUSES
    print('Initial task status:', status)

    time.sleep(1)

    # Retrieve the intermediate task status
    response = requests.get(f'{base_url}status/{task_id}')
    status = response.json()['status']
    assert response.status_code == 200
    assert response.json()['task_id'] == task_id
    assert status in STATUSES
    print('Intermediate task status:', status)


    # Retrieve the task result
    response = requests.get(f'{base_url}result/{task_id}')
    status = response.json()['status']
    # Make this more efficient later
    while status == 'RUNNING' or status == 'QUEUED':
        time.sleep(1)
        response = requests.get(f'{base_url}result/{task_id}')
        status = response.json()['status']
        print(f'Current status: {status}')
    if response.json()['status'] == 'COMPLETED':
        result = deserialize(response.json()['result'])
        assert response.status_code == 200
        assert response.json()['task_id'] == task_id
        assert status in STATUSES
        assert result == X * 2
        print('Final Task status:', status)
        print('Task result:', result)
    else:
        print('Task failed.')