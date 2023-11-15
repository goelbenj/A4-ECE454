import argparse
import threading
import time

#ThreadRunner class is responsible for thread control
class ThreadRunner:
    #initializes a list of threads to be managed with a given timeout
    def __init__(self, num_threads, timeout):
        """Create pool of threads"""
        self.num_threads = num_threads
        self.threads = []
        self.timeout = timeout

    def __enter__(self):
        return self

    #spins up threads on a target function
    def run(self, thread_functions, thread_args):
        try:
            _ = iter(thread_functions)
        except TypeError:
            # not iterable
            thread_functions = [thread_functions]
        else:
            # iterable
            if len(thread_functions) != self.num_threads:
                raise ValueError(f"Length of thread_functions is not equal to number of threads")
        try:
            _ = iter(thread_args)
        except TypeError:
            # not iterable
            thread_args = [thread_args]
        else:
            # iterable
            if len(thread_args) != self.num_threads:
                raise ValueError(f"Length of thread_functions is not equal to number of threads")

        self.threads = [threading.Thread(target=thread_func, args=args) for thread_func, args in zip(thread_functions, thread_args)]
        for thread in self.threads:
            thread.start()

    #reaps threads and checks for timeout error condition
    def __exit__(self, type, value, traceback):
        for thread in self.threads:
            if thread.ident is not None:
                thread.join(self.timeout)
                if thread.is_alive():
                    print(f'Thread {thread} timed out...')
                    #exit()

#simple queue designed to be used with semaphore
class Queue:
    def __init__(self, threads):
        self.q = threads
    def push(self, element):
        if element not in self.q:
            self.q.append(element)
    def pop(self):
        if len(self.q):
            return self.q.pop(0)
    def print(self):
        print(self.q)

#synchronizes thread execution by keeping track of available resources and threads in-line to claim the next available resource
class Semaphore:
    #initializes semaphore with a number of resources and queue of threads to claim a resource
    def __init__(self, value, idx):
        self.total_value = value
        self.value = value
        self.queue = Queue(idx)
        self._lock = threading.Lock()

    #semaphore wait function responsible for giving an available resource to a thread or enforcing a wait condition on the thread
    def P(self, thread):
        self._lock.acquire()
        if self.value > 0 and thread == self.queue.q[0]:
            self.value -= 1
            _ = self.queue.pop()
            self._lock.release()
            return True
        else:
            # fake semaphore lock
            self._lock.release()
            return False

    #semaphore signal function responsible for freeing a resource when a thread is finished with it and signaling
    #the next thread in queue to claim it
    def V(self):
        self._lock.acquire()
        self.value += 1
        self.print_queue_situation()
        self._lock.release()

    def print_queue_situation(self):
        print(f"QUEUE STATUS: {self.queue.q}")
        print(f"RESOURCE STATUS: {self.value}/{self.total_value}")

if __name__ == "__main__":
    #default values
    num_resources = 3
    num_threads = 10
    num_iters = 5
    timeout = 0.1

    #CLI user input parser for modifying parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--customers", metavar = "customers", type = int, help = "The number of banking customers (threads)", default = num_threads)
    parser.add_argument("-t", "--tellers", metavar = "tellers", type = int, help = "The number of banking tellers (shared resources)", default = num_resources)
    parser.add_argument("-i", "--iterations", metavar = "iterations", type = int, help = "The number of iterations to average over", default = num_iters)
    parser.add_argument("-time", "--timeout", metavar = "timeout", type = float, help = "The amount of time a customer can resonably wait (thread timeout)", default = timeout)
    args = parser.parse_args()
    
    #updating parameters based on user input
    num_threads = args.customers
    num_resources = args.tellers
    num_iters = args.iterations
    timeout = args.timeout

    #initializing data structures for logging thread performance metrics
    thread_perf = dict()
    
    #initializing semaphore for the given number of resources and threads 
    semaphore = Semaphore(value=num_resources, idx=list(range(num_threads)))

    #thread function to utilize resource and then return
    def thread_func(idx):
        #performance logging
        start_spin_time = time.perf_counter()
        #try to acquire a resource (wait)
        while not semaphore.P(idx):
            # spin on semaphore's lock
            time.sleep(0.1)
        #performance logging
        end_spin_time = time.perf_counter()
        #print thread status
        print(f"ENTER FUNC {idx}")
        #simulate work with the resource
        i = 0
        while (i < 1_000_000):
            i += 1
        #return resource (signal)
        semaphore.V()
        #print thread status
        print(f"EXIT FUNC {idx}")
        #performance logging
        thread_time = time.thread_time()
        total_spin_time = (end_spin_time - start_spin_time)
        if idx not in thread_perf:
            thread_perf[idx] = [total_spin_time, thread_time]
        else:
            thread_perf[idx][0] += total_spin_time
            thread_perf[idx][1] += thread_time

    #program performance logging
    start_program_time = time.perf_counter()
    #spin up all the threads
    for _ in range(num_iters):
        with ThreadRunner(num_threads, timeout) as runner:
            print(runner)
            # give each thread a thread function and arguments
            runner.run([thread_func]*num_threads, [(idx,) for idx in range(num_threads)])
        semaphore = Semaphore(value=num_resources, idx=list(range(num_threads)))

    #program performance logging
    end_program_time = time.perf_counter()
    avg_program_time = (end_program_time - start_program_time) / num_iters

    #print performance results
    print("--------------")
    print(f"Average Program Time {avg_program_time:.3e}")
    print("--------------")
    for i, (total_spin_time, thread_time) in thread_perf.items():
        total_spin_time /= num_iters
        thread_time /= num_iters
        print(f"Average Spin Time {i}: {total_spin_time:.3e}")
        print(f"Average Thread Time {i}: {thread_time:.3e}")
