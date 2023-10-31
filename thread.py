import threading
import time


class ThreadRunner:
    def __init__(self, num_threads):
        """Create pool of threads"""
        self.num_threads = num_threads
        self.threads = []

    def __enter__(self):
        return self

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

    def __exit__(self, type, value, traceback):
        for thread in self.threads:
            if thread.ident is not None:
                thread.join()


class Queue:
    def __init__(self):
        self.q = []
    def push(self, element):
        if element not in self.q:
            self.q.append(element)
    def pop(self):
        if len(self.q):
            return self.q.pop(0)
    def print(self):
        print(self.q)

class Semaphore:
    def __init__(self, value):
        self.value = value
        self.queue = Queue()
        self._lock = threading.Lock()

    def P(self, thread):
        self._lock.acquire()
        if self.value > 0 and thread not in self.queue.q:
            self.value -= 1
            self._lock.release()
            return True
        else:
            # fake semaphore lock
            self.queue.push(thread)
            self._lock.release()
            return False

    def V(self):
        self._lock.acquire()
        _ = self.queue.pop()
        self.value += 1
        self._lock.release()


if __name__ == "__main__":
    num_resources = 3
    num_threads = 10
    num_iters = 5
    thread_perf = dict()

    semaphore = Semaphore(value=num_resources)

    def thread_func(idx):
        start_spin_time = time.perf_counter()
        while not semaphore.P(idx):
            # spin on semaphore's lock
            time.sleep(0.1)
        end_spin_time = time.perf_counter()
        print(f"ENTER FUNC {idx}")
        # do work
        i = 0
        while (i < 1_000_000):
            # getting rich
            i += 1
        semaphore.V()
        print(f"EXIT FUNC {idx}")
        thread_time = time.thread_time()
        total_spin_time = (end_spin_time - start_spin_time)
        if idx not in thread_perf:
            thread_perf[idx] = [total_spin_time, thread_time]
        else:
            thread_perf[idx][0] += total_spin_time
            thread_perf[idx][1] += thread_time

    for _ in range(num_iters):
        with ThreadRunner(num_threads) as runner:
            print(runner)
            # give each thread a thread function and arguments
            runner.run([thread_func]*num_threads, [(idx,) for idx in range(1, num_threads+1)])

    # print(thread_perf)
    for i, (total_spin_time, thread_time) in thread_perf.items():
        total_spin_time /= num_iters
        thread_time /= num_iters
        thread_time = '{:.3e}'.format(thread_time)
        total_spin_time = '{:.3e}'.format(total_spin_time)
        print(f"Total Spin Time {i}: {total_spin_time}")
        print(f"Total Thread Time {i}: {thread_time}")
