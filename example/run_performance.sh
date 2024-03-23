#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <worker_type> <num_workers>"
    echo "Worker types: local, push, pull"
    exit 1
fi

worker_type="$1"
num_workers="$2"

cd src/
current_directory=$(pwd)
echo "Running tests in $current_directory"

# Run a command in a new terminal window
run_in_terminal() {
    local command="$1"
    osascript -e "tell application \"Terminal\"
        activate
        do script \"$command\"
    end tell"
}

# # Terminal 1: Start Redis
run_in_terminal "cd '$current_directory'; redis-server"

# Terminal 2: Start the API
run_in_terminal "cd '$current_directory'; uvicorn main:app --reload"

# Terminal 3: Start the task dispatcher
# Terminal 4: (for pull/push only) Start the workers based on the worker type
if [ "$worker_type" == "local" ]; then
    run_in_terminal "cd '$current_directory'; python3 task_dispatcher.py -m local -p 8888 -w $num_workers"
elif [ "$worker_type" == "pull" ]; then
    run_in_terminal "cd '$current_directory'; python3 task_dispatcher.py -m pull -p 8888"
    sleep 1
    run_in_terminal "cd '$current_directory'; python3 pull_worker.py $num_workers tcp://127.0.0.1:8888"
elif [ "$worker_type" == "push" ]; then
    run_in_terminal "cd '$current_directory'; python3 task_dispatcher.py -m push -p 8888"
    sleep 1
    run_in_terminal "cd '$current_directory'; python3 push_worker.py $num_workers tcp://127.0.0.1:8888"
else
    echo "Invalid worker type: $worker_type"
    exit 1
fi
sleep 5 # Wait for the workers to connect

# Terminal 5: Run pytest tests
run_in_terminal "cd '$current_directory'; python3 tests/performance.py $num_workers '$worker_type'"
