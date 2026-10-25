import time
import pandas as pd
from hyperCSA import HyperCSA
from hyperGraph import HyperGraph
import random
import numpy as np
import os
import re
import glob
import pysdsl

hypergraphs = [
    'amazon-reviews/',
    'house-bills/',
    'house-committees/',
    'mathoverflow-answers/',
    'senate-committees/',
    'senate-bills/',
    'stackoverflow-answers/',
    'trivago-clicks/',
    'walmart-trips/',
    'com-orkut/',
    'com-friendster/',
    ]
names = ["AmRe", "HoBi", "HoCo", "MaAn", "SeCo", "SeBi", "StAn", "TrCl", "WaTr", "CoOr", "CoFr"]

find_search_interval_algorithms = [ (HyperCSA.find_search_intervals_binsearch, "Binärsuche"),
                                    (HyperCSA.find_search_intervals_select, "select")                  
    ]

search_algorithms = [   (HyperCSA.query_binary_search_bounded, "HyperCSA-Binärsuche"),
                        (HyperCSA.query_select_forward_bounded, "Exakte Vorwärtssuche"),
                        (HyperCSA.query_select_forward_unbounded, "Wildcard-Vorwärtssuche"),
                        (HyperCSA.query_select_backward_bounded, "Exakte Rückwärtssuche"),
                        (HyperCSA.query_select_backward_unbounded, "Wildcard-Rückwärtssuche")                  
    ]

def main():
    for dir in hypergraphs:
        generate_hypergraph_samples(dir)
        generate_test_queries(dir, 1000) 

    evaluate_compression_encodings() 
    evaluate_compression()   
    evaluate_borders_vs_select()
    evaluate_find_search_interval_algorithms()
    evaluate_search_algorithm_sampled()



def evaluate_compression():
    results_list = []

    for i, hypergraph in enumerate(hypergraphs):
        result = test_compression(hypergraph)
        result["hypergraph"] = names[i]
        results_list.append(result)

    df = pd.DataFrame(results_list)
    print(df)
    df.to_csv('compression_eval.csv', index=False)

def evaluate_compression_encodings():
    encodings = [
        (pysdsl.EncVectorEliasDelta, "Elias-Delta"),
        (pysdsl.EncVectorFibonacci, "Fibonacci"),
        (pysdsl.EncVectorEliasGamma, "Elias-Gamma"),
    ]

    results_list = []
    for i, hypergraph in enumerate(hypergraphs):
        result = test_integer_encoding(HyperCSA(hypergraph, forceRebuild=True), encodings)
        result["hypergraph"] = names[i]
        results_list.append(result)

    df = pd.DataFrame(results_list)
    print(df)
    df.to_csv('compression_encoding_eval.csv', index=False)

def evaluate_find_search_interval_algorithms():
    results_list = []
    for i, hypergraph in enumerate(hypergraphs):
        result = test_find_search_interval_algorithm(hypergraph, HyperCSA(hypergraph), find_search_interval_algorithms)
        result["hypergraph"] = names[i]
        results_list.append(result)

    df = pd.DataFrame(results_list)
    print(df)
    df.to_csv('query_contains_eval.csv', index=False)

def evaluate_search_algorithms():
    results_list = []
    for i, hypergraph in enumerate(hypergraphs):
        result = test_search_algorithm(hypergraph, HyperCSA(hypergraph), search_algorithms)
        result["hypergraph"] = names[i]
        results_list.append(result)

    df = pd.DataFrame(results_list)
    print(df)
    df.to_csv('query_exact_eval.csv', index=False)

def evaluate_search_algorithm_sampled():
    for dir in hypergraphs:
        original_size = count_lines(f"{dir}hyperedges.txt")
        results_list = []
        for file in glob.glob(f"{dir}samples/hyperedges*"):
            sampling_interval = extract_sampling_number(file)
            result = test_search_algorithm(dir, HyperCSA(f"{dir}samples/", hyperEdges=os.path.basename(file), fileAppendix='-'+sampling_interval), search_algorithms)
            sampling_size = count_lines(file)
            result["size"] = sampling_size / original_size
            results_list.append(result)

        df = pd.DataFrame(results_list)
        df.to_csv('query_contains_sampled_eval.csv', index=False)

def evaluate_borders_vs_select():
    results_list = []
    for i, hypergraph in enumerate(hypergraphs):
        hyperCSA = HyperCSA(hypergraph)
        result = test_borders_vs_select(hypergraph, hyperCSA)
        result["hypergraph"] = names[i]
        result["size"] = hyperCSA.borders.size_in_bytes
        results_list.append(result)

    df = pd.DataFrame(results_list)
    print(df)
    df.to_csv('borders_select_eval.csv', index=False)

def test_compression(hypergraph):
    results = {}

    original_size = HyperGraph(hypergraph).get_size()

    compressed_hypergraph = HyperCSA(hypergraph, forceRebuild=True)
    compressed_size = compressed_hypergraph.get_size()

    results["original_size"] = original_size
    results["compressed_size"] = compressed_size
    results["compression_ratio"] = original_size / compressed_size
    return results

def test_integer_encoding(hyperCSA, encodings):
    results = {}

    for encoding in encodings:
        enc_vector = encoding[0](hyperCSA.psi)
        results[encoding[1]] = enc_vector.size_in_bytes
    return results

def test_search_algorithm(dir, hyperCSA, algorithms, bounded=True, index=0):
    hyperedges = f"{dir}queries.txt"
    results = {}
    
    for algorithm in algorithms:
        with open(hyperedges, "r") as file:
            durations = np.zeros(count_lines(file.name))
            i=0
            print(algorithm[1], dir)
            for line in file:
                query = list(map(int, line.strip().split(","))) 
                if not bounded:
                    query[index] = '*'  
                start_time = time.perf_counter()
                algorithm[0](hyperCSA, query)
                end_time = time.perf_counter()
                durations[i] = end_time - start_time
                i+=1
            results[algorithm[1]] = np.median(durations)
    return results

def test_find_search_interval_algorithm(dir, hyperCSA, algorithms):
    hyperedges = f"{dir}queries.txt"
    results = {}
    
    for algorithm in algorithms:
        with open(hyperedges, "r") as file:
            durations = np.zeros(count_lines(file.name))
            i=0
            print(algorithm[1], dir)
            for line in file:
                query = HyperCSA.translateQuery(hyperCSA, list(map(int, line.strip().split(","))))
                start_time = time.perf_counter()
                algorithm[0](hyperCSA, query)
                end_time = time.perf_counter()
                durations[i] = end_time - start_time
                i+=1
            results[algorithm[1]] = np.mean(durations)
    return results

def test_borders_vs_select(dir, hyperCSA):
    hyperedges = f"{dir}queries.txt"
    results = {}
    
    with open(hyperedges, "r") as file:
        durations = np.zeros(count_lines(file.name))
        i=0
        print("borders", dir)
        for line in file:
            query = list(map(int, line.strip().split(",")))
            start_time = time.perf_counter()
            for j in range(len(query)):
                hyperCSA.borders[j]
                hyperCSA.borders[j+1]
            end_time = time.perf_counter()
            durations[i] = end_time - start_time
            i+=1
        results["borders"] = np.mean(durations)
    with open(hyperedges, "r") as file:
        durations = np.zeros(count_lines(file.name))
        i=0
        print("select", dir)
        for line in file:
            query = list(map(int, line.strip().split(",")))
            selecter = hyperCSA.d.init_select()
            start_time = time.perf_counter()
            for j in range(len(query)-1):
                selecter.select(hyperCSA.gaps[j]+1)
                selecter.select(hyperCSA.gaps[j+1]+1)-1
            end_time = time.perf_counter()
            durations[i] = end_time - start_time
            i+=1
        results["select"] = np.mean(durations)
    return results

def generate_hypergraph_samples(dir):
    intervals = [1, 2, 4, 8, 16, 32, 64, 128]
    
    output_files = {}
    counters = {interval: 0 for interval in intervals}
    
    try:
        for interval in intervals:
            output_filename = f"{dir}samples/hyperedges_sampled_{interval}.txt"
            directory = os.path.dirname(output_filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            output_files[interval] = open(output_filename, 'w', encoding='utf-8')
        
        with open(f"{dir}/hyperedges.txt", 'r', encoding='utf-8') as infile:
            for index, line in enumerate(infile):
                for interval in intervals:
                    if index % interval == 0:
                        output_files[interval].write(line)
                        counters[interval] += 1
                        
    finally:
        for f in output_files.values():
            f.close()

def generate_test_queries(hypergraph, num_samples):
    hyperedges = f"{hypergraph}hyperedges.txt"
    with open(hyperedges, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    sampled_lines = random.sample(lines, min(num_samples, len(lines)))

    with open(f"{hypergraph}queries.txt", 'w') as f:
        for line in sampled_lines:
            f.write(line + "\n")           
            elements = line.split(',')
            random.shuffle(elements)
            permuted_line = ','.join(elements)
            f.write(permuted_line + "\n")

def extract_sampling_number(s):
    match = re.search(r".*sampled_(\d+)\.txt", s)
    if match:
        return match.group(1)
    else:
        return ""

def count_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return sum(1 for _ in file)

if __name__ == '__main__':
    main()
