from fastapi import FastAPI, HTTPException
import redis, uuid
from util import RegisterFn, RegisterFnRep, ExecuteFnReq, ExecuteFnRep, TaskStatusRep, TaskResultRep
from tests.serialize import deserialize


# Initialize FastAPI app and Redis connection
app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


# Check if a string is serialized
def is_serialized(obj_str):
    try:
        deserialize(obj_str)
        return True
    except Exception:
        return False
    

# Endpoint to register functions
@app.post('/register_function/', response_model=RegisterFnRep, status_code=201)
def register_function(function: RegisterFn):
    if not is_serialized(function.payload):
        raise HTTPException(status_code=400, detail='Payload is not serialized')
    function_id = str(uuid.uuid4())
    function_entry = {'name': function.name, 
                      'payload': function.payload}
    redis_client.hmset(function_id, function_entry)
    return {'function_id': function_id}


# Endpoint to execute a function
@app.post('/execute_function/', response_model=ExecuteFnRep, status_code=201)
def execute_function(req: ExecuteFnReq):
    if not is_serialized(req.payload):
        raise HTTPException(status_code=400, detail='Payload is not serialized')
    task_id = str(uuid.uuid4())
    function_id = str(req.function_id)
    if not redis_client.exists(function_id):
        raise HTTPException(status_code=404, detail='Function ID {req.function_id} not found') 
    task_entry = {'function_id': function_id, 
                  'payload': req.payload,
                  'status': 'QUEUED',
                  'result': ''}
    redis_client.hmset(task_id, task_entry)
    redis_client.publish('Tasks', task_id)
    return {'task_id': task_id}


# Endpoint to retrieve task status
@app.get('/status/{task_id}/', response_model=TaskStatusRep, status_code=200)
def get_task_status(task_id: str) -> TaskStatusRep:
    task_status = redis_client.hget(task_id, 'status')
    if task_status is None:
        raise HTTPException(status_code=404, detail='Task ID {task_id} not found')
    return {'task_id': task_id, 'status': task_status}


# Endpoint to retrieve task results
@app.get('/result/{task_id}/', response_model=TaskResultRep, status_code=200)
def get_task_result(task_id: str):
    status = redis_client.hget(task_id, 'status')
    if status is None:
        raise HTTPException(status_code=404, detail='Task ID {task_id} not found')
    result = str(redis_client.hget(task_id, 'result'))
    return {'task_id': task_id, 'status': status, 'result': result}