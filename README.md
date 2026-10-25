# Tuple HyperCSA

## Usage

File format to parse:

    label, node1, node2, ...                       # jeweils Integer-Werte

Here, one edge per line as comma-seperated list.

Use `HyperCSA(file)` to construct the data structure.
You can then use the following query-algorithms:

    query_binary_search_bounded(query)
    query_select_forward_bounded(query)
    query_select_forward_unbounded(query)
    query_select_backward_bounded(query)
    query_select_backward_unbounded(query)

Here, `query` is a list of parameters for the search like the edges above.
In addition, `'*'` is allowed as a wildcard. 
The return is a generator of indices of result edges.
For each index, you can obtain the edge using the `decompress`-method.

The edges are just numbers, to get the string use `resolveName(hyperedgeMap, nodeMap, hyperedge)`.

See example.py for usages of all functions on the dataset in 0-Test

## References

You need pysdsl for this library: https://github.com/QratorLabs/pysdsl
