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


if __name__ == "__main__":
    def thread_func(idx):
        print(f"ENTER FUNC {idx}")
        time.sleep(0.5)
        print(f"EXIT FUNC {idx}")

    with ThreadRunner(num_threads=3) as runner:
        print(runner)
        runner.run([thread_func]*3, [(idx,) for idx in range(3)])
