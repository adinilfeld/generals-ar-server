import time
import sys
from src.tests.serialize import serialize, deserialize
import requests
import subprocess
from matplotlib import pyplot as plt

# Modify these parameters based on your experiment
BASE_URL = "http://127.0.0.1:8000/"  # Replace with the actual URL of your MPCSFaaS service
# NUM_WORKERS = [1, 2, 4,8]  # Vary the number of workers

def launch_task_dispatcher(mode,port=4321,num_workers=1):
    # Launch the task dispatcher
    if mode == "local":
        # print(f"Launched task dispatcher. Mode: {mode}, Port: {port}, Number of Workers: {num_workers}")
        return subprocess.Popen(["python3", "src/task_dispatcher.py", "-m", mode, "-w", str(num_workers)],stdout=subprocess.PIPE,stdin=subprocess.PIPE,close_fds=True)
    else:
        # print(f"Launched task dispatcher. Mode: {mode}, Port: {port}, Number of Workers: {num_workers}")
        return subprocess.Popen(["python3", "src/task_dispatcher.py", "-m", mode, "-p", str(port)],stdout=subprocess.PIPE,stdin=subprocess.PIPE,close_fds=True)

def launch_worker(mode,port=4321,num_workers=1):
    url = f"tcp://127.0.0.1:{port}"
    if mode == "local":
        print(f"Local mode.")
        return None
    elif mode == "pull":
        # print(f"Launched worker. Mode: {mode}, URL: {url}, Number of Workers: {num_workers}")
        return subprocess.Popen(["python3", "src/pull_worker.py",  str(num_workers), url],stdout=subprocess.PIPE,stdin=subprocess.PIPE,close_fds=True)
    elif mode == "push":
        # print(f"Launched worker. Mode: {mode}, URL: {url}, Number of Workers: {num_workers}")
        return subprocess.Popen(["python3", "src/push_worker.py",  str(num_workers), url],stdout=subprocess.PIPE,stdin=subprocess.PIPE,close_fds=True)

def noOp():
    return

def register_function(name, func):
    register_function = {
        'name': name,
        'payload': serialize(func)
    }
    response = requests.post(f'{BASE_URL}register_function', json=register_function)
    assert response.status_code == 201
    assert 'function_id' in response.json()
    func_id = response.json()['function_id']
    return func_id

def run_test(func_id, num_tasks):

    execute_function= {
        'function_id': func_id,
        'payload': serialize(((), {}))
    }
    tasks = []
    start_time = time.time()
    for i in range(num_tasks):
        response = requests.post(f'{BASE_URL}execute_function', json=execute_function)
        # assert response.status_code == 201
        # assert 'task_id' in response.json()
        task_id = response.json()['task_id']
        # print('Task ID:', task_id)
        tasks.append(task_id)

    # Retrieve the initial task status
    num_done = 0
    while num_done <= num_tasks:
        for task_id in tasks:
            response = requests.get(f'{BASE_URL}status/{task_id}')
            status = response.json()['status']
            assert response.status_code == 200
            assert response.json()['task_id'] == task_id
            if status == "COMPLETED":
                num_done += 1

    end_time = time.time()
    # print(f"Ran {func_id} succesfully {num_tasks} times.")
    # print(f"Elapsed time: {time.time() - start_time}")
    return end_time - start_time

if __name__ == "__main__":
    noOp_id = register_function("noOp", noOp)

    times = {}
    times["local"] = []
    times["push"] = []
    times["pull"] = []

    import random
    for mode in ['local','pull','push']:
        port = random.randint(1000,9999)
        task_p = launch_task_dispatcher(mode,num_workers=1,port=port)
        worker_p = None
        if mode == "pull" or mode == "push":
            worker_p = launch_worker(mode,num_workers=1,port=port)
        for i in range(10):
            t = run_test(noOp_id, 10)
            times[mode].append(t)
        if mode == "pull" or mode == "push":
            worker_p.kill()
        task_p.kill()

    avg_times = {}
    avg_times["local"] = sum(times["local"])/len(times["local"])
    avg_times["pull"] = sum(times["pull"])/len(times["pull"])
    avg_times["push"] = sum(times["push"])/len(times["push"])

    plt.bar(['Local','Pull','Push'],[avg_times["local"],avg_times["pull"],avg_times["push"]])
    plt.title("Latency by Mode")
    plt.ylabel("Latency (s)")
    plt.savefig("latency.png")
    print(f"Local latency: {avg_times['local']}")
    print(f"Pull latency: {avg_times['pull']}")
    print(f"Push latency: {avg_times['push']}")



