import pysdsl
import itertools
from collections import defaultdict

def parse(fileName):
    file = open(fileName, "r")
    result = [list(map(int, line.strip().split(","))) for line in file]
    file.close()
    return result

def parse_gaps(entries):
    result = [0]
    for entry in entries:
        if len(entry) > len(result):
            result.extend([0] * (len(entry) - len(result)))
        for i in range(len(entry)):
            if i+1 < len(result) and entry[i] > result[i+1]:
                result[i+1] = entry[i]
    for i in range(1, len(result)):
        result[i] = result[i-1] + result[i]
    result = pysdsl.IntVector(result)
    result.bit_compress()
    return result

def parse_borders(entries):
    result = []
    for entry in entries:
        if len(entry) > len(result):
            result.extend([0] * (len(entry) - len(result)))
        for i in range(len(entry)):
            result[i] += 1
    for i in range(1, len(result)):
        result[i] = result[i-1] + result[i]
    result = [0] + result
    result = pysdsl.IntVector(result)
    result.bit_compress()
    return result

def parse_array(filename, directed):
    file = open(filename, "r")
    result = []
    encoding = []
    count = 0
    for line in file:
        entries = list(map(int, line.strip().split(",")))
        if not directed:
            entries[1:] = sorted(entries[1:])
        while len(encoding) < len(entries):
            encoding.append(defaultdict(lambda: len(encoding[len(encoding)-1]) + 1))
        encoded_sublist = []
        for i, value in enumerate(entries):
            if value not in encoding[i]:
                encoding[i][value] = len(encoding[i])+1
            encoded_sublist.append(encoding[i][value])
        result.append(encoded_sublist)
        count += 1
    result.sort()
    gaps = parse_gaps(result)
    borders = parse_borders(result)
    for entry in result:
        for i in range(len(entry)):
            entry[i] = entry[i]+gaps[i]
    file.close()
    result = pysdsl.IntVector(list(itertools.chain.from_iterable(result)))
    result.bit_compress()
    for i in range(len(encoding)):
        encoding[i] = {v: k for k, v in encoding[i].items()}
    return result, encoding, count, gaps, borders
