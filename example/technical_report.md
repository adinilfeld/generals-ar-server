# Technical Report

## Introduction

We created a Function-as-a-Service (FaaS) platform using Python, FastAPI, ZMQ, and Redis. Our implementation consists of an MPCSFaaS service and a worker pool. Clients access the MPCSFaaS service, which in turn communicate with the Redis database and task dispatcher through the REST API. The worker pool is accessed through the task dispatcher, which communicates with the workers through ZMQ. The worker pool consists of a variable number of either push and pull workers, which execute given tasks and return the results to the task dispatcher. Finally, the task dispatcher returns the results to the Redis database.

## Task Dispatcher ('task_dispatcher.py')

***Implementation***

The task dispatcher manages the communication between the Redis server and the workers. It is solely responsible for communication with the workers. It handles task retrieval from the Redis database (through a subscription model) and queues tasks for distribution. It is also responsible for distribituing tasks to workers and receiving results from workers, as well as updating the Redis database with the result of task execution.

***Registration***

Worker registration was done on initialization of the worker. Workers in both push and pull modes would send a message with status "REGISTER", at which point the handler would add an item to the worker registration dictionary indicating the presence of the worker. The key of this dictionary was the worker id, as sent by the worker, and the value was its availability and last heartbeat time.

***Task Distribution***

A key aim of this project was to ensure effective performance of tasks through fair distribution of tasks across all available workers. Our expectation was that bulk task execution would speedup as the number of available workers increased. To do this, we implemented a fair task distribution system for each mode. FOr the local mode, the Multiprocessing Pool automatically distributed tasks to available workers first and otherwise queued tasks until a worker became available. This ensured no worker was given too much work. For the pull mode, tasks were only distributed to workers that sent a "WORKER_READY" status message, ensuring that only available workers were given tasks. Pull workers sent this message immediately upon availability, ensuring speediness of task dispatching. Finally, push workers were handled through the worker registration dictionary, which kept track of a worker's availability (or current task) as well as its heartbeat. Tasks would only be sent to workers marked as available. These methods ensured tasks were fairly distributed across workers in all modes.

***Heartbeat***

The heartbeat mechanism for the service involved collaboration between both each worker implementations and the task dispatcher itself. For the task dispatcher, the heartbeat mechanism is implemented through the handling of the worker. Within the handle loops of both the pull and push worker, the task dispatcher checks the status of a received message to see if it is a heartbeat message. If it is, the task dispatcher replies and updates the worker's last heartbeat time in the worker register ('worker_dict'). If the worker has not sent a heartbeat message within the last 10 seconds, the task dispatcher will remove the worker from the list of active workers. This was done by maintaining a seperate thread that would loop through the worker registration dictionary and check its last heartbeat. If the worker had not sent a heartbeat within the last 10 seconds, it would be marked as unavailable in the dictionary. This ensured the task dispatcher would not send tasks to failed workers. If a worker is marked as failed while it was given a task to execute, this task is requeued in the tasks queue for distribution to another worker.

***Limitations***

The task distribution may be improved upon through other distribution systems, such as round robin. This would ensure all workers would eventually do work, instead of always picking the first available worker in the worker registration dictionary to do a task. In the case of a large number of remote workers or quick tasks, our current approach would find that some workers may never do work. Additional fault tolerance would also benefit the task dispatcher. The current heartbeat system is dependent on the workers sending heartbeats rather than sending heartbeats to the workers themselves and awaiting a response. This would ensure that the task dispatcher would know if a worker had failed, rather than simply assuming it had failed after 10 seconds of no heartbeat. Additionally, the task dispatcher could specifically check on workers that have either been executing a task for a long period or have not been accessed for a long period.

## Pull Worker ('pull_worker.py')

***Implementation***

The pull worker mode operates through a ZMQ REQ/REP pattern, where an individual worker messages the task dispatcher to request a task. The task dispatcher then responds to the specific worker either with a task to execute or an indication that no task is available to execute. This loop is constantly running and there are no blocks in the system; it does not stop if no task is available. To ensure that the task dispatcher sends work to the specific worker that requests it, the pull worker acquires a lock on the socket and awaits for the dispatcher's reply before releasing.

***Heartbeat***

The heartbeat mechanism for the pull worker was implemented within the worker itself. Each pull worker periodically sends a heartbeat and its worker ID to the task dispatcher and awaits a response. This was done through a separate thread in the run loop of the worker which would acquire the lock, send its heartbeat message, and receive the response. By running in a separate thread, a worker that was currently executing a task could still send a heartbeat to the dispatcher.

***Processing***

Tasks were run within each worker process. Parameters were deserialized within the worker (for added performance) and functions were run in a try-catch frame to ensure that workers would not fail by running faulty parameters and would instead send back a "FAILED" status message along with the task ID. Successful results were serialized and sent back to the dispatcher, along with the worker ID (to update register), status, and task_id. A worker awaited a response from the dispatcher that its result was logged before discarding the result and requesting another task.

***Limitations***

A lock on the socket prevented the socket from being accessed by multiple workers at the same time. This added a degree of sequentialness to the program, as only one worker could request and receive a task at a time. This was a limitation of the ZMQ REQ/REP pattern. If the task dispatcher received many tasks that could be executed very rapidly and there were many workers, this limitation was especially apparent as tasks could only be sent out sequentially and the overhead to receive the task would be much higher than execution of the task. Conversely, if tasks took longer to execute and there were fewer workers polling the task dispatcher, this overhead did not impact performance as much.

The use of a repeated loop even when no tasks were available added unnecessary overhead to the system. This could be reduced by having the dispatcher notify the pull workers when a task was available and then await a response from some available worker, sending the task to this specific worker. However, we found this repeated loop most effective in providing fault tolerance as the repeated communication provided another way for the dispatcher to update the heartbeat time of workers in the worker register.

## Push Worker ('push_worker.py')

***Implementation***

The push worker mode operates through a ZMQ DEALER/ROUTER pattern, where push workers await tasks from the task dispatcher. Workers first register themselves to the task dispatcher with their worker IDs. The task dispatcher uses this register to choose which worker it sends a task to when one is available, picking the first free worker. The task dispatcher waits for messages from push workers for a certain timeout (1 second). These messages could either be a heartbeat, registration, or status update on an executing task. If no message is received within this time, the task dispatcher attempts to fetch a task from the task queue and dispatch it to an available worker (chosen through the worker register). If a worker and task are available, the worker is sent the task and its worker register is updated to contain the task_id of the task it is running. If no workers are available and a task was fetched, the task is requeued. If there is no task available, we repeat this loop, once again checking if a message was received from a push worker.

***Heartbeat***

Heartbeats are implemented as in the pull worker, with the exception that the heartbeat response message from the task dispatcher is received within the main "run()" thread. This prevents the need to lock the socket.

***Processing***

Processing is implemented as in the pull worker.

***Limitations***

The push worker shares the heartbeat limitation with the pull worker. In addition, the handling of the push worker is done in a single process which both awaits messages from the worker then sends tasks (if available). This process could be multithreaded, with one thread strictly awaiting messages from the worker and another thread strictly sending tasks to workers when they are available. As it stands, tasks are only fetched and sent when no message has been received from push workers after a set timeout. This new approach would allow greater concurrency. The overhead of the repeated loop would decrease: the message receiving thread could simply await until a message is received to process and the dispatching thread could await until a task is available to send.
