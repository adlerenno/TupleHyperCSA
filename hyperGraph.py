import pysdsl
import functools
import time

class HyperGraph:

    def timer(func):
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            tic = time.perf_counter()
            value = func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            print(f"Elapsed time: {elapsed_time:0,.4f} s")
            return value
        return wrapper_timer
    
    @timer
    def __init__(self, dir):
        hyperedges = f"{dir}hyperedges.txt"
        file = open(hyperedges, "r")
        result = []
        count = 0
        for line in file:
            entries = list(map(int, line.strip().split(",")))
            result.extend([max(0, x) for x in entries])
            count += 1
        self.hypergraph = pysdsl.IntVector(result[:-1])

    def get_size(self):
        return self.hypergraph.size_in_bytes

    @timer
    def search(self, query):
        print(f"Searching for pattern: ({','.join(map(str, query))})")
        