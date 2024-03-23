from pydantic import BaseModel
from tests.serialize import serialize, deserialize
import uuid, argparse


class RegisterFn(BaseModel):
    name: str
    payload: str

class RegisterFnRep(BaseModel):
    function_id: uuid.UUID

class ExecuteFnReq(BaseModel):
    function_id: uuid.UUID
    payload: str

class ExecuteFnRep(BaseModel):
    task_id: uuid.UUID

class TaskStatusRep(BaseModel):
    task_id: uuid.UUID
    status: str

class TaskResultRep(BaseModel):
    task_id: uuid.UUID
    status: str
    result: str


def parse_arguments(worker_type):
    # Parse arguments for push and pull workers
    parser = argparse.ArgumentParser(description=worker_type)
    parser.add_argument(
        'num_workers',
        type=int,
        help='Number of worker processors'
    )
    parser.add_argument(
        'url',
        help='URL of task dispatcher'
    )
    args = parser.parse_args()
    return args


def process_task(task):
    # Process a task
    task_id = task['task_id']
    function = deserialize(task['function'])
    parameters = deserialize(task['parameters'])
    args = parameters[0]
    kwargs = parameters[1]
    try:
        result = function(*args,**kwargs)
        return {'task_id':task_id, 'result':serialize(result), 'status':'COMPLETED'}
    except Exception as e:
        print(f'Error on processing task: {e}')
        return {'task_id':task_id, 'result':None, 'status':'FAILED'}