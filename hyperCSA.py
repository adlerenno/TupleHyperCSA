import binsearch
import graph_parser as parser
import pysdsl
import yaml
import functools
import time
from collections import Counter
import pickle
import os
import sys

class HyperCSA:

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
    def __init__(self, dir, directed=True, forceRebuild=False, hyperEdges="hyperedges.txt", fileAppendix=""):
        self.directed = directed
        file_extension = "directed" if directed else "undirected"
        hyperedges = f"{dir}{hyperEdges}"
        pkl = f"{dir}hyperCSA-{file_extension}{fileAppendix}.pkl"
        print(pkl)
        if not forceRebuild and os.path.exists(pkl):
            print(f"Load saved HyperCSA from '{pkl}'")
            with open(pkl, "rb") as input:
                hyperCSA = pickle.load(input)
                self.__dict__.update(hyperCSA.__dict__)
        else:
            print(f"Calculate HyperCSA from '{hyperedges}'")
            print("Starting construction of HyperCSA")
            self.t, self.encoding, self.count, self.gaps, self.borders = parser.parse_array(hyperedges, directed)
            self.encoding_inv = [{v: k for k, v in enc.items()} for enc in self.encoding]
            self.psi = self.calc_psi()
            self.d = self.calc_d()
            print(f"Size of Psi: {self.psi.size_in_bytes} bytes")
            print(f"Size of D: {self.d.size_in_bytes} bytes")
            print("Finished construction of HyperCSA")
            with open(pkl, "wb") as output:
                    pickle.dump(self, output)

    def get_size(self):
        return sum([self.gaps.size_in_bytes, self.borders.size_in_bytes, self.psi.size_in_bytes, self.d.size_in_bytes, sys.getsizeof(self.encoding)])

    def calc_psi(self):
        print("Starting construction of Suffix Array")
        sa = pysdsl.SuffixArraySadakaneInt(self.t)
        print("Finished construction of Suffix Array")
        psi = sa.psi[1:-1]
        for i in range(self.count):
            next = i
            while psi[next]-1 >= self.count:
                next = psi[next]-1
            psi[next] = i+1
        psi = pysdsl.EncVectorEliasDelta(psi)
        return psi

    def calc_d(self):
        value_counts = Counter(self.t)
        bitarray = []
        for _, count in sorted(value_counts.items()):
            bitarray.extend([1] + [0] * (count - 1))
        bitarray.append(1)
        return pysdsl.BitVector(bitarray)

    def decompress(self, index):
        result = []
        intermediate = []
        ranker = self.d.init_rank()
        nextPos = index
        startFound = False
        while self.psi[nextPos]-1 != index:
            if nextPos < self.count:
                startFound = True
            if startFound:
                result.append(ranker.rank(nextPos+1))
            else:
                intermediate.append(ranker.rank(nextPos+1))
            nextPos = self.psi[nextPos]-1
        result.append(ranker.rank(nextPos+1))
        result.extend(intermediate)
        for i in range(len(result)):
            result[i] = self.encoding[i][result[i]-self.gaps[i]]
        return result

    @staticmethod
    def calc_Map(filename):
        pkl = f"{filename}.pkl"
        yml = f"{filename}.yml"
        if os.path.exists(pkl):
            print(f"Load saved label-map from '{pkl}'")
            with open(pkl, "rb") as input:
                data = pickle.load(input)
        else:
            print(f"Read label-map from '{yml}'")
            with open(yml, "r") as input:
                with open(pkl, "wb") as output:
                    data = yaml.safe_load(input)
                    pickle.dump(data, output)
        return data

    @staticmethod
    def resolveName(hyperedgeMap, nodeMap, tuple):
        return f"{hyperedgeMap[tuple[0]]}: \t\t{', '.join([nodeMap[node] for node in tuple[1:]])}"

    def translateQuery(self, query):    
        result = []
        if len(query) <= len(self.encoding_inv):
            for index, entry in enumerate(query):
                if entry == "*":
                    result.append("*")
                else:
                    translated_value = self.encoding_inv[index].get(entry, -1-self.gaps[-1])
                    result.append(translated_value + self.gaps[index])
            return result
        else:
            return []

    def query_binary_search_bounded(self, query):
        query = self.translateQuery(query)
        ranker = self.d.init_rank()
        return range(binsearch.search_left_csa(self.psi, query, 0, len(self.psi), key=lambda x: ranker.rank(x+1)), binsearch.search_right_csa(self.psi, query, 0, len(self.psi), key=lambda x: ranker.rank(x+1))+1)

    def query_select_forward_bounded(self, query):
        query = self.translateQuery(query)
        intervals = self.find_search_intervals_binsearch(query)
        if len(query) == 0 and len(intervals) == 0:
            return range(0,0)
        intervals.append(intervals[0])
        for i in range(len(intervals)-1):
            intervals[i] = range(binsearch.search_left(self.psi, intervals[i+1].start+1, intervals[i].start, intervals[i].stop-1), binsearch.search_right(self.psi, intervals[i+1].stop, intervals[i].start, intervals[i].stop-1)+1)
        intermediate = [intervals[0].start, intervals[0].stop-1]
        for i in range(len(query)-1):
            interval = intervals[i+1]
            intermediate = (self.psi[binsearch.search_left(self.psi, interval.start+1, intermediate[0], intermediate[1])]-1, self.psi[binsearch.search_right(self.psi, interval.stop, intermediate[0], intermediate[1])]-1)
        return range(intermediate[0], intermediate[1]+1)

    def query_select_forward_unbounded(self, query):
        query = self.translateQuery(query)
        intervals = self.find_search_intervals_binsearch(query, False)
        if len(query) == 0 and len(intervals) == 0:
            return range(0,0)
        intermediate = list(intervals[0])
        for i in range(len(query)-1):
            next = []
            for j in intermediate:
                if self.psi[j]-1 in intervals[i+1]:
                    next.append(self.psi[j]-1)
            intermediate = next
        return intermediate
    
    def query_select_backward_bounded(self, query):
        query = self.translateQuery(query)
        intervals = self.find_search_intervals_binsearch(query)
        if len(query) == 0 and len(intervals) == 0:
            return range(0,0)
        intermediate = [intervals[-1].start, intervals[-1].stop-1]
        for i in range(len(query)-1, 0, -1):
            interval = intervals[i-1]
            intermediate = (binsearch.search_left(self.psi, intermediate[0]+1, interval.start, interval.stop-1), binsearch.search_right(self.psi, intermediate[1]+1, interval.start, interval.stop-1))
        return range(intermediate[0], intermediate[1]+1)
    
    def query_select_backward_unbounded(self, query):
        query = self.translateQuery(query)
        intervals = self.find_search_intervals_binsearch(query, False)
        if len(query) == 0 and len(intervals) == 0:
            return range(0,0)
        intermediate = intervals[-1]
        for i in range(len(query)-1, 0, -1):
            next = []
            for j in intervals[i-1]:
                if self.psi[j]-1 in intermediate:
                    next.append(j)
            intermediate = next
        return intermediate
    
    def find_search_intervals_binsearch(self, query, bounded=True):
        if bounded and "*" in query:
            raise ValueError("Wildcard parameter '*' is not allowed in bounded search")
        ranker = self.d.init_rank()
        intervals = []
        for i in range(len(query)):
            lo = self.borders[i]
            hi = self.borders[i+1]-1
            if query[i] == "*":
                intervals.append(range(lo, hi+1))
            else:
                intervals.append(range(binsearch.search_left(self.psi, query[i], lo, hi, key=lambda x: ranker.rank(x+1)), binsearch.search_right(self.psi, query[i], lo, hi, key=lambda x: ranker.rank(x+1))+1))
        return intervals

    def find_search_intervals_select(self, query, bounded=True):   
        if bounded and "*" in query:
            raise ValueError("Wildcard parameter '*' is not allowed in bounded search")
        selecter = self.d.init_select()
        intervals = []
        for i in range(len(query)):
            if query[i] == "*":
                intervals.append(range(self.borders[i], self.borders[i+1]))
            else: 
                if query[i] > 0:
                    intervals.append(range(selecter.select(query[i]), selecter.select(query[i]+1)))
                else:
                    intervals.append(range(0, 0))
        return intervals
    