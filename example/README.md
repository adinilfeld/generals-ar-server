# Function as a Service (FaaS) Platform

Team: Kevin Wu and Francisco Mendes

## Running the FaaS Platform

1. Navigate to `src/`
2. Terminal 1 - start Redis: `redis-server`
3. Terminal 2 - start the API: `uvicorn main:app --reload`
4. Terminal 3 - start the task dispatcher
   1. Local: `python3 task_dispatcher.py -m local -p 8888 -w 2`
   2. Pull: `python3 task_dispatcher.py -m pull -p 8888`
   3. Push: `python3 task_dispatcher.py -m push -p 8888`
5. Terminal 4 - start the workers (for push/pull only)
   1. Pull: `python3 pull_worker.py 2 tcp://127.0.0.1:8888`
   2. Push: `python3 push_worker.py 2 tcp://127.0.0.1:8888`
6. Terminal 5 - run the client: `python3 client.py -p 8000`

## Running Pytests (on Mac)

1. `chmod +x run_tests.sh`
2. Run tests
   1. Local worker: `./run_tests.sh local`
   2. Pull worker: `./run_tests.sh pull`
   3. Push worker: `./run_tests.sh push`
3. The tests will run in one of the new terminal windows. Check the output for the results.

## Running Performance Tests (on Mac)

1. `chmod +x run_performance.sh`
2. Run tests (`w` is the number of workers)
   1. Local worker: `./run_performance.sh local w`
   2. Pull worker: `./run_performance.sh pull w`
   3. Push worker: `./run_performance.sh push w`
3. Results are saved in `src/results/` and plots are made by `src/tests/performance.ipynb` and saved in `figures/`
